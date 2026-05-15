"""Streamlit dashboard for experiment-engine.

Launches an interactive Streamlit dashboard with sidebar controls
and multiple plot views, enabling live exploration of experiment data.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, List, Optional

from experiment_engine.models import InputData, RenderConfig
from experiment_engine.viz.base import Renderer


class StreamlitDashboard(Renderer):
    """Launches a Streamlit dashboard for interactive data exploration.

    The dashboard renders in the browser and provides sidebar controls
    for plot type selection, color scheme, and axis configuration.

    Examples:
        >>> dashboard = StreamlitDashboard()
        >>> dashboard.run(data)  # launches Streamlit in the browser
    """

    DASHBOARD_TEMPLATE = r'''
import streamlit as st
import numpy as np
import pandas as pd

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Experiment Engine Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Experiment Engine Dashboard")
st.markdown("Interactive exploration of experiment data.")

# ── Load data (injected at launch) ──────────────────────────────────
DATA_ARRAY = np.array({data_array})
COLUMNS = {columns}
INDEX = {index}

if INDEX:
    df = pd.DataFrame(DATA_ARRAY, columns=COLUMNS, index=INDEX)
else:
    df = pd.DataFrame(DATA_ARRAY, columns=COLUMNS)

# ── Sidebar controls ────────────────────────────────────────────────
with st.sidebar:
    st.header("🎛️ Controls")

    plot_type = st.selectbox(
        "Plot type",
        ["line", "scatter", "bar", "histogram", "surface"],
        index=0,
    )

    colormap = st.selectbox(
        "Color scheme",
        ["viridis", "plasma", "inferno", "magma", "cividis",
         "Blues", "Reds", "Greens", "RdYlBu", "Spectral"],
        index=0,
    )

    show_data = st.checkbox("Show raw data", value=False)

    st.divider()
    st.subheader("📐 Dimensions")

    n_samples, n_features = df.shape

    if plot_type == "scatter" and n_features >= 2:
        x_col = st.selectbox("X axis", COLUMNS, index=0)
        y_col = st.selectbox("Y axis", COLUMNS, index=min(1, n_features - 1))
        color_col = st.selectbox(
            "Color by", ["None"] + COLUMNS, index=2 if n_features >= 3 else 0
        )
    else:
        x_col = COLUMNS[0] if COLUMNS else "index"
        y_col = COLUMNS[1] if n_features >= 2 else COLUMNS[0]
        color_col = "None"

    st.divider()
    st.caption(f"Rows: {n_samples}  •  Columns: {n_features}")

    auto_refresh = st.checkbox("Auto-refresh", value=False)
    if auto_refresh:
        st.rerun()

# ── Main panel ──────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"📈 {plot_type.title()} Plot")

    if plot_type == "line":
        import plotly.express as px
        fig = px.line(df, title=f"{plot_type.title()} Plot",
                      color_discrete_sequence=px.colors.sequential.Plasma)
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    elif plot_type == "scatter":
        import plotly.express as px
        if color_col != "None":
            fig = px.scatter(
                df, x=x_col, y=y_col, color=color_col,
                title=f"{x_col} vs {y_col} (colored by {color_col})",
                color_continuous_scale=colormap,
            )
        else:
            fig = px.scatter(
                df, x=x_col, y=y_col,
                title=f"{x_col} vs {y_col}",
            )
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    elif plot_type == "bar":
        import plotly.express as px
        fig = px.bar(df, title=f"Bar Chart",
                      color_discrete_sequence=px.colors.sequential.Plasma,
                      barmode="group")
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    elif plot_type == "histogram":
        import plotly.express as px
        fig = px.histogram(df, title="Histogram",
                           color_discrete_sequence=px.colors.sequential.Plasma,
                           nbins=30, barmode="overlay", opacity=0.6)
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    elif plot_type == "surface":
        import plotly.graph_objects as go
        side = int(np.ceil(np.sqrt(n_samples)))
        x_1d = np.linspace(-3, 3, side)
        y_1d = np.linspace(-3, 3, side)
        x_grid, y_grid = np.meshgrid(x_1d, y_1d)
        z_grid = np.zeros((side, side))
        for idx in range(min(n_samples, side * side)):
            i = idx // side
            j = idx % side
            z_grid[i, j] = DATA_ARRAY[idx, 0] if n_features >= 1 else 0
        fig = go.Figure(data=[
            go.Surface(z=z_grid, x=x_grid, y=y_grid,
                       colorscale=colormap, opacity=0.9)
        ])
        fig.update_layout(title="3D Surface Plot",
                          scene=dict(xaxis_title="X", yaxis_title="Y",
                                     zaxis_title=COLUMNS[0] if COLUMNS else "Z"))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("ℹ️ Summary")

    col_meta = pd.DataFrame({{
        "Mean": df.mean(numeric_only=True),
        "Std": df.std(numeric_only=True),
        "Min": df.min(numeric_only=True),
        "Max": df.max(numeric_only=True),
    }}).round(4)

    st.dataframe(col_meta, use_container_width=True)

    if show_data:
        st.divider()
        st.subheader("📄 Raw Data")
        st.dataframe(df, use_container_width=True, height=400)

st.divider()
st.caption("Experiment Engine • Streamlit Dashboard")
'''

    @property
    def name(self) -> str:
        return "streamlit"

    def render(
        self,
        data: InputData,
        config: VisualizationConfig,
        **kwargs: Any,
    ) -> str:
        """Render is not applicable for Streamlit; use :meth:`run` instead.

        Raises:
            NotImplementedError: Always — call ``run()`` instead.
        """
        raise NotImplementedError(
            "StreamlitDashboard does not support render(). "
            "Use the run() method to launch the dashboard."
        )

    def run(
        self,
        data: InputData,
        port: int = 8501,
        open_browser: bool = True,
        **kwargs: Any,
    ) -> subprocess.Popen:
        """Launch a Streamlit dashboard for the given *data*.

        Generates a self-contained Python script with the data embedded
        and launches it via ``streamlit run``.

        Args:
            data: Input data to display.
            port: Local port for the Streamlit server (default: 8501).
            open_browser: Whether to open the browser automatically
                (default: True).
            **kwargs: Additional keyword arguments forwarded to the
                dashboard template.

        Returns:
            subprocess.Popen: Handle to the running Streamlit process.
        """
        script = self._generate_script(data)
        script_path = self._write_script(script)

        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(script_path),
            "--server.port",
            str(port),
            "--server.headless",
            "false" if open_browser else "true",
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return process

    def _generate_script(self, data: InputData) -> str:
        """Generate the Streamlit dashboard Python code.

        Injects the data array, columns, and index into the template.

        Args:
            data: Input data to embed in the script.

        Returns:
            str: Complete Python script for the dashboard.
        """
        data_array_repr = repr(data.data.tolist())
        columns_repr = repr(data.columns)
        index_repr = repr(data.index) if data.index else "None"

        script = self.DASHBOARD_TEMPLATE.format(
            data_array=data_array_repr,
            columns=columns_repr,
            index=index_repr,
        )
        return script

    @staticmethod
    def _write_script(script: str) -> Path:
        """Write the dashboard script to a temporary file.

        Args:
            script: The Python script content.

        Returns:
            Path: Path to the written script file.
        """
        temp_dir = Path(tempfile.gettempdir()) / "experiment_engine_dashboards"
        temp_dir.mkdir(parents=True, exist_ok=True)

        script_path = temp_dir / "dashboard.py"
        script_path.write_text(script, encoding="utf-8")
        return script_path
