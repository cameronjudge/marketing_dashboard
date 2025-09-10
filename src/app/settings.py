from __future__ import annotations

import streamlit as st


APP_TITLE: str = "Marketing Dashboard"
APP_ICON: str = "https://framerusercontent.com/images/u8LnenhR3qeY7enlkhKgmaatK40.jpg"
APP_LAYOUT: str = "wide"


def configure_page() -> None:
    """Apply Streamlit page configuration once per run."""
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout=APP_LAYOUT)


