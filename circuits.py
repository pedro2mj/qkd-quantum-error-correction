from qiskit import QuantumCircuit
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
                qc.z(i)
            if (i+1-start_index) == flipped_qubit:
                qc.z(i+1)


def add_CNOT_syndrom_gates(qc, n_exchanged_pairs, n_pure_pairs, hash_matrix):

    for col in range(n_exchanged_pairs):
        for row in range(n_pure_pairs):
            if hash_matrix[row, col] == 1:
                qc.cx(col*2, n_exchanged_pairs*2 + row*2)
                qc.cx(col*2 + 1, n_exchanged_pairs*2 + row*2 + 1)


def generate_qec_circuit(n_exchanged_pairs, flipped_qubit=None):
    if n_exchanged_pairs < 3:
        raise ValueError("Number of exchanged pairs must be at least 3.")

    n_pure_pairs = int(np.log2(n_exchanged_pairs))+1

    n_exchanged_qubits = 2 * n_exchanged_pairs 
    n_ancilla_qubits = n_pure_pairs*2 
    n_total_qubits = n_exchanged_qubits + n_ancilla_qubits

    n_classical_bits = n_pure_pairs

    qc = QuantumCircuit(n_total_qubits, n_classical_bits)
    
    # Create pure bell pairs
    qc.barrier()
    generate_bell_pairs(qc, n_pure_pairs, start_index=n_exchanged_qubits)

    # Create bell pairs to simulate the exchange of qubits between Alice and Bob
    qc.barrier()
    generate_bell_pairs(qc, n_exchanged_pairs, start_index=0, flipped_qubit=flipped_qubit)
    
    qc.barrier()
    # Parity check for bit flip error correction
    H = generate_hash_matrix(n_exchanged_pairs)

    add_CNOT_syndrom_gates(qc, n_exchanged_pairs, n_pure_pairs, H)

    qc.barrier()

    # parity = []
    # # Check parity of the ancilla qubits to detect bit flip errors
    # for i in range(n_pure_pairs):

    #     qc.measure(2 + i*4, qc.clbits[i])
    #     parity_qubit = expr.lift(qc.clbits[i])

    #     qc.measure(2 + i*4 + 1, qc.clbits[i])
    #     parity_qubit = expr.bit_xor(qc.clbits[i], parity_qubit)
        
    #     parity.append(parity_qubit)

    
    # for i in range(n_pure_pairs):
    #     with qc.if_test(parity[i]) and qc.if_test(parity[i+1]):
    #          qc.z((i+1)*4+1)

    
    # with qc.if_test(parity[-1]) and not qc.if_test(parity[-2]):
    #     qc.z(-1)

    return qc   

if __name__ == "__main__":

    n_exchanged_pairs = 4
    flipped_qubit = None
    qc = generate_qec_circuit(n_exchanged_pairs, flipped_qubit)
    qc.draw(output='mpl')
    plt.show()