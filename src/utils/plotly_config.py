"""
Plotly configuration utilities to avoid deprecation warnings
"""
import streamlit as st
from typing import Any, Dict, Optional
import plotly.graph_objects as go

# Global Plotly configuration to avoid deprecation warnings
DEFAULT_PLOTLY_CONFIG = {
    'displayModeBar': False,
    'displaylogo': False,
    'staticPlot': False,
    'responsive': True,
    'showTips': False,
    'showAxisDragHandles': False,
    'showAxisRangeEntryBoxes': False,
    'doubleClick': 'reset',
    'scrollZoom': False,
    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d', 'zoom2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'chart',
        'height': 500,
        'width': 700,
        'scale': 1
    }
}

def render_plotly_chart(
    fig: go.Figure, 
    width: str = 'stretch', 
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Render a Plotly chart with consistent configuration to avoid deprecation warnings.
    
    Args:
        fig: Plotly figure object
        width: Chart width ('stretch' or 'content')
        config: Optional custom config (defaults to DEFAULT_PLOTLY_CONFIG)
        **kwargs: Additional arguments passed to st.plotly_chart
    """
    if config is None:
        config = DEFAULT_PLOTLY_CONFIG.copy()
    
    # Ensure we always have the required config keys to avoid warnings
    final_config = DEFAULT_PLOTLY_CONFIG.copy()
    final_config.update(config)
    
    st.plotly_chart(fig, width=width, config=final_config, **kwargs)