import numpy as np

class AirHeater:
    def __init__(self, Kh=3.5, theta_t=22.0, Ts=0.1, Tenv=21.5, 
                 noise_std=0.05, delay_steps=2):
        """Initialize air heater model with given parameters"""
        self.Kh = Kh          # Process gain
        self.theta_t = theta_t # Time constant
        self.Ts = Ts          # Sampling time
        self.Tenv = Tenv      # Environmental temperature
        self.noise_std = noise_std  # Noise standard deviation
        self.delay_steps = delay_steps
        
        # Initialize states
        self.Tout = Tenv      # Current output temperature
        self.u_buffer = [0.0] * delay_steps  # Initialize delay buffer
        
    def update(self, u):
        """Update model state and return output temperature"""
        # Input saturation
        u = max(0.0, min(5.0, u))
        
        # Update buffer for time delay
        self.u_buffer.append(u)
        u_delayed = self.u_buffer.pop(0)
        
        # Discrete air heater model implementation
        self.Tout = (self.Tout + 
                    (self.Ts/self.theta_t) * 
                    (-self.Tout + self.Kh*u_delayed + self.Tenv))
        
        # Add measurement noise
        output = self.Tout + np.random.normal(0, self.noise_std)
        
        return output

class PIController:
    def __init__(self, Kp=2.0, Ti=7.5, Ts=0.1):
        """Initialize PI controller"""
        self.Kp = Kp        # Proportional gain
        self.Ti = Ti        # Integral time
        self.Ts = Ts        # Sampling time
        
        # Initialize states
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_output = 0.0
        
    def update(self, setpoint, measurement):
        """Update controller and return control signal"""
        # Calculate error
        error = setpoint - measurement
        
        # Update integral term
        self.integral += self.Ts * error
        
        # Anti-windup
        self.integral = max(-5.0/self.Kp, min(5.0/self.Kp, self.integral))
        
        # Calculate control signal
        u = (self.Kp * error + 
             (self.Kp/self.Ti) * self.integral)
        
        # Saturation
        u = max(0.0, min(5.0, u))
        
        # Store previous values
        self.prev_error = error
        self.prev_output = u
        
        return u

class LowpassFilter:
    def __init__(self, Tf=0.5, Ts=0.1, y_init=21.5):
        """Initialize lowpass filter"""
        self.Tf = Tf        # Filter time constant
        self.Ts = Ts        # Sampling time
        self.y = y_init     # Initial output
        
        # Calculate filter coefficient
        self.alpha = self.Ts/(self.Tf + self.Ts)
        
    def update(self, u):
        """Update filter state and return filtered output"""
        self.y = (1 - self.alpha)*self.y + self.alpha*u
        return self.y