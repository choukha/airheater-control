import numpy as np
import control
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class StabilityAnalyzer:
    def __init__(self, Kh=3.5, theta_t=22, theta_d=2):
        """Initialize stability analyzer with air heater parameters"""
        self.Kh = Kh          # Process gain
        self.theta_t = theta_t # Time constant
        self.theta_d = theta_d # Time delay
        
    def get_process_tf(self):
        """Get process transfer function with Padé approximation for delay"""
        # Process transfer function without delay
        num_p = np.array([self.Kh])
        den_p = np.array([self.theta_t, 1])
        H1 = control.tf(num_p, den_p)
        
        # Padé approximation for delay
        num_pade, den_pade = control.pade(self.theta_d, 3)  # 3rd order Padé
        H2 = control.tf(num_pade, den_pade)
        
        # Complete process transfer function
        Hp = control.series(H1, H2)
        return Hp
    
    def get_controller_tf(self, Kp, Ti):
        """Get PI controller transfer function"""
        num_c = np.array([Kp*Ti, Kp])
        den_c = np.array([Ti, 0])
        return control.tf(num_c, den_c)
    
    def get_filter_tf(self, Tf):
        """Get low-pass filter transfer function"""
        num_f = np.array([1])
        den_f = np.array([Tf, 1])
        return control.tf(num_f, den_f)
    
    def analyze_stability(self, Kp, Ti, Tf):
        """Perform stability analysis and return key metrics"""
        # Get process transfer function
        Hp = self.get_process_tf()
        
        # Get controller transfer function
        Hc = self.get_controller_tf(Kp, Ti)
        
        # Get filter transfer function
        Hf = self.get_filter_tf(Tf)
        
        # Get loop transfer function
        L = control.series(Hc, Hp, Hf)
        
        # Calculate stability margins
        gm, pm, wpc, wgc = control.margin(L)
        
        # Calculate critical gain
        Kc = Kp * gm
        
        return {
            'gain_margin': gm,
            'gain_margin_db': 20 * np.log10(gm),
            'phase_margin': pm,
            'critical_gain': Kc,
            'crossover_freq': wgc,
            'w180': wpc
        }
    
    def create_bode_plot(self, Kp, Ti, Tf):
        """Create Bode plot using plotly"""
        # Get transfer functions
        Hp = self.get_process_tf()
        Hc = self.get_controller_tf(Kp, Ti)
        Hf = self.get_filter_tf(Tf)
        L = control.series(Hc, Hp, Hf)
        
        # Generate frequency points
        w = np.logspace(-3, 2, 1000)
        
        # Get magnitude and phase
        mag, phase, w = control.bode(L, w, plot=False)
        
        # Convert to dB and degrees
        mag_db = 20 * np.log10(mag)
        phase_deg = phase * 180 / np.pi
        
        # Create Bode plot
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Magnitude Plot', 'Phase Plot'),
            vertical_spacing=0.15
        )
        
        # Add magnitude plot
        fig.add_trace(
            go.Scatter(x=w, y=mag_db, name="Magnitude",
                      line=dict(color='blue', width=2)),
            row=1, col=1
        )
        
        # Add phase plot
        fig.add_trace(
            go.Scatter(x=w, y=phase_deg, name="Phase",
                      line=dict(color='red', width=2)),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True,
            xaxis_type="log",
            xaxis2_type="log"
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Frequency [rad/s]", row=2, col=1)
        fig.update_yaxes(title_text="Magnitude [dB]", row=1, col=1)
        fig.update_yaxes(title_text="Phase [deg]", row=2, col=1)
        
        return fig