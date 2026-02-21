import pytest
from buggy_code import merge_intervals, find_interval, weighted_coverage


def test_no_overlap():
    result = merge_intervals([(1, 3, 1), (5, 7, 1)])
    assert result == [(1, 3, 1), (5, 7, 1)]


def test_adjacent_merge():
    """Bug 2: adjacent intervals (3,5) and (5,8) should merge."""
    result = merge_intervals([(1, 5, 1), (5, 8, 2)])
    assert len(result) == 1, f"Adjacent intervals should merge, got {result}"
    assert result[0] == (1, 8, 3)


def test_overlapping_merge():
    result = merge_intervals([(1, 5, 1), (3, 7, 2)])
    assert len(result) == 1
    assert result[0] == (1, 7, 3)


def test_containment():
    """When one interval contains another."""
    result = merge_intervals([(1, 10, 1), (3, 5, 2)])
    assert len(result) == 1
    assert result[0] == (1, 10, 3)


def test_find_interval_at_end():
    """Bug 3: point at exact end of interval should be found."""
    merged = [(1, 5, 1), (7, 10, 2)]
    result = find_interval(merged, 5)
    assert result is not None, "Point at end of interval should be found"
    assert result == (1, 5, 1)


def test_find_interval_at_start():
    merged = [(1, 5, 1), (7, 10, 2)]
    result = find_interval(merged, 1)
    assert result == (1, 5, 1)


def test_find_interval_not_found():
    merged = [(1, 5, 1), (7, 10, 2)]
    result = find_interval(merged, 6)
    assert result is None


def test_weighted_coverage():
    ivs = [(1, 3, 1), (2, 5, 1)]
    result = weighted_coverage(ivs)
    # merged: (1, 5, 2), coverage = (5-1)*2 = 8
    assert result == 8


def test_empty():
    assert merge_intervals([]) == []
    assert find_interval([], 5) is None
