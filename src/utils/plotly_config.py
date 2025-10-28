"""
Plotly configuration utilities to avoid deprecation warnings
"""
import streamlit as st
from typing import Any, Dict, Optional
import plotly.graph_objects as go

# Global Plotly configuration to avoid deprecation warnings
DEFAULT_PLOTLY_CONFIG = {
    'displayModeBar': 'hover',
    'displaylogo': False,
    'staticPlot': False,
    'responsive': True,
    'showTips': True,
    'showAxisDragHandles': True,
    'showAxisRangeEntryBoxes': True,
    'doubleClick': 'reset',
    'scrollZoom': True,
    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
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
    use_container_width: bool = True,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Render a Plotly chart with consistent configuration to avoid deprecation warnings.
    
    Args:
        fig: Plotly figure object
        use_container_width: Whether to use full container width
        config: Optional custom config (defaults to DEFAULT_PLOTLY_CONFIG)
        **kwargs: Additional arguments passed to st.plotly_chart
    """
    if config is None:
        config = DEFAULT_PLOTLY_CONFIG.copy()
    
    # Ensure we always have the required config keys to avoid warnings
    final_config = DEFAULT_PLOTLY_CONFIG.copy()
    final_config.update(config)
    
    st.plotly_chart(fig, use_container_width=use_container_width, config=final_config, **kwargs)