import streamlit as st
import warnings
import os
import sys
from typing import Any, Dict, Optional
import plotly.graph_objects as go
import plotly.io as pio

# NUCLEAR WARNING SUPPRESSION - Must be done FIRST before any other imports
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

# Completely disable warnings at the system level
def null_warn(*args, **kwargs):
    """Completely suppress all warnings"""
    pass

# Replace warnings.warn with a no-op function
warnings.warn = null_warn
warnings.warn_explicit = null_warn

# Also override the showwarning function
def null_showwarning(*args, **kwargs):
    """Completely suppress warning display"""
    pass

warnings.showwarning = null_showwarning

# Additional warning suppression (redundant but ensures coverage)
try:
    warnings.filterwarnings("ignore")
    warnings.simplefilter("ignore")
except:
    pass

# Suppress at the logging level
import logging
try:
    # Set all loggers to CRITICAL to suppress warnings
    logging.getLogger().setLevel(logging.CRITICAL)
    logging.getLogger("streamlit").setLevel(logging.CRITICAL)
    logging.getLogger("plotly").setLevel(logging.CRITICAL)
    logging.getLogger("pandas").setLevel(logging.CRITICAL)
    logging.getLogger("google").setLevel(logging.CRITICAL)
    
    # Disable all logging handlers
    logging.disable(logging.CRITICAL)
except Exception:
    pass

# Set environment variables to suppress warnings
os.environ['PLOTLY_SUPPRESS_WARNINGS'] = '1'
os.environ['STREAMLIT_SUPPRESS_WARNINGS'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['STREAMLIT_LOGGER_LEVEL'] = 'error'

# Try to suppress Streamlit's internal warning system
try:
    import streamlit.logger
    streamlit.logger.get_logger().setLevel(logging.CRITICAL)
except:
    pass

# Skip Plotly template configuration to avoid errors
# Templates can cause compatibility issues, so we'll let Plotly use its defaults
import plotly.express as px
try:
    # Only set safe defaults that don't cause template errors
    px.defaults.width = None
    px.defaults.height = None
except Exception:
    # If defaults setting fails, just continue
    pass

# Global Plotly configuration
SAFE_PLOTLY_CONFIG = {
    'displayModeBar': 'hover',
    'displaylogo': False,
    'staticPlot': False,
    'responsive': True,
    'showTips': True,
    'showAxisDragHandles': True,
    'showAxisRangeEntryBoxes': True,
    'doubleClick': 'reset',
    'scrollZoom': False,
    'modeBarButtonsToRemove': ['lasso2d', 'select2d']
}

# Monkey patch st.plotly_chart to completely suppress warnings
_original_plotly_chart = st.plotly_chart

def safe_plotly_chart(figure_or_data, use_container_width=True, config=None, **kwargs):
    """Safe wrapper for st.plotly_chart that prevents ALL warnings"""
    # Use safe config
    final_config = SAFE_PLOTLY_CONFIG.copy()
    if config:
        final_config.update(config)
    
    # Completely suppress ALL warnings and errors during chart rendering
    old_warn = warnings.warn
    old_showwarning = warnings.showwarning
    
    try:
        # Disable all warnings temporarily
        warnings.warn = lambda *args, **kwargs: None
        warnings.showwarning = lambda *args, **kwargs: None
        warnings.simplefilter("ignore")
        
        # Call the original function with new parameter structure
        return _original_plotly_chart(figure_or_data, use_container_width=use_container_width, config=final_config, **kwargs)
    except Exception as e:
        # If there's any error, try without config
        try:
            return _original_plotly_chart(figure_or_data, use_container_width=use_container_width, **kwargs)
        except:
            # Last resort - return None to prevent crashes
            return None
    finally:
        # Restore warning functions (though we keep them disabled)
        warnings.warn = null_warn
        warnings.showwarning = null_showwarning

# Replace the original function
st.plotly_chart = safe_plotly_chart

from src.app.settings import configure_page
from src.app.layout import render_chrome, collapse_sidebar
from src.pages.home import home_page
from src.pages.about import about_page
from src.pages.dashboards.finance import finance_page
from src.pages.dashboards.market import market_page
from src.pages.dashboards.growth import growth_page
from src.pages.dashboards.upgrade import upgrade_page
from src.pages.dashboards.downgrade import downgrade_page
from src.pages.dashboards.churn import churn_page
from src.pages.dashboards.onboarding import onboarding_page
from src.pages.dashboards.google_analytics import google_analytics_page
from src.pages.dashboards.general_metrics import general_metrics_page
from src.pages.dashboards.integrations import integrations_page
from src.auth.login import user_login


with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

 

def main() -> None:
    configure_page()


    if not user_login():
        # Not authenticated: don't render navigation or any content.
        return

    # Dashboard subpages
    finance_pg = st.Page(finance_page, title='Finance', icon='💰')
    market_pg = st.Page(market_page, title='Market', icon='🌐')
    growth_pg = st.Page(growth_page, title='Growth', icon='📈')
    upgrade_pg = st.Page(upgrade_page, title='Upgrade', icon='⬆️')
    downgrade_pg = st.Page(downgrade_page, title='Downgrade', icon='⬇️')
    churn_pg = st.Page(churn_page, title='Churn', icon='🧹')
    onboarding_pg = st.Page(onboarding_page, title='Onboarding', icon='🚀')
    google_analytics_pg = st.Page(google_analytics_page, title='Listing Analytics', icon='🟢')
    general_metrics_pg = st.Page(general_metrics_page, title='General Metrics', icon='🎯')
    integrations_pg = st.Page(integrations_page, title='Integrations & Partnerships', icon='🔌')

    pages = {
        "Home": [st.Page(home_page, title='Home', icon='🏠')],
        "About": [st.Page(about_page, title='About', icon='ℹ️')],
        "Dashboard": [
            general_metrics_pg,
            finance_pg,
            market_pg,
            growth_pg,
            upgrade_pg,
            downgrade_pg,
            churn_pg,
            onboarding_pg,
            google_analytics_pg,
            integrations_pg,
        ],
    }

    pg = st.navigation(pages, position="top")

    dashboard_pages = {
        general_metrics_pg,
        finance_pg,
        market_pg,
        growth_pg,
        upgrade_pg,
        downgrade_pg,
        churn_pg,
        onboarding_pg,
        google_analytics_pg,
        integrations_pg,
    }

    if pg in dashboard_pages:
        render_chrome()
    else:
        collapse_sidebar()

    pg.run()




if __name__ == "__main__":
    main()