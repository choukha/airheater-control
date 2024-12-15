import nidaqmx
from nidaqmx.constants import TerminalConfiguration
from typing import Optional, Tuple
import logging

class ProcessManager:
    def __init__(self):
        self.mode = "simulator"  # Default to simulator mode
        self.task_ai = None
        self.task_ao = None
        
    def setup_hardware(self) -> bool:
        """Setup DAQ hardware connections"""
        try:
            # Setup analog input (temperature reading)
            self.task_ai = nidaqmx.Task()
            self.task_ai.ai_channels.add_ai_voltage_chan(
                "Dev1/ai0",
                terminal_config=TerminalConfiguration.RSE,
                min_val=1.0,
                max_val=5.0
            )
            self.task_ai.start()
            
            # Setup analog output (control signal)
            self.task_ao = nidaqmx.Task()
            self.task_ao.ao_channels.add_ao_voltage_chan(
                'Dev1/ao0',
                min_val=0.0,
                max_val=5.0
            )
            self.task_ao.start()
            
            logging.info("Hardware setup successful")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up hardware: {e}")
            self.cleanup_hardware()
            return False
            
    def cleanup_hardware(self):
        """Cleanup DAQ tasks"""
        if self.task_ai:
            try:
                self.task_ai.stop()
                self.task_ai.close()
            except:
                pass
            finally:
                self.task_ai = None
                
        if self.task_ao:
            try:
                self.task_ao.write(0)  # Safety: set output to 0
                self.task_ao.stop()
                self.task_ao.close()
            except:
                pass
            finally:
                self.task_ao = None
                
    def switch_mode(self, new_mode: str) -> bool:
        """Switch between simulator and hardware modes"""
        if new_mode not in ["simulator", "hardware"]:
            return False
            
        if new_mode == self.mode:
            return True
            
        if new_mode == "hardware":
            if self.setup_hardware():
                self.mode = "hardware"
                return True
            return False
        else:
            self.cleanup_hardware()
            self.mode = "simulator"
            return True
            
    def read_temperature(self) -> Optional[float]:
        """Read temperature from hardware or return None"""
        if self.mode != "hardware" or not self.task_ai:
            return None
            
        try:
            voltage = self.task_ai.read()
            temperature = self.voltage_to_temperature(voltage)
            return temperature
        except Exception as e:
            logging.error(f"Error reading temperature: {e}")
            return None
            
    def write_control_signal(self, value: float) -> bool:
        """Write control signal to hardware"""
        if self.mode != "hardware" or not self.task_ao:
            return False
            
        try:
            # Ensure value is within bounds
            value = max(0.0, min(5.0, value))
            self.task_ao.write(value)
            return True
        except Exception as e:
            logging.error(f"Error writing control signal: {e}")
            return False
            
    @staticmethod
    def voltage_to_temperature(voltage: float) -> float:
        """Convert voltage (1-5V) to temperature (0-50°C)"""
        return (voltage - 1.0) * (50.0 / 4.0)
        
    @staticmethod
    def temperature_to_voltage(temperature: float) -> float:
        """Convert temperature (0-50°C) to voltage (1-5V)"""
        return (temperature * (4.0 / 50.0)) + 1.0
        
    def get_status(self) -> dict:
        """Get current status of process manager"""
        return {
            "mode": self.mode,
            "hardware_connected": bool(self.task_ai and self.task_ao),
            "ai_task_valid": bool(self.task_ai),
            "ao_task_valid": bool(self.task_ao)
        }