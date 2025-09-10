from __future__ import annotations

import streamlit as st


def render_filters_sidebar() -> None:
    """Render common sidebar filters shared across pages.

    Keys ensure the widgets are stateful across pages.
    """
    st.title("Filters")
    st.selectbox("Segment", ["All", "SMB", "Mid-Market", "Enterprise"], key="segment")
    st.date_input("Start date", key="start_date")
    st.date_input("End date", key="end_date")


    #log out button
    if st.button("Log out"):
        st.logout()


