"""Visualization layer for experiment-engine.

Provides renderers and dashboards for visualizing experimental data
through various backends: matplotlib, plotly, streamlit, and console.
"""

from experiment_engine.viz.base import Renderer
from experiment_engine.viz.matplotlib_renderer import MatplotlibRenderer
from experiment_engine.viz.plotly_renderer import PlotlyRenderer
from experiment_engine.viz.streamlit_dashboard import StreamlitDashboard
from experiment_engine.viz.console import ConsoleRenderer

__all__ = [
    "Renderer",
    "MatplotlibRenderer",
    "PlotlyRenderer",
    "StreamlitDashboard",
    "ConsoleRenderer",
]
