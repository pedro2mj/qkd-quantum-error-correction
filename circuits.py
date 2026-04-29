from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.classical import expr
import numpy as np
from auxiliary import generate_hash_matrix
import matplotlib.pyplot as plt

def create_bell_pair(qc, i):
    qc.h(i)
    qc.cx(i, i + 1)
    
def long_distance_cnot(qc, control, target):

    if control == target:
        raise ValueError("Control and target qubits must be different.")

    if abs(control - target) == 1:
        qc.cx(control, target)

    elif control < target:
        qc.swap(control, control + 1)
        long_distance_cnot(qc, control + 1, target)
        qc.swap(control, control + 1) 
        
    else:
        qc.swap(control, control - 1)
        long_distance_cnot(qc, control - 1, target)
        qc.swap(control, control - 1)


def generate_bell_pairs(qc, n_pairs, start_index=0, flipped_qubit = None):
    
    if n_pairs < 1:
        raise ValueError("Number of pairs must be at least 1.")

    n_qubits = 2 * n_pairs

    for i in range(start_index, start_index+n_qubits, 2):
        create_bell_pair(qc, i)
        if flipped_qubit is not None:
            if (i-start_index) == flipped_qubit:
                qc.x(i)
            if (i+1-start_index) == flipped_qubit:
                qc.x(i+1)


def add_CNOT_syndrome_gates(qc, n_exchanged_pairs, n_pure_pairs, hash_matrix):

    for col in range(n_exchanged_pairs):
        for row in range(n_pure_pairs):
            if hash_matrix[row, col] == 1:
                qc.cx(col*2, n_exchanged_pairs*2 + row*2)
                qc.cx(col*2 + 1, n_exchanged_pairs*2 + row*2 + 1)

def add_measurement_gates(qc, cr, sr, n_exchanged_qubits, n_pure_pairs):
    
    for i in range(n_pure_pairs):

        qc.measure(n_exchanged_qubits + 2*i, cr[2*i])
        qc.measure(n_exchanged_qubits + 2*i + 1, cr[2*i + 1])
        
        qc.store(sr[i], expr.bit_xor(cr[2*i], cr[2*i + 1]))


def correct_errors(qc, sr, n_exchanged_pairs):
    for i in range(n_exchanged_pairs):
        with qc.if_test((sr, i+1)):
            qc.x(i*2)


def generate_qec_circuit(n_exchanged_pairs, flipped_qubit=None):
    if n_exchanged_pairs < 3:
        raise ValueError("Number of exchanged pairs must be at least 3.")

    n_pure_pairs = int(np.log2(n_exchanged_pairs))+1

    n_exchanged_qubits = 2 * n_exchanged_pairs 
    n_ancilla_qubits = n_pure_pairs*2 
    n_total_qubits = n_exchanged_qubits + n_ancilla_qubits

    n_aux_classical = n_ancilla_qubits
    syndrome_bits =  n_pure_pairs

    qr = QuantumRegister(n_total_qubits, name='q')
    cr = ClassicalRegister(n_aux_classical, name='c')
    sr = ClassicalRegister(syndrome_bits, name='s')

    qc = QuantumCircuit(qr, cr, sr)
    
    # Create pure bell pairs
    qc.barrier()
    generate_bell_pairs(qc, n_pure_pairs, start_index=n_exchanged_qubits)

    # Create bell pairs to simulate the exchange of qubits between Alice and Bob
    qc.barrier()
    generate_bell_pairs(qc, n_exchanged_pairs, start_index=0, flipped_qubit=flipped_qubit)
    
    qc.barrier()
    # Parity check for bit flip error correction
    H = generate_hash_matrix(n_exchanged_pairs)

    add_CNOT_syndrome_gates(qc, n_exchanged_pairs, n_pure_pairs, H)

    qc.barrier()

    add_measurement_gates(qc, cr, sr, n_exchanged_qubits, n_pure_pairs)

    qc.barrier()

    correct_errors(qc, sr, n_exchanged_pairs)

    qc.barrier()

    # Check parity of the ancilla qubits to detect bit flip errors
    # for i in range(n_pure_pairs):

    #     qc.measure(n_exchanged_qubits + 2*i, qc.clbits[2*i])
    #     parity = expr.lift(qc.clbits[2*i])

    #     qc.measure(n_exchanged_qubits + 2*i + 1, qc.clbits[2*i + 1])
    #     parity = expr.bit_xor(qc.clbits[2*i + 1], parity)
        
    #     with qc.if_test(parity):
    #         qc.x(2*i)

    #     qc.barrier()

    qc.measure_all()
    return qc   

if __name__ == "__main__":

    n_exchanged_pairs = 3
    flipped_qubit = None
    qc = generate_qec_circuit(n_exchanged_pairs, flipped_qubit)
    qc.draw(output='mpl', fold=-1)

    # from qiskit.quantum_info import SparsePauliOp

    # num_qubit_pairs = qc.num_qubits // 2
    # operator_strings = ['II'*i +  'ZZ' + 'II'*(num_qubit_pairs-i-1) for i in range(num_qubit_pairs)]
    # print(operator_strings)
    # print(len(operator_strings))

    # observables = [SparsePauliOp(operator_string) for operator_string in operator_strings]

    from qiskit_aer import AerSimulator

    sim = AerSimulator()

    job = sim.run(qc, shots=1000)
    result = job.result()

    counts = result.get_counts()
    print(counts)


    plt.show()