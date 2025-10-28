import streamlit as st
import warnings
import os
from typing import Any, Dict, Optional
import plotly.graph_objects as go
import plotly.io as pio

# Suppress Plotly deprecation warnings
warnings.filterwarnings("ignore", message=".*keyword arguments have been deprecated.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="plotly")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="streamlit")
warnings.filterwarnings("ignore", category=UserWarning, module="plotly")

# Set environment variable to suppress Plotly warnings
os.environ['PLOTLY_SUPPRESS_WARNINGS'] = '1'

# Set global Plotly configuration
pio.templates.default = "plotly_white"
pio.renderers.default = "browser"

# Configure Plotly to avoid deprecation warnings
import plotly.express as px
px.defaults.template = "plotly_white"
px.defaults.width = None
px.defaults.height = None

# Global Plotly configuration
SAFE_PLOTLY_CONFIG = {
    'displayModeBar': False,
    'displaylogo': False,
    'staticPlot': False,
    'responsive': True,
    'showTips': False,
    'showAxisDragHandles': False,
    'showAxisRangeEntryBoxes': False,
    'doubleClick': 'reset',
    'scrollZoom': False
}

# Monkey patch st.plotly_chart to always use safe config
_original_plotly_chart = st.plotly_chart

def safe_plotly_chart(figure_or_data, width='stretch', config=None, **kwargs):
    """Safe wrapper for st.plotly_chart that prevents deprecation warnings"""
    # Always use our safe config, ignoring any passed config to avoid conflicts
    final_config = SAFE_PLOTLY_CONFIG.copy()
    
    # Remove any config from kwargs to prevent conflicts
    kwargs.pop('config', None)
    
    return _original_plotly_chart(figure_or_data, width=width, config=final_config, **kwargs)

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