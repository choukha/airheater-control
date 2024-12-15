# config.py

# Database settings
DB_PATH = "airheater.db"

# Default controller settings
DEFAULT_SETTINGS = {
    'Kp': 2.0,
    'Ti': 7.5,
    'Setpoint': 25.0,
    'FilterTf': 0.5,
    'DisplayWindow': 10
}

# Air heater model parameters
AIRHEATER_PARAMS = {
    'Kh': 3.5,
    'theta_t': 22.0,
    'theta_d': 2.0,
    'Tenv': 21.5,
    'noise_std': 0.05
}

# Sampling and timing settings
DEFAULT_SAMPLING_TIME = 0.1  # seconds

# Data management settings
DATA_RETENTION_DAYS = 30
MAX_DISPLAY_POINTS = 500