import streamlit as st
import time
from datetime import datetime, timedelta
from simulator import AirHeaterSimulator
from stability_analysis import StabilityAnalyzer
from plotting import create_process_plots
from database_handler import DatabaseHandler
from users import UserAuth
from session_manager import SessionManager
from process_manager import ProcessManager

# Page config
st.set_page_config(layout="wide")

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.db = DatabaseHandler()
    st.session_state.simulator = AirHeaterSimulator(st.session_state.db)
    st.session_state.analyzer = StabilityAnalyzer()
    st.session_state.auth = UserAuth()
    st.session_state.session_manager = SessionManager()
    st.session_state.process_manager = ProcessManager()
    st.session_state.data_version = 0
    st.session_state.last_refresh = time.time()
    st.session_state.initialized = True
    st.session_state.is_running = False
    st.session_state.display_minutes = 1.0

def login_page():
    """Display login page"""
    st.title("Air Heater Control System - Login")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                role = st.session_state.auth.verify_user(username, password)
                if role:
                    session_id = st.session_state.session_manager.create_session(username, role)
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = role
                    st.session_state.session_id = session_id
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with col2:
        st.markdown("### Continue as Guest")
        if st.button("Guest Access"):
            role = "guest"
            session_id = st.session_state.session_manager.create_session("guest", role)
            st.session_state.authenticated = True
            st.session_state.username = "guest"
            st.session_state.role = role
            st.session_state.session_id = session_id
            st.success("Logged in as guest")
            time.sleep(1)
            st.rerun()

def create_sidebar():
    """Create sidebar with controls and user info"""
    # User information
    st.sidebar.header("User Information")
    st.sidebar.write(f"User: {st.session_state.username}")
    st.sidebar.write(f"Role: {st.session_state.role}")
    
    if st.sidebar.button("Logout"):
        if st.session_state.session_id:
            st.session_state.session_manager.end_session(st.session_state.session_id)
        for key in ['authenticated', 'username', 'role', 'session_id']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # Mode Selection
    st.sidebar.header("Process Mode")
    if 'process_mode' not in st.session_state:
        st.session_state.process_mode = "simulator"
    
    mode = st.sidebar.radio(
        "Select Mode",
        ["simulator", "DAQ hardware"],
        index=0 if st.session_state.process_mode == "simulator" else 1,
        key="mode_selector"
    )
    
    # Handle mode change
    if mode != st.session_state.process_mode:
        if mode == "DAQ hardware":
            try:
                import nidaqmx
                devices = nidaqmx.system.System.local().devices
                if not devices:
                    st.sidebar.error("No DAQ devices found!")
                    st.session_state.process_mode = "simulator"
                else:
                    st.session_state.process_mode = mode
                    st.sidebar.success(f"Found DAQ device: {devices[0].name}")
            except ImportError:
                st.sidebar.warning("Couldn't connect to DAQ hardware! Staying in simulator mode.")
                st.session_state.process_mode = "simulator"
        else:
            st.session_state.process_mode = mode

    # Start/Stop Control (Available for all users)
    st.sidebar.header("Click Twice to Start/Stop")
    if st.session_state.simulator.is_running():
        if st.sidebar.button("🛑 STOP", key="stop_button"):
            st.session_state.simulator.stop()
            st.session_state.is_running = False
    else:
        if st.sidebar.button("✅ START", key="start_button"):
            st.session_state.simulator.start()
            st.session_state.is_running = True

    # Display window options
    st.sidebar.header("Display Settings")
    st.session_state.display_minutes = st.sidebar.slider("Display window (minutes)", 1, 60, 10, 1)

    # Controller settings (Operators only)
    st.sidebar.header("Controller Settings")
    disabled = st.session_state.role != "operator"
    
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

    setpoint = st.sidebar.slider("Temperature Setpoint (°C)", 20.0, 50.0, default_setpoint, 0.5, disabled=disabled)
    kp = st.sidebar.slider("Proportional Gain (Kp)", 0.1, 5.0, default_kp, 0.1, disabled=disabled)
    ti = st.sidebar.slider("Integral Time (Ti)", 0.1, 20.0, default_ti, 0.1, disabled=disabled)

    st.sidebar.header("Process Settings")
    noise_std = st.sidebar.slider("Noise Level (std)", 0.0, 1.0, 0.05, 0.01, disabled=disabled)
    filter_tf = st.sidebar.slider("Filter Time Constant (Tf)", 0.1, 2.0, 0.5, 0.1, disabled=disabled)

    # Update simulator parameters (if operator)
    if st.session_state.role == "operator":
        st.session_state.simulator.update_parameters(setpoint, kp, ti, noise_std, filter_tf)

    return setpoint, kp, ti, noise_std, filter_tf

@st.fragment(run_every=0.01)
def simulation_update_fragment():
    """High-frequency simulation updates"""
    if st.session_state.simulator.is_running():
        temp, filtered_temp, control = st.session_state.simulator.simulate_step()
        st.session_state.temperature = temp
        st.session_state.filtered_temperature = filtered_temp
        st.session_state.control_signal = control

@st.fragment(run_every=10)
def plot_and_metrics_fragment():
    """Real-time plot and metrics updates"""
    st.header("Air Heater Control")
    if st.session_state.is_running:
        col1, col2, col3, col4 = st.columns(4)
        plot_placeholder = st.empty()
        
        # Fetch and display data
        df = st.session_state.db.get_recent_data(minutes=st.session_state.display_minutes)
        latest_values = st.session_state.db.get_latest_values()

        temperature = float(st.session_state.get("temperature", latest_values.get("temperature", 0.0)))
        filtered_temperature = float(st.session_state.get("filtered_temperature", latest_values.get("temperature_filtered", 0.0)))
        control_signal = float(st.session_state.get("control_signal", latest_values.get("control_signal", 0.0)))
        setpoint = float(st.session_state.get("setpoint", latest_values.get("setpoint", 25.0)))

        with col1:
            st.metric("Temperature", f"{temperature:.1f}°C")
        with col2:
            st.metric("Filtered Temperature", f"{filtered_temperature:.1f}°C")
        with col3:
            st.metric("Control Signal", f"{control_signal:.2f}V")
        with col4:
            st.metric("Setpoint", f"{setpoint:.1f}°C")

        if not df.empty:
            fig = create_process_plots(
                x_values=df["timestamp"].values,
                temp_data=df["temperature"].values,
                filtered_temp_data=df["temperature_filtered"].values,
                control_data=df["control_signal"].values,
                setpoint_data=df["setpoint"].values,
            )
            plot_placeholder.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Run the Process to collect data. START/STOP Button on Top Left side")

@st.fragment(run_every=5)
def data_management_fragment():
    """Data management tab content"""
    st.header("Data Management")
    
    if st.session_state.role != "operator":
        st.info("Data management features are only available for operators")
        return
        
    # Statistics Section
    st.subheader("System Statistics")
    stats = st.session_state.db.get_statistics()
    if stats is None or not stats or stats["total_records"] == 0:
        st.write("No data available. Start the process to collect data.")
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
    
    # Data Management Actions (Operators only)
    st.subheader("Data Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Clear Historical Data"):
            confirm = st.checkbox("Confirm data deletion")
            if confirm and st.button("Proceed with Deletion"):
                if st.session_state.db.clear_historical_data():
                    st.success("Historical data cleared successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error clearing historical data")
    
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

def main():
    """Main application entry point"""
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        login_page()
        return

    # Verify session is still valid
    session = st.session_state.session_manager.get_session(st.session_state.session_id)
    if not session:
        st.warning("Session expired. Please log in again.")
        for key in ['authenticated', 'username', 'role', 'session_id']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.title("Air Heater Control and Monitoring System")
    
    # Create sidebar and get parameters
    setpoint, kp, ti, noise_std, filter_tf = create_sidebar()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Control", "Stability Analysis", "Data Management"])
    
    with tab1:
        simulation_update_fragment()
        plot_and_metrics_fragment()
    
    with tab2:
        st.header("Stability Analysis")
        stability_metrics = st.session_state.analyzer.analyze_stability(kp, ti, filter_tf)
        
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
        
        st.subheader("Bode Plot")
        bode_fig = st.session_state.analyzer.create_bode_plot(kp, ti, filter_tf)
        st.plotly_chart(bode_fig, use_container_width=True)
        
        st.markdown("""
        ### Stability Analysis Information
        - The Gain Margin indicates how much the loop gain can be increased before instability
        - The Phase Margin indicates how much additional phase lag can be tolerated
        - The Critical Gain is the gain at which the system becomes marginally stable
        - Stability criteria:
          - Gain Margin > 6 dB
          - Phase Margin > 30 degrees
        """)
    
    with tab3:
        data_management_fragment()

if __name__ == "__main__":
    main()