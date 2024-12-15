import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_process_plots(x_values, temp_data, filtered_temp_data, control_data, setpoint_data):
    """Create process plots using Plotly."""
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Temperature Response', 'Control Signal'),
        vertical_spacing=0.15
    )

    # Add temperature traces
    fig.add_trace(
        go.Scatter(x=x_values, y=temp_data, name="Temperature",
                   line=dict(color='blue', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=x_values, y=filtered_temp_data, name="Filtered Temperature",
                   line=dict(color='green', width=2)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=x_values, y=setpoint_data, name="Setpoint",
                   line=dict(color='red', dash='dash', width=2)),
        row=1, col=1
    )

    # Add control signal trace
    fig.add_trace(
        go.Scatter(x=x_values, y=control_data, name="Control Signal",
                   line=dict(color='orange', width=2)),
        row=2, col=1
    )

    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="bottom",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255, 255, 255, 0.8)'
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )

    # Update axes
    fig.update_xaxes(title_text="Time", row=1, col=1)
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Temperature [°C]", row=1, col=1)
    fig.update_yaxes(title_text="Control Signal [V]", row=2, col=1)

    return fig
