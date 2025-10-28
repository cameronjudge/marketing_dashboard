"""
Plotly configuration utilities to avoid deprecation warnings
"""
import streamlit as st
from typing import Any, Dict, Optional
import plotly.graph_objects as go

# Brand color palette with high contrast for excellent readability
BRAND_COLORS = {
    'primary': {
        'keppel': '#3EB2A2',
        'indigo_blue': '#0E415F',
        'white': '#FFFFFF',
        'dark_text': '#1F2937'  # Very dark text for maximum readability
    },
    'secondary': {
        'tea_green': '#C8F9D5',
        'light_green': '#A2EEB7',
        'honeydew': '#E9FFEF',
        'periwinkle': '#B8BFF1',
        'picton_blue': '#57AEE0'
    },
    'high_contrast': {
        # Completely different color families for maximum distinction
        'navy_blue': '#1E3A8A',        # Strong navy blue
        'deep_orange': '#EA580C',      # Vibrant orange
        'forest_green': '#166534',     # Deep forest green
        'burgundy': '#991B1B',         # Deep red/burgundy
        'purple': '#7C3AED',           # Vivid purple
        'teal_dark': '#0F766E',        # Dark teal (different from keppel)
        'amber': '#D97706',            # Amber/gold
        'slate': '#475569'             # Dark slate gray
    }
}

# High contrast chart color sequence - each color is distinctly different
CHART_COLOR_SEQUENCE = [
    BRAND_COLORS['primary']['keppel'],           # #3EB2A2 - Teal (brand primary)
    BRAND_COLORS['high_contrast']['navy_blue'],  # #1E3A8A - Navy Blue
    BRAND_COLORS['high_contrast']['deep_orange'], # #EA580C - Orange
    BRAND_COLORS['high_contrast']['forest_green'], # #166534 - Forest Green
    BRAND_COLORS['high_contrast']['burgundy'],   # #991B1B - Burgundy
    BRAND_COLORS['high_contrast']['purple'],     # #7C3AED - Purple
    BRAND_COLORS['high_contrast']['amber'],      # #D97706 - Amber
    BRAND_COLORS['high_contrast']['slate']       # #475569 - Slate
]

# Special color pairs for dual-axis charts (bar + line combinations)
DUAL_CHART_COLORS = {
    'bar_primary': BRAND_COLORS['primary']['keppel'],      # Teal bars
    'line_primary': BRAND_COLORS['high_contrast']['deep_orange'], # Orange line
    'bar_secondary': BRAND_COLORS['high_contrast']['navy_blue'],  # Navy bars  
    'line_secondary': BRAND_COLORS['high_contrast']['burgundy']   # Burgundy line
}

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
    'scrollZoom': False,
    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'chart',
        'height': 500,
        'width': 700,
        'scale': 1
    }
}

def get_brand_layout_config():
    """
    Get standard layout configuration with brand colors
    """
    return {
        'plot_bgcolor': "rgba(0,0,0,0)",
        'paper_bgcolor': "rgba(0,0,0,0)",
        'font': {'color': BRAND_COLORS['primary']['indigo_blue']},
        'title': {'font': {'color': BRAND_COLORS['primary']['indigo_blue']}},
        'colorway': CHART_COLOR_SEQUENCE
    }

def apply_brand_styling(fig: go.Figure) -> go.Figure:
    """
    Apply brand styling to a Plotly figure
    
    Args:
        fig: Plotly figure object
        
    Returns:
        Styled figure with brand colors and formatting
    """
    brand_layout = get_brand_layout_config()
    
    fig.update_layout(
        plot_bgcolor=brand_layout['plot_bgcolor'],
        paper_bgcolor=brand_layout['paper_bgcolor'],
        font=brand_layout['font'],
        colorway=brand_layout['colorway']
    )
    
    # Update axes styling
    fig.update_xaxes(
        showgrid=False,
        color=BRAND_COLORS['primary']['indigo_blue']
    )
    fig.update_yaxes(
        showgrid=False,
        color=BRAND_COLORS['primary']['indigo_blue']
    )
    
    return fig

def render_plotly_chart(
    fig: go.Figure, 
    use_container_width: bool = True,
    config: Optional[Dict[str, Any]] = None,
    apply_brand_colors: bool = True,
    **kwargs
) -> None:
    """
    Render a Plotly chart with consistent configuration to avoid deprecation warnings.
    
    Args:
        fig: Plotly figure object
        use_container_width: Whether to use full container width
        config: Optional custom config (defaults to DEFAULT_PLOTLY_CONFIG)
        apply_brand_colors: Whether to apply brand color styling
        **kwargs: Additional arguments passed to st.plotly_chart
    """
    if config is None:
        config = DEFAULT_PLOTLY_CONFIG.copy()
    
    # Apply brand styling if requested
    if apply_brand_colors:
        fig = apply_brand_styling(fig)
    
    # Ensure we always have the required config keys to avoid warnings
    final_config = DEFAULT_PLOTLY_CONFIG.copy()
    final_config.update(config)
    
    st.plotly_chart(fig, use_container_width=use_container_width, config=final_config, **kwargs)