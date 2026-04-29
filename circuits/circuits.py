from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.classical import expr
import numpy as np
from .auxiliary import generate_hash_matrix
import matplotlib.pyplot as plt

def create_bell_pair(qc, i):
    """Creates a Bell pair between qubits i and i+1.
    Args:
        qc (QuantumCircuit): The quantum circuit to which the gates will be added.
        i (int): The index of the first qubit in the pair. The second qubit will be i+1.
        
    Raises:
        ValueError: If i+1 exceeds the number of qubits in the circuit.
    """
    qc.h(i)
    qc.cx(i, i + 1)
    
def long_distance_cnot(qc, control, target):
    """Implements a long-distance CNOT gate between control and target qubits using SWAP gates.
    Args:
        qc (QuantumCircuit): The quantum circuit to which the gates will be added.
        control (int): The index of the control qubit.
        target (int): The index of the target qubit.

    Raises:
        ValueError: If the control and target qubits are the same.
    """

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
    """
    Generates n_pairs of Bell pairs starting from the specified index in the quantum circuit.
    Optionally, one of the qubits in the pairs can be flipped to simulate an error. 
    
    Args:
        qc (QuantumCircuit): The quantum circuit to which the gates will be added.
        n_pairs (int): The number of Bell pairs to generate.
        start_index (int): The index of the first qubit in the first pair.
        flipped_qubit (int, optional): The index of the qubit to flip.

    Raises:
        ValueError: If n_pairs is less than 1.
    """
    
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

    """
    Adds CNOT gates to the quantum circuit for syndrome measurement based on the provided hash matrix.
    
    Args:
        qc (QuantumCircuit): The quantum circuit to which the gates will be added.
        n_exchanged_pairs (int): The number of exchanged pairs of qubits.
        n_pure_pairs (int): The number of pure pairs of qubits used for syndrome measurement.
        hash_matrix (numpy.ndarray): A binary matrix that defines the connections between the exchanged qubits and the pure qubits for syndrome measurement.
        
    Raises:
        ValueError: If the dimensions of the hash matrix do not match the number of exchanged pairs and pure pairs.
    """
    if hash_matrix.shape != (n_pure_pairs, n_exchanged_pairs):
        raise ValueError("Hash matrix dimensions do not match the number of exchanged pairs and pure pairs.")
    
    for col in range(n_exchanged_pairs):
        for row in range(n_pure_pairs):
            if hash_matrix[row, col] == 1:
                qc.cx(col*2, n_exchanged_pairs*2 + row*2)
                qc.cx(col*2 + 1, n_exchanged_pairs*2 + row*2 + 1)

def add_measurement_gates(qc, cr, sr, n_exchanged_qubits):
    """
    Adds measurement gates to the quantum circuit for syndrome measurement and stores the results in classical registers.
    
    Args:
        qc (QuantumCircuit): The quantum circuit to which the gates will be added.
        cr (ClassicalRegister): The classical register where the measurement results of the ancilla qubits will be stored.
        sr (ClassicalRegister): The classical register where the syndrome bits will be stored. 
        n_exchanged_qubits (int): The number of qubits that were exchanged between Alice and Bob.
    
    Raises:
        ValueError: If the number of pairs is less than 1
    """
    if n_exchanged_pairs < 1:
        raise ValueError("Number of exchanged pairs must be at least 1.")
    
    n_pure_pairs = int(np.log2(n_exchanged_pairs))+1


    for i in range(n_pure_pairs):

        qc.measure(n_exchanged_qubits + 2*i, cr[2*i])
        qc.measure(n_exchanged_qubits + 2*i + 1, cr[2*i + 1])
        
        qc.store(sr[i], expr.bit_xor(cr[2*i], cr[2*i + 1]))


def correct_errors(qc, sr, n_exchanged_pairs):
    """
    2 Adds gates to the quantum circuit to correct bit flip errors based on the syndrome bits stored in the classical register.
    
    Args:
        qc (QuantumCircuit): The quantum circuit to which the gates will be added.
        sr (ClassicalRegister): The classical register where the syndrome bits are stored.
        n_exchanged_pairs (int): The number of exchanged pairs of qubits.
    
    Raises:
        ValueError: If the number of exchanged pairs is less than 1.
    """
    if n_exchanged_pairs < 1:
        raise ValueError("Number of exchanged pairs must be at least 1.")

    for i in range(n_exchanged_pairs):
        with qc.if_test((sr, i+1)):
            qc.x(i*2)


def generate_qec_circuit(n_exchanged_pairs, flipped_qubit=None):
    """
    Generates a quantum error correction circuit for bit flip errors based on the number of exchanged pairs of qubits and an optional flipped qubit to simulate an error.
    Args:
        n_exchanged_pairs (int): The number of exchanged pairs of qubits between Alice and Bob.
        flipped_qubit (int, optional): The index of the qubit to flip to simulate an error. The index is based on the order of the exchanged qubits (0 to 2*n_exchanged_pairs-1). If None, no qubits will be flipped.
    Raises:
        ValueError: If the number of exchanged pairs is less than 3.
        ValueError: If the flipped qubit index is out of range.

    Returns:
        QuantumCircuit: The generated quantum error correction circuit.    
    """
    if n_exchanged_pairs < 3:
        raise ValueError("Number of exchanged pairs must be at least 3.")
    if flipped_qubit is not None and (flipped_qubit < 0 or flipped_qubit >= 2*n_exchanged_pairs):
        raise ValueError("Flipped qubit index is out of range.")
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

    qc.measure_all()
    return qc   

if __name__ == "__main__":

    n_exchanged_pairs = 3
    flipped_qubit = None
    qc = generate_qec_circuit(n_exchanged_pairs, flipped_qubit)
    qc.draw(output='mpl', fold=-1)

    from qiskit_aer import AerSimulator

    sim = AerSimulator()

    job = sim.run(qc, shots=1000)
    result = job.result()

    counts = result.get_counts()
    print(counts)


    plt.show()