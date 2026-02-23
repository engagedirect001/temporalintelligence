"""
Task 13: Matrix Operations with Numerical Stability
Category: Math/Numerical bugs
"""
import math


def matrix_multiply(A, B):
    """Multiply two matrices."""
    rows_a, cols_a = len(A), len(A[0])
    rows_b, cols_b = len(B), len(B[0])
    
    if cols_a != rows_b:
        raise ValueError("Incompatible matrix dimensions")
    
    result = [[0.0] * cols_b for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += A[i][k] * B[k][j]
    return result


def matrix_inverse_2x2(M):
    """Compute inverse of 2x2 matrix."""
    a, b = M[0][0], M[0][1]
    c, d = M[1][0], M[1][1]
    
    det = a * d - b * c
    if abs(det) < 1e-15:
        raise ValueError("Matrix is singular")
    
    # Bug 1: sign error — should be [[d, -b], [-c, a]] / det
    return [
        [d / det, -b / det],
        [c / det, a / det]   # Bug: c should be -c
    ]


def solve_linear_system(A, b):
    """Solve Ax = b using Gaussian elimination with partial pivoting.
    A is n×n, b is length n. Returns x."""
    n = len(A)
    # Augmented matrix
    aug = [row[:] + [b[i]] for i, row in enumerate(A)]
    
    for col in range(n):
        # Partial pivoting
        max_row = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > abs(aug[max_row][col]):
                max_row = row
        aug[col], aug[max_row] = aug[max_row], aug[col]
        
        if abs(aug[col][col]) < 1e-15:
            raise ValueError("Matrix is singular")
        
        # Eliminate below
        for row in range(col + 1, n):
            # Bug 2: factor calculation doesn't use pivoted row
            factor = aug[row][col] / aug[col][col]
            for j in range(col, n + 1):
                aug[row][j] -= factor * aug[col][j]
    
    # Back substitution
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = aug[i][n]
        for j in range(i + 1, n):
            x[i] -= aug[i][j] * x[j]
        # Bug 3: divides by wrong diagonal element after pivoting
        # (This is actually correct IF pivoting was done right, but
        # there's a subtle issue: the augmented matrix cols shift)
        x[i] /= aug[i][i]
    
    return x


def condition_number(A):
    """Estimate condition number of 2x2 matrix using 1-norm."""
    if len(A) != 2 or len(A[0]) != 2:
        raise ValueError("Only 2x2 supported")
    
    # 1-norm: max column sum of absolute values
    norm_A = max(
        abs(A[0][0]) + abs(A[1][0]),
        abs(A[0][1]) + abs(A[1][1])
    )
    
    A_inv = matrix_inverse_2x2(A)
    norm_A_inv = max(
        abs(A_inv[0][0]) + abs(A_inv[1][0]),
        abs(A_inv[0][1]) + abs(A_inv[1][1])
    )
    
    return norm_A * norm_A_inv
