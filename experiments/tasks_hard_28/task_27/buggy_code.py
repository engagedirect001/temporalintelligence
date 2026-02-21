"""
Task 27: Kalman Filter for 1D Position Tracking
Category: Hardest — numerical + algorithm + state estimation
"""
import math


class KalmanFilter1D:
    """1D Kalman filter for position tracking with constant velocity model.
    
    State: [position, velocity]
    Measurement: position only
    """
    
    def __init__(self, initial_position=0.0, initial_velocity=0.0,
                 position_variance=1.0, velocity_variance=1.0,
                 process_noise=0.1, measurement_noise=1.0):
        # State vector [position, velocity]
        self.x = [initial_position, initial_velocity]
        
        # Covariance matrix (2x2, stored as flat list [p00, p01, p10, p11])
        self.P = [position_variance, 0.0, 0.0, velocity_variance]
        
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.history = []
    
    def predict(self, dt):
        """Predict step: project state forward by dt seconds."""
        # State transition: x' = F * x
        # F = [[1, dt], [0, 1]]
        new_pos = self.x[0] + self.x[1] * dt
        new_vel = self.x[1]
        self.x = [new_pos, new_vel]
        
        # Covariance prediction: P' = F * P * F^T + Q
        # Bug 1: incorrect covariance prediction matrix multiplication
        # F*P*F^T for F=[[1,dt],[0,1]] gives:
        # [[P00 + dt*P10 + dt*(P01 + dt*P11), P01 + dt*P11],
        #  [P10 + dt*P11, P11]]
        p00, p01, p10, p11 = self.P
        
        # Wrong: doesn't include cross terms properly
        new_p00 = p00 + dt * p01 + dt * p10 + dt * dt * p11 + self.process_noise * dt
        new_p01 = p01 + dt * p11
        new_p10 = p10 + dt * p11
        new_p11 = p11 + self.process_noise  # Bug: process noise should scale with dt
        
        self.P = [new_p00, new_p01, new_p10, new_p11]
    
    def update(self, measurement):
        """Update step: incorporate measurement."""
        # Measurement matrix H = [1, 0]
        # Innovation: y = z - H * x
        innovation = measurement - self.x[0]
        
        # Innovation covariance: S = H * P * H^T + R
        S = self.P[0] + self.measurement_noise
        
        if abs(S) < 1e-15:
            return  # avoid division by zero
        
        # Kalman gain: K = P * H^T / S
        K0 = self.P[0] / S
        K1 = self.P[2] / S  # P[2] = p10
        
        # State update
        self.x[0] += K0 * innovation
        self.x[1] += K1 * innovation
        
        # Covariance update: P = (I - K*H) * P
        # Bug 2: Joseph form should be used for numerical stability,
        # but the real bug is the update formula is wrong
        # (I - K*H) = [[1-K0, 0], [-K1, 1]] for H=[1,0]
        p00, p01, p10, p11 = self.P
        
        # Bug 3: wrong covariance update — doesn't update all elements
        self.P[0] = (1 - K0) * p00
        self.P[1] = (1 - K0) * p01
        # Missing: P[2] and P[3] should also be updated
        # self.P[2] = p10 - K1 * p00  (missing!)
        # self.P[3] = p11 - K1 * p01  (missing!)
        
        self.history.append({
            "measurement": measurement,
            "estimate": self.x[0],
            "velocity": self.x[1],
            "uncertainty": self.P[0],
        })
    
    def get_position(self):
        return self.x[0]
    
    def get_velocity(self):
        return self.x[1]
    
    def get_uncertainty(self):
        return math.sqrt(self.P[0])
    
    def batch_filter(self, measurements, dt=1.0):
        """Run filter on a sequence of measurements."""
        results = []
        for z in measurements:
            self.predict(dt)
            self.update(z)
            results.append((self.x[0], self.x[1], math.sqrt(abs(self.P[0]))))
        return results
