import pytest
from buggy_code import longest_increasing_subsequence

def is_strictly_increasing(seq):
    return all(seq[i] < seq[i+1] for i in range(len(seq)-1))

def is_subsequence(sub, arr):
    it = iter(arr)
    return all(c in it for c in sub)

def test_basic():
    result = longest_increasing_subsequence([10, 9, 2, 5, 3, 7, 101, 18])
    assert is_strictly_increasing(result)
    assert is_subsequence(result, [10, 9, 2, 5, 3, 7, 101, 18])
    assert len(result) == 4

def test_duplicate_values():
    """Bug 1 manifests: duplicates should NOT be in a strictly increasing subsequence."""
    result = longest_increasing_subsequence([1, 3, 3, 4])
    assert is_strictly_increasing(result), f"Result {result} is not strictly increasing"
    assert len(result) == 3  # [1, 3, 4]

def test_tie_breaking_path():
    """Bug 2+3 manifest: >= in dp update causes wrong parent tracking on ties."""
    result = longest_increasing_subsequence([2, 6, 3, 4, 5])
    assert is_strictly_increasing(result)
    assert is_subsequence(result, [2, 6, 3, 4, 5])
    assert len(result) == 4  # [2, 3, 4, 5]

def test_all_same():
    result = longest_increasing_subsequence([5, 5, 5, 5])
    assert len(result) == 1
    assert is_strictly_increasing(result) or len(result) == 1

def test_already_sorted():
    result = longest_increasing_subsequence([1, 2, 3, 4, 5])
    assert result == [1, 2, 3, 4, 5]

def test_decreasing():
    result = longest_increasing_subsequence([5, 4, 3, 2, 1])
    assert len(result) == 1

def test_single():
    result = longest_increasing_subsequence([42])
    assert result == [42]

def test_empty():
    result = longest_increasing_subsequence([])
    assert result == []

def test_complex_path_recovery():
    """Multiple LIS paths exist — result must be a valid one."""
    arr = [1, 5, 2, 3, 4, 6]
    result = longest_increasing_subsequence(arr)
    assert is_strictly_increasing(result)
    assert is_subsequence(result, arr)
    assert len(result) == 5  # [1, 2, 3, 4, 6]
