-- Schema for air heater monitoring database
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature REAL,
    temperature_filtered REAL,
    setpoint REAL,
    control_signal REAL,
    kp REAL,
    ti REAL
);

-- Index for faster time-based queries
CREATE INDEX IF NOT EXISTS idx_timestamp ON measurements(timestamp);