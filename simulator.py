from typing import Tuple, Optional
from airheater_model import AirHeater, PIController, LowpassFilter
from database_handler import DatabaseHandler

class AirHeaterSimulator:
    def __init__(self, db_handler: Optional[DatabaseHandler] = None):
        """Initialize simulator components"""
        # Initialize model components
        self.heater = AirHeater(
            Kh=3.5,              # Process gain
            theta_t=22.0,        # Time constant
            Ts=0.1,              # Sampling time
            Tenv=21.5,           # Environmental temperature
            noise_std=0.05       # Noise level
        )
        
        self.controller = PIController(
            Kp=2.0,              # Default Kp
            Ti=7.5,              # Default Ti
            Ts=0.1               # Sampling time
        )
        
        self.filter = LowpassFilter(
            Tf=0.5,              # Filter time constant
            Ts=0.1,              # Sampling time
            y_init=21.5          # Initial value
        )
        
        # Runtime parameters
        self._running = False
        self.setpoint = 25.0     # Default setpoint
        
        # Database handler
        self.db = db_handler or DatabaseHandler()
        
        # Load latest settings if available
        self._load_latest_settings()
        
    def _load_latest_settings(self):
        """Load latest settings from database"""
        latest = self.db.get_latest_values()
        if not latest.empty:
            self.setpoint = float(latest['setpoint'].iloc[0])
            self.controller.Kp = float(latest['kp'].iloc[0])
            self.controller.Ti = float(latest['ti'].iloc[0])
        
    def start(self):
        """Start simulation"""
        self._running = True
        
    def stop(self):
        """Stop simulation"""
        self._running = False
        
    def is_running(self) -> bool:
        """Check if simulation is running"""
        return self._running
        
    def update_parameters(self, setpoint: float, kp: float, ti: float, 
                         noise_std: float, filter_tf: float):
        """Update simulation parameters"""
        self.setpoint = setpoint
        self.controller.Kp = kp
        self.controller.Ti = ti
        self.heater.noise_std = noise_std
        self.filter.Tf = filter_tf
        
    def simulate_step(self):
        """Run one simulation step
        
        Returns:
            Tuple containing (temperature, filtered_temperature, control_signal)
        """
        if not self.is_running:
            return None, None, None
        
        try:
            # Get current temperature
            current_temp = self.heater.Tout
            
            # Calculate control signal
            control_signal = self.controller.update(self.setpoint, current_temp)
            
            # Update process
            temperature = self.heater.update(control_signal)
            
            # Filter measurement
            filtered_temp = self.filter.update(temperature)
            
            # Store in database
            self.db.store_measurement(
                temperature=temperature,
                filtered_temp=filtered_temp,
                control_signal=control_signal,
                setpoint=self.setpoint,
                kp=self.controller.Kp,
                ti=self.controller.Ti
            )
            
            return temperature, filtered_temp, control_signal
        except Exception as e:
            print(f"Simulation error: {e}")
            self.is_running = False
            return None, None, None