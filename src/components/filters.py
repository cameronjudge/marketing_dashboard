from __future__ import annotations

import streamlit as st


def render_filters_sidebar() -> None:
    """Render common sidebar filters shared across pages.

    Keys ensure the widgets are stateful across pages.
    """
    st.title("Filters")
    st.selectbox("Segment", ["Placeholder", "Placeholder", "Placeholder", "Placeholder"], key="Placeholder")
    st.date_input("Start date", key="start_date")
    st.date_input("End date", key="end_date")


    #log out button
    if st.button("Log out"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.logout()


