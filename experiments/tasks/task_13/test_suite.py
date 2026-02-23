import pytest
import math
from buggy_code import matrix_multiply, matrix_inverse_2x2, solve_linear_system, condition_number


def approx_matrix(M, expected, rel=1e-6):
    for i in range(len(M)):
        for j in range(len(M[0])):
            assert M[i][j] == pytest.approx(expected[i][j], rel=rel), \
                f"M[{i}][{j}] = {M[i][j]}, expected {expected[i][j]}"


def test_matrix_multiply():
    A = [[1, 2], [3, 4]]
    B = [[5, 6], [7, 8]]
    result = matrix_multiply(A, B)
    approx_matrix(result, [[19, 22], [43, 50]])


def test_inverse_2x2():
    """Bug 1: sign error in inverse."""
    M = [[4, 7], [2, 6]]
    inv = matrix_inverse_2x2(M)
    # M * M^-1 should be identity
    product = matrix_multiply(M, inv)
    approx_matrix(product, [[1, 0], [0, 1]], rel=1e-10)


def test_inverse_2x2_another():
    M = [[1, 2], [3, 4]]
    inv = matrix_inverse_2x2(M)
    product = matrix_multiply(M, inv)
    approx_matrix(product, [[1, 0], [0, 1]], rel=1e-10)


def test_solve_2x2():
    # 2x + 3y = 8, x + y = 3 => x=1, y=2
    A = [[2, 3], [1, 1]]
    b = [8, 3]
    x = solve_linear_system(A, b)
    assert x[0] == pytest.approx(1.0, rel=1e-10)
    assert x[1] == pytest.approx(2.0, rel=1e-10)


def test_solve_3x3():
    A = [[2, 1, -1], [-3, -1, 2], [-2, 1, 2]]
    b = [8, -11, -3]
    x = solve_linear_system(A, b)
    assert x[0] == pytest.approx(2.0, rel=1e-10)
    assert x[1] == pytest.approx(3.0, rel=1e-10)
    assert x[2] == pytest.approx(-1.0, rel=1e-10)


def test_solve_needs_pivoting():
    """System where first pivot is zero — needs row swap."""
    A = [[0, 1, 1], [1, 0, 1], [1, 1, 0]]
    b = [2, 2, 2]
    x = solve_linear_system(A, b)
    for xi in x:
        assert xi == pytest.approx(1.0, rel=1e-10)


def test_condition_number_identity():
    """Condition number of identity is 1."""
    I = [[1, 0], [0, 1]]
    cond = condition_number(I)
    assert cond == pytest.approx(1.0, rel=1e-10)


def test_condition_number_ill_conditioned():
    """Bug 1 cascades: wrong inverse => wrong condition number."""
    M = [[1, 1], [1, 1.0001]]
    cond = condition_number(M)
    # Should be very large (ill-conditioned)
    assert cond > 10000


def test_singular_matrix():
    with pytest.raises(ValueError):
        matrix_inverse_2x2([[1, 2], [2, 4]])
