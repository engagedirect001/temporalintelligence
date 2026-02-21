import pytest
import math
from buggy_code import RunningStats


def test_mean_basic():
    rs = RunningStats()
    for x in [1, 2, 3, 4, 5]:
        rs.update(x)
    assert rs.get_mean() == pytest.approx(3.0)


def test_population_variance():
    """Bug 2: Wrong M2 accumulation gives wrong variance."""
    rs = RunningStats()
    data = [2, 4, 4, 4, 5, 5, 7, 9]
    for x in data:
        rs.update(x)
    expected_var = sum((x - 5.0)**2 for x in data) / len(data)
    assert rs.variance(ddof=0) == pytest.approx(expected_var, rel=1e-10), \
        f"Population variance: expected {expected_var}, got {rs.variance(ddof=0)}"


def test_sample_variance():
    """Bug 3: ddof not used in denominator."""
    rs = RunningStats()
    data = [2, 4, 4, 4, 5, 5, 7, 9]
    for x in data:
        rs.update(x)
    expected_sample_var = sum((x - 5.0)**2 for x in data) / (len(data) - 1)
    result = rs.variance(ddof=1)
    assert result == pytest.approx(expected_sample_var, rel=1e-10), \
        f"Sample variance: expected {expected_sample_var}, got {result}"


def test_single_value():
    rs = RunningStats()
    rs.update(42.0)
    assert rs.get_mean() == pytest.approx(42.0)
    assert rs.variance(ddof=0) == pytest.approx(0.0)
    assert math.isnan(rs.variance(ddof=1))


def test_stddev():
    rs = RunningStats()
    for x in [10, 12, 23, 23, 16, 23, 21, 16]:
        rs.update(x)
    expected_std = math.sqrt(sum((x - 18.0)**2 for x in [10,12,23,23,16,23,21,16]) / 8)
    assert rs.stddev(ddof=0) == pytest.approx(expected_std, rel=1e-9)


def test_min_max():
    rs = RunningStats()
    for x in [5, 3, 8, 1, 9]:
        rs.update(x)
    assert rs.min_val == 1
    assert rs.max_val == 9


def test_merge():
    rs1 = RunningStats()
    rs2 = RunningStats()
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    for x in data[:5]:
        rs1.update(x)
    for x in data[5:]:
        rs2.update(x)
    rs1.merge(rs2)
    
    assert rs1.n == 10
    assert rs1.get_mean() == pytest.approx(5.5)
    expected_var = sum((x - 5.5)**2 for x in data) / 10
    assert rs1.variance(ddof=0) == pytest.approx(expected_var, rel=1e-10)


def test_large_identical_values():
    """Variance of identical values should be 0."""
    rs = RunningStats()
    for _ in range(1000):
        rs.update(7.0)
    assert rs.variance(ddof=0) == pytest.approx(0.0, abs=1e-12)
