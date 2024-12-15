import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_process_plots(df):
    """Create process plots with plotly"""
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Temperature Response', 'Control Signal'),
        vertical_spacing=0.15
    )
    
    # Temperature plot
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['temperature'],
                name="Temperature", line=dict(color='blue', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['temperature_filtered'],
                name="Filtered Temperature", line=dict(color='green', width=2)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['setpoint'],
                name="Setpoint", line=dict(color='red', dash='dash', width=2)),
        row=1, col=1
    )
    
    # Control signal plot
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['control_signal'],
                name="Control Signal", line=dict(color='orange', width=2)),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255, 255, 255, 0.8)'
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    # Update axes
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Temperature [°C]", row=1, col=1)
    fig.update_yaxes(title_text="Control Signal [V]", row=2, col=1)
    
    # Set y-axis ranges
    fig.update_yaxes(range=[15, 55], row=1, col=1)
    fig.update_yaxes(range=[-0.5, 5.5], row=2, col=1)
    
    return fig