import streamlit as st

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

    pages = {
        "Home": [st.Page(home_page, title='Home', icon='🏠')],
        "About": [st.Page(about_page, title='About', icon='ℹ️')],
        "Dashboard": [
            finance_pg,
            market_pg,
            growth_pg,
            upgrade_pg,
            downgrade_pg,
            churn_pg,
            onboarding_pg,
            google_analytics_pg,
        ],
    }

    pg = st.navigation(pages, position="top")

    dashboard_pages = {
        finance_pg,
        market_pg,
        growth_pg,
        upgrade_pg,
        downgrade_pg,
        churn_pg,
        onboarding_pg,
        google_analytics_pg,
    }

    if pg in dashboard_pages:
        render_chrome()
    else:
        collapse_sidebar()

    pg.run()




if __name__ == "__main__":
    main()