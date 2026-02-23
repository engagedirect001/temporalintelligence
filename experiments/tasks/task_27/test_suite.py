import pytest
import math
from buggy_code import KalmanFilter1D


def test_stationary_object():
    """Object at fixed position — filter should converge."""
    kf = KalmanFilter1D(initial_position=0.0, initial_velocity=0.0,
                         measurement_noise=1.0, process_noise=0.01)
    
    for _ in range(50):
        kf.predict(1.0)
        kf.update(10.0)
    
    assert kf.get_position() == pytest.approx(10.0, abs=0.5)
    assert kf.get_velocity() == pytest.approx(0.0, abs=0.5)


def test_constant_velocity():
    """Object moving at constant velocity."""
    kf = KalmanFilter1D(initial_position=0.0, initial_velocity=0.0,
                         measurement_noise=0.5, process_noise=0.01)
    
    # True position = 2*t
    for t in range(1, 30):
        true_pos = 2.0 * t
        kf.predict(1.0)
        kf.update(true_pos)
    
    assert kf.get_velocity() == pytest.approx(2.0, abs=0.5)


def test_uncertainty_decreases():
    """With repeated measurements, uncertainty should decrease."""
    kf = KalmanFilter1D(position_variance=100.0, measurement_noise=1.0,
                         process_noise=0.01)
    
    initial_uncertainty = kf.get_uncertainty()
    
    for _ in range(20):
        kf.predict(1.0)
        kf.update(5.0)
    
    assert kf.get_uncertainty() < initial_uncertainty * 0.5


def test_covariance_stays_symmetric():
    """Bug 3: covariance matrix should remain symmetric (P01 == P10)."""
    kf = KalmanFilter1D(position_variance=10.0, velocity_variance=1.0,
                         measurement_noise=1.0, process_noise=0.1)
    
    for _ in range(20):
        kf.predict(1.0)
        kf.update(5.0)
        assert kf.P[1] == pytest.approx(kf.P[2], abs=1e-10), \
            f"Covariance not symmetric: P01={kf.P[1]}, P10={kf.P[2]}"


def test_covariance_positive_definite():
    """Covariance diagonal elements should remain positive."""
    kf = KalmanFilter1D(measurement_noise=1.0, process_noise=0.1)
    
    for i in range(50):
        kf.predict(1.0)
        kf.update(float(i))
        assert kf.P[0] > 0, f"P[0,0] went non-positive at step {i}: {kf.P[0]}"
        assert kf.P[3] > 0, f"P[1,1] went non-positive at step {i}: {kf.P[3]}"


def test_process_noise_scaling():
    """Bug in predict: process noise for velocity should scale with dt."""
    kf1 = KalmanFilter1D(process_noise=1.0, velocity_variance=0.0)
    kf2 = KalmanFilter1D(process_noise=1.0, velocity_variance=0.0)
    
    kf1.predict(1.0)
    kf2.predict(2.0)
    
    # With dt=2, velocity process noise should be larger than dt=1
    assert kf2.P[3] > kf1.P[3], \
        f"Process noise should scale with dt: P11(dt=1)={kf1.P[3]}, P11(dt=2)={kf2.P[3]}"


def test_batch_filter():
    kf = KalmanFilter1D(measurement_noise=1.0, process_noise=0.1)
    measurements = [1.0, 2.1, 2.9, 4.1, 5.0]
    results = kf.batch_filter(measurements, dt=1.0)
    
    assert len(results) == 5
    # Final position should be close to 5
    assert results[-1][0] == pytest.approx(5.0, abs=1.5)


def test_velocity_covariance_update():
    """Bug 3: velocity covariance should be updated in update step."""
    kf = KalmanFilter1D(velocity_variance=10.0, measurement_noise=0.1,
                         process_noise=0.01)
    
    initial_vel_var = kf.P[3]
    
    for _ in range(30):
        kf.predict(1.0)
        kf.update(5.0)
    
    # Velocity variance should decrease with measurements
    assert kf.P[3] < initial_vel_var, \
        f"Velocity variance should decrease: initial={initial_vel_var}, final={kf.P[3]}"
