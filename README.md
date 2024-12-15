# Air Heater Control Application

This repository contains the code for an **Air Heater Control System**, implemented with **Streamlit** for real-time simulation and data visualisation. The application provides a user-friendly interface for managing, monitoring, and analysing the performance of an air heater system.

---

## Features

- **Simulation Control**: Start and stop the air heater simulation dynamically.
- **Real-Time Metrics**: Monitor temperature, filtered temperature, control signals, and setpoints in real-time.
- **Data Management**:
  - Export historical data to CSV.
  - Clear or clean up historical data.
- **Visualisations**:
  - Plot real-time temperature responses and control signals.
  - View recent data in a tabular format.
- **Customisable Setpoints**: Adjust setpoints and parameters dynamically.

---

## Getting Started

### Step 1: Clone the Repository
```bash
git clone https://github.com/choukha/airheater-control.git
cd airheater-control
```

### Step 2: Setting Up a Virtual Environment
#### 1. Create a Virtual Environment:
```bash
python -m venv .venv
```
#### 2. Activate the Virtual Environment:

On Windows:
```bash
.venv\\Scripts\\activate
```
On macOS/Linux:
```bash
source .venv/bin/activate
```
### Step 3: Install Dependencies
Install the required Python libraries using pip:
```bash
pip install -r requirements.txt
```

### Step 4: Running the Application
Start the Streamlit app with the following command:
```bash
streamlit run app.py
```

## Repository Structure
```bash
airheater-control/
├── app.py                   # Main application entry point
├── database_handler.py      # Handles database operations
├── simulator.py             # Air heater simulation logic
├── airheater_model.py       # Air heater system model
├── plotting.py              # Plotting utilities for visualisation
├── requirements.txt         # Python dependencies
├── README.md                # Documentation (this file)
├── database_schema.sql      # SQL schema for setting up the database
└── .venv/                   # Virtual environment (created locally)
```