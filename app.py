import streamlit as st

from src.app.settings import configure_page
from src.app.layout import render_chrome, collapse_sidebar
from src.pages.home import home_page
from src.pages.about import about_page
from src.pages.time_to_value import time_to_value_page
from src.auth.login import user_login


with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main() -> None:
    configure_page()


    if not user_login():
        # Not authenticated: don't render navigation or any content.
        return

    dashboard_page = st.Page(time_to_value_page, title='Dashboard', icon='📊')
    pages = [
        st.Page(home_page, title='Home', icon='🏠'),
        dashboard_page,
        st.Page(about_page, title='About', icon='ℹ️')
    ]

    pg = st.navigation(pages, position="top")

    if pg is dashboard_page:
        render_chrome()
    else:
        collapse_sidebar()

    pg.run()




if __name__ == "__main__":
    main()