import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def build_sparkline_area(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str | None = None,
    height: int = 110,
    line_color: str = "rgba(91,91,214,1)",
    top_fill_rgba: str = "rgba(91,91,214,0.35)",
    bottom_fill_rgba: str = "rgba(91,91,214,0.0)",
) -> go.Figure | None:
    if df is None or df.empty or y_col not in df.columns:
        return None

    fig = go.Figure()
    scatter_kwargs = dict(
        x=df[x_col],
        y=df[y_col],
        mode="lines",
        line=dict(color=line_color, width=2),
        fill="tozeroy",
        fillcolor=top_fill_rgba,  # fallback if gradient unsupported
        name=title or "",
    )

    # Plotly's fillgradient is available in newer versions; use if present
    try:
        scatter_kwargs["fillgradient"] = dict(
            type="vertical",
            # Some Plotly builds map 0->bottom and 1->top. To ensure
            # transparency at the baseline (bottom) and opacity near the line (top),
            # place the transparent color at 0 and the opaque at 1.
            colorscale=[[0, bottom_fill_rgba], [1, top_fill_rgba]],
        )
    except Exception:
        pass

    fig.add_trace(go.Scatter(**scatter_kwargs))
    # Smooth the line for a curved appearance instead of straight segments
    fig.update_traces(line_shape="spline")

    fig.update_layout(
        showlegend=False,
        height=height,
        margin=dict(l=10, r=10, t=22, b=0),
        xaxis_title=None,
        yaxis_title=None,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False, showline=False, ticks="")
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False, showline=False, ticks="")
    return fig


def format_number(value) -> str:
    try:
        if value is None:
            return "—"
        # Use thousands separators, no decimals for ints
        if float(value).is_integer():
            return f"{int(value):,}"
        return f"{float(value):,.2f}"
    except Exception:
        return str(value)


def format_percent(value) -> str:
    try:
        if value is None:
            return "—"
        return f"{float(value):.2f}%"
    except Exception:
        return str(value)
