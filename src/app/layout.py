from __future__ import annotations

import streamlit as st

from src.components.filters import render_filters_sidebar


def render_chrome() -> None:
    """Render common chrome elements used across all pages."""
    with st.sidebar:
        render_filters_sidebar()


def collapse_sidebar() -> None:
    """Visually collapse the sidebar for pages that shouldn't display it.

    Uses CSS to hide the sidebar area so the main content spans full width.
    """
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        /* Hide the floating collapse/expand control to avoid confusion */
        [data-testid="stSidebarCollapsedControl"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


