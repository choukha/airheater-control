import streamlit as st
import time
from datetime import datetime, timedelta
from simulator import AirHeaterSimulator
from stability_analysis import StabilityAnalyzer
from plotting import create_process_plots
from database_handler import DatabaseHandler

# Page config
st.set_page_config(layout="wide")

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.db = DatabaseHandler()
    st.session_state.simulator = AirHeaterSimulator(st.session_state.db)
    st.session_state.analyzer = StabilityAnalyzer()
    st.session_state.last_data_clear = None
    st.session_state.data_version = 0  # Track data changes
    st.session_state.last_refresh = time.time()
    st.session_state.initialized = True

# Function to check if data needs refresh
def needs_refresh():
    current_time = time.time()
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = current_time
        return True
    
    # Refresh every 5 seconds or if data_version changed
    if (current_time - st.session_state.last_refresh) > 5:
        st.session_state.last_refresh = current_time
        return True
    return False

if "is_running" not in st.session_state:
    st.session_state.is_running = False


# App title
st.title("Air Heater Control and Monitoring System")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Control", "Stability Analysis", "Data Management"])


# Sidebar: Control buttons
st.sidebar.header("Click Twice to Start/Stop")

if st.session_state.simulator.is_running():
    # Stop button with red emoji icon
    if st.sidebar.button("🛑 STOP", key="stop_button"):
        st.session_state.simulator.stop()
        st.session_state.is_running = False
else:
    # Start button with green emoji icon
    if st.sidebar.button("✅ START", key="start_button"):
        st.session_state.simulator.start()
        st.session_state.is_running = True


# Sidebar controls
st.sidebar.header("Controller Settings")
# Get latest values for initial slider positions
latest = st.session_state.db.get_latest_values()
if not latest.empty:
    default_setpoint = float(latest['setpoint'].iloc[0])
    default_kp = float(latest['kp'].iloc[0])
    default_ti = float(latest['ti'].iloc[0])
else:
    default_setpoint = 25.0
    default_kp = 2.0
    default_ti = 7.5

setpoint = st.sidebar.slider("Temperature Setpoint (°C)", 20.0, 50.0, default_setpoint, 0.5)
kp = st.sidebar.slider("Proportional Gain (Kp)", 0.1, 5.0, default_kp, 0.1)
ti = st.sidebar.slider("Integral Time (Ti)", 0.1, 20.0, default_ti, 0.1)

st.sidebar.header("Process Settings")
noise_std = st.sidebar.slider("Noise Level (std)", 0.0, 1.0, 0.05, 0.01)
filter_tf = st.sidebar.slider("Filter Time Constant (Tf)", 0.1, 2.0, 0.5, 0.1)

# Display window options
st.sidebar.header("Display Settings")
display_minutes = st.sidebar.slider("Display window (minutes)", 1, 60, 10, 1)

# Update simulator parameters
st.session_state.simulator.update_parameters(setpoint, kp, ti, noise_std, filter_tf)




# Ensure necessary data is initialized in session state
if "stats" not in st.session_state:
    st.session_state.stats = None
if "recent_data" not in st.session_state:
    st.session_state.recent_data = None

# Fragment for Tab1: Simulation Control

@st.fragment(run_every=0.01)  # High-frequency simulation updates
def simulation_update_fragment():
    if st.session_state.simulator.is_running():
        # Run the simulation step
        temp, filtered_temp, control = st.session_state.simulator.simulate_step()

        # Update session state with the latest simulation results
        st.session_state.temperature = temp
        st.session_state.filtered_temperature = filtered_temp
        st.session_state.control_signal = control



@st.fragment(run_every=10)  # Periodic plot and metric updates
def plot_and_metrics_fragment():
    st.header("Air Heater Control")
    if st.session_state.is_running:
        

        # Create metrics placeholders
        col1, col2, col3, col4 = st.columns(4)

        # Create plot placeholder
        plot_placeholder = st.empty()

        # Fetch the latest data for plotting
        df = st.session_state.db.get_recent_data(minutes=display_minutes)

        # Fetch fallback values from the database
        latest_values = st.session_state.db.get_latest_values()

        # Retrieve state values or fallback to database (ensure scalar values)
        temperature = float(st.session_state.get("temperature", latest_values.get("temperature", 0.0)))
        filtered_temperature = float(st.session_state.get("filtered_temperature", latest_values.get("temperature_filtered", 0.0)))
        control_signal = float(st.session_state.get("control_signal", latest_values.get("control_signal", 0.0)))
        setpoint = float(st.session_state.get("setpoint", latest_values.get("setpoint", 25.0)))


        # Update metrics
        with col1:
            st.metric("Temperature", f"{temperature:.1f}°C")
        with col2:
            st.metric("Filtered Temperature", f"{filtered_temperature:.1f}°C")
        with col3:
            st.metric("Control Signal", f"{control_signal:.2f}V")
        with col4:
            st.metric("Setpoint", f"{setpoint:.1f}°C")

        # Update plots
        if not df.empty:
            fig = create_process_plots(
                x_values=df["timestamp"].values,  # Use timestamps for x-axis
                temp_data=df["temperature"].values,
                filtered_temp_data=df["temperature_filtered"].values,
                control_data=df["control_signal"].values,
                setpoint_data=df["setpoint"].values,
            )
            plot_placeholder.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No data available. Run the process to collect data.")
    else:
            st.write("Run the Process to collect data. START/STOP Button on Top Left side")


# Stability Analysis tab content
with tab2:
    st.header("Stability Analysis")
    
    # Perform stability analysis
    stability_metrics = st.session_state.analyzer.analyze_stability(kp, ti, filter_tf)
    
    # Display stability metrics
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Stability Margins")
        st.write(f"Gain Margin: {stability_metrics['gain_margin_db']:.2f} dB")
        st.write(f"Phase Margin: {stability_metrics['phase_margin']:.2f} degrees")
        st.write(f"Critical Gain: {stability_metrics['critical_gain']:.2f}")
    
    with col2:
        st.subheader("Crossover Frequencies")
        st.write(f"Gain Crossover: {stability_metrics['crossover_freq']:.2f} rad/s")
        st.write(f"Phase Crossover: {stability_metrics['w180']:.2f} rad/s")
    
    # Create and display Bode plot
    st.subheader("Bode Plot")
    bode_fig = st.session_state.analyzer.create_bode_plot(kp, ti, filter_tf)
    st.plotly_chart(bode_fig, use_container_width=True)
    
    # Add explanation
    st.markdown("""
    ### Stability Analysis Information
    - The Gain Margin indicates how much the loop gain can be increased before instability
    - The Phase Margin indicates how much additional phase lag can be tolerated
    - The Critical Gain is the gain at which the system becomes marginally stable
    - Stability criteria:
      - Gain Margin > 6 dB
      - Phase Margin > 30 degrees
    """)

# Fragment for Tab3: Data Management
@st.fragment(run_every=5)  # Rerun every 5 seconds
def data_management_fragment():
    st.header("Data Management")
    
    # Ensure stats and recent_data are initialised
    if "stats" not in st.session_state:
        st.session_state.stats = None  # Default value for stats
    if "recent_data" not in st.session_state:
        st.session_state.recent_data = None  # Default value for recent data

    # Refresh stats and recent data
    st.session_state.stats = st.session_state.db.get_statistics()
    st.session_state.recent_data = st.session_state.db.get_recent_data(minutes=60 * 24)


    # Statistics Section
    st.subheader("System Statistics")
    st.session_state.stats = st.session_state.db.get_statistics()
    stats = st.session_state.stats
    if stats is None or not stats or stats["total_records"] == 0:
        st.write("Process not running. Data will appear after starting the Process. START/STOP button on Top-Left")
    else:
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            st.write("Data Summary:")
            st.write(f"- Total Records: {stats['total_records']:,}")
            st.write(f"- First Record: {stats['first_record']}")
            st.write(f"- Last Record: {stats['last_record']}")
        
        with stats_col2:
            st.write("Temperature Statistics:")
            st.write(f"- Average Temperature: {stats['avg_temperature']:.1f}°C")
            st.write(f"- Min Temperature: {stats['min_temperature']:.1f}°C")
            st.write(f"- Max Temperature: {stats['max_temperature']:.1f}°C")
            st.write(f"- Average Control Signal: {stats['avg_control_signal']:.2f}V")
    
    # Data Management Actions
    st.subheader("Data Actions")
    col1, col2, col3 = st.columns(3)
    
    # Initialize state for confirmation
    if 'show_confirm' not in st.session_state:
        st.session_state.show_confirm = False
    
    with col1:
        if st.button("Clear Historical Data", key="clear_data_button"):
            st.session_state.show_confirm = True
        
        # Show confirmation dialog if needed
        if st.session_state.show_confirm:
            st.warning("⚠️ This will permanently delete all historical data.")
            confirm = st.checkbox("I understand and want to proceed with deletion")
            
            col1a, col1b = st.columns(2)
            with col1a:
                if st.button("Confirm Delete"):
                    success = st.session_state.db.clear_historical_data()
                    if success:
                        st.success("✅ Historical data cleared successfully!")
                        # Reset all related session state
                        st.session_state.show_confirm = False
                        if 'recent_data' in st.session_state:
                            del st.session_state.recent_data
                        if 'stats' in st.session_state:
                            st.session_state.stats = st.session_state.db.get_statistics()
                        time.sleep(1)  # Give time to show success message
                        st.rerun()
                    else:
                        st.error("❌ Error clearing historical data")
            
            with col1b:
                if st.button("Cancel"):
                    st.session_state.show_confirm = False
                    st.rerun()
    
    with col2:
        if st.button("Export Data to CSV"):
            if st.session_state.db.export_to_csv():
                st.success("Data exported successfully!")
            else:
                st.error("Error exporting data")
    
    with col3:
        cleanup_days = st.number_input("Days to keep", min_value=1, value=30)
        if st.button("Cleanup Old Data"):
            if st.session_state.db.cleanup_old_data(cleanup_days):
                st.success(f"Removed data older than {cleanup_days} days")
            else:
                st.error("Error cleaning up old data")
    
    # Data Preview
    st.subheader("Recent Data Preview")
    preview_rows = st.slider("Number of rows to preview", 5, 100, 20)
    recent_data = st.session_state.db.get_recent_data(minutes=60*24)  # Last 24 hours
    if not recent_data.empty:
        st.dataframe(recent_data.tail(preview_rows))


with tab1:
    simulation_update_fragment()  # High-frequency simulation updates
    plot_and_metrics_fragment()  # Low-frequency plot and metric updates

with tab3:
    data_management_fragment()  # Periodic updates for stats and data preview