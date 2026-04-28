import numpy as np
from pyparsing import col

def generate_hash_matrix(n_exchanged_pairs):
    n_pure_pairs = int(np.log2(n_exchanged_pairs))+1
    
    # Create a hash matrix for the parity check
    hash_matrix = np.zeros((n_pure_pairs, n_exchanged_pairs), dtype=int)
    
    for col in range(n_exchanged_pairs):
        for row in range(n_pure_pairs):
            #Conver the col index + 1 to binary and fill the hash matrix
            if ((col+1) >> row) & 1:
                hash_matrix[row, col] = 1
    
    return hash_matrix