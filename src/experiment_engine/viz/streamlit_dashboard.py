"""Streamlit dashboard for experiment-engine.

Launches an interactive Streamlit dashboard with sidebar controls
and multiple plot views, enabling live exploration of experiment data.
Also provides a dedicated pipeline results view.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from experiment_engine.models import InputData, PipelineResult, RenderConfig
from experiment_engine.viz.base import Renderer


class StreamlitDashboard(Renderer):
    """Launches a Streamlit dashboard for interactive data exploration.

    The dashboard renders in the browser and provides sidebar controls
    for plot type selection, color scheme, and axis configuration.

    Use :meth:`run` for :class:`~experiment_engine.models.InputData` and
    :meth:`run_pipeline_result` for
    :class:`~experiment_engine.models.PipelineResult`.

    Examples:
        >>> dashboard = StreamlitDashboard()
        >>> dashboard.run(data)  # launches Streamlit in the browser
        >>> dashboard.run_pipeline_result(result)  # pipeline result view
    """

    DASHBOARD_TEMPLATE = r"""
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
    st.caption(f"Rows: {{n_samples}}  •  Columns: {{n_features}}")

    auto_refresh = st.checkbox("Auto-refresh", value=False)
    if auto_refresh:
        st.rerun()

# ── Main panel ──────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"📈 {{plot_type.title()}} Plot")

    if plot_type == "line":
        import plotly.express as px
        fig = px.line(df, title=f"{{plot_type.title()}} Plot",
                      color_discrete_sequence=px.colors.sequential.Plasma)
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    elif plot_type == "scatter":
        import plotly.express as px
        if color_col != "None":
            fig = px.scatter(
                df, x=x_col, y=y_col, color=color_col,
                title=f"{{x_col}} vs {{y_col}} (colored by {{color_col}})",
                color_continuous_scale=colormap,
            )
        else:
            fig = px.scatter(
                df, x=x_col, y=y_col,
                title=f"{{x_col}} vs {{y_col}}",
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
"""

    PIPELINE_TEMPLATE = r"""
import streamlit as st
import numpy as np
import pandas as pd
import json

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pipeline Results — Experiment Engine",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔬 Pipeline Results")
st.markdown(f"**Experiment:** {experiment_name}")

# ── Pipeline metadata (injected at launch) ──────────────────────────
PIPELINE_META = {pipeline_meta}
STAGES = {stages_data}
FINAL_OUTPUT = {final_output}

# ── Emoji helper for status ─────────────────────────────────────────
_STATUS_EMOJI = {{
    "completed": "✅",
    "failed": "❌",
    "partial": "⚠️",
    "pending": "⏳",
    "running": "🔄",
    "skipped": "⏭️",
}}


def _status_badge(status: str) -> str:
    emoji = _STATUS_EMOJI.get(status.lower(), "❓")
    return f"{{emoji}} {{status.title()}}"


# ── Overall pipeline summary ────────────────────────────────────────
overall_status = PIPELINE_META.get("status", "unknown")
total_duration = PIPELINE_META.get("total_duration_ms", 0.0)

total_stages = len(STAGES)
completed_count = sum(
    1 for s in STAGES if s.get("status") in ("completed", "skipped")
)
failed_count = sum(1 for s in STAGES if s.get("status") == "failed")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Pipeline Status", _status_badge(overall_status))
with col2:
    st.metric("Total Duration", f"{{total_duration:.1f}} ms")
with col3:
    st.metric("Stages Completed", f"{{completed_count}} / {{total_stages}}")
with col4:
    st.metric("Failed Stages", failed_count)

st.divider()

# ── Tabs: Stage Results | Errors | Final Output | Correlation ─────
tabs = st.tabs(["📋 Stage Results", "❌ Errors", "📤 Final Output"])

# ── Tab 1: Stage Results Table ──────────────────────────────────────
with tabs[0]:
    st.subheader("Stage Execution Summary")

    if STAGES:
        df_stages = pd.DataFrame(STAGES)
        col_map = {{
            "stage_name": "Stage",
            "stage_type": "Type",
            "status": "Status",
            "duration_ms": "Duration (ms)",
            "error": "Error",
        }}
        display_df = df_stages.rename(columns=col_map)

        # Color status column with emoji
        display_df["Status"] = display_df["Status"].apply(
            lambda s: _status_badge(s)
        )

        # Drop error column if no errors exist
        if not any(s.get("error") for s in STAGES):
            display_df = display_df.drop(columns=["Error"], errors="ignore")

        st.dataframe(
            display_df,
            use_container_width=True,
            height=min(60 + len(STAGES) * 40, 600),
        )

        # Optional: duration bar chart
        if len(STAGES) > 1:
            st.subheader("Stage Duration (ms)")
            st.bar_chart(
                df_stages,
                x="stage_name",
                y="duration_ms",
            )
    else:
        st.info("No stage results recorded.")

# ── Tab 2: Error Details ────────────────────────────────────────────
with tabs[1]:
    st.subheader("Stage Errors")

    errors = [s for s in STAGES if s.get("error")]
    if errors:
        for s in errors:
            with st.expander(
                f"❌ {{s['stage_name']}} ({{s['stage_type']}})",
                expanded=True,
            ):
                st.code(s["error"], language="text")
    else:
        st.success("✅ No errors — all stages completed successfully!")

# ── Tab 3: Final Output ─────────────────────────────────────────────
with tabs[2]:
    st.subheader("Final Pipeline Output")

    if FINAL_OUTPUT is not None:
        output = FINAL_OUTPUT
        # Display based on type
        if isinstance(output, list):
            if output and isinstance(output[0], (list, tuple)):
                # 2D tabular data
                st.dataframe(pd.DataFrame(output), use_container_width=True)
            else:
                # 1D list
                st.dataframe(
                    pd.DataFrame({{"Output": list(output)}}),
                    use_container_width=True,
                )
        elif isinstance(output, dict):
            st.json(output)
        elif isinstance(output, str) and len(output) > 500:
            st.text(output)
        else:
            st.write(output)

        # Try to visualize if it looks like numeric data
        if isinstance(output, (list, tuple)) and len(output) > 0:
            try:
                arr = np.array(output, dtype=float)
                st.subheader("Output Visualization")
                st.line_chart(arr, use_container_width=True)
            except (ValueError, TypeError):
                pass
    else:
        st.info("No output data available.")

st.divider()
st.caption("Experiment Engine • Pipeline Results Dashboard")
"""

    @property
    def name(self) -> str:
        return "streamlit"

    def render(
        self,
        data: InputData,
        config: RenderConfig,
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

        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def run_pipeline_result(
        self,
        result: PipelineResult,
        port: int = 8501,
        open_browser: bool = True,
        **kwargs: Any,
    ) -> subprocess.Popen:
        """Launch a Streamlit dashboard visualising a ``PipelineResult``.

        Generates a self-contained Python script with the pipeline result
        data embedded and launches it via ``streamlit run``.

        The dashboard shows:
        - Overall pipeline status badge + summary metrics
        - Stage execution table (name, type, status, duration, error)
        - Failed stage error details
        - Final pipeline output with basic visualisation

        Args:
            result: The pipeline execution result to visualise.
            port: Local port for the Streamlit server (default: 8501).
            open_browser: Whether to open the browser automatically
                (default: True).
            **kwargs: Additional keyword arguments forwarded to the
                dashboard template.

        Returns:
            subprocess.Popen: Handle to the running Streamlit process.
        """
        script = self._generate_pipeline_script(result)
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

        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

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

        return self.DASHBOARD_TEMPLATE.format(
            data_array=data_array_repr,
            columns=columns_repr,
            index=index_repr,
        )

    def _generate_pipeline_script(self, result: PipelineResult) -> str:
        """Generate the pipeline result dashboard Python code.

        Injects pipeline metadata, stage list, and final output into the
        pipeline template.

        Args:
            result: Pipeline execution result to embed.

        Returns:
            str: Complete Python script for the pipeline dashboard.
        """
        # Serialise pipeline metadata dict (JSON-compatible)
        pipeline_meta_repr = repr(
            {
                "experiment_name": result.experiment_name,
                "status": result.status.value
                if hasattr(result.status, "value")
                else str(result.status),
                "total_duration_ms": result.total_duration_ms,
                "started_at": result.started_at,
                "completed_at": result.completed_at,
            }
        )

        # Serialise stages as list of dicts
        stages_data = []
        for s in result.stages:
            stages_data.append(
                {
                    "stage_name": s.stage_name,
                    "stage_type": s.stage_type,
                    "status": s.status.value
                    if hasattr(s.status, "value")
                    else str(s.status),
                    "duration_ms": round(s.duration_ms, 2),
                    "error": s.error,
                }
            )
        stages_repr = repr(stages_data)

        # Serialise final output
        final_output = result.output
        if final_output is not None:
            if hasattr(final_output, "tolist"):
                final_output_repr = repr(final_output.tolist())
            else:
                final_output_repr = repr(final_output)
        else:
            final_output_repr = "None"

        return self.PIPELINE_TEMPLATE.format(
            experiment_name=repr(result.experiment_name),
            pipeline_meta=pipeline_meta_repr,
            stages_data=stages_repr,
            final_output=final_output_repr,
        )

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
