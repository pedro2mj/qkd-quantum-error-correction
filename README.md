# bit-error-correction

Implementation in Qiskit of a quantum error correction code via entanglement distillation on a QKD BBM92 protocol as seen on https://arxiv.org/abs/1810.03267 (Apendix A)

It is desinged to detect a single bit flip with the hash matrix in which each column corresponds to the qubit number in binary.

Eg. for a 7 qubit key the hashing matrix is:

$  H =  \begin{pmatrix}
0 & 0 & 0 & 1 & 1 & 1 & 1 \\
0 & 1 & 1 & 0 & 0 & 1 & 1 \\
1 & 0 & 1 & 0 & 1 & 0 & 1 
\end{pmatrix}
$

 
  
