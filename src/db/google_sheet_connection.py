import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


@st.cache_resource(ttl='1h')
def google_sheet_connection() -> GSheetsConnection:
    """
    Create a Google Sheets connection
    """
    return st.connection("gcp_service_account", type=GSheetsConnection)


@st.cache_data(ttl='1h')
def load_google_sheet_data(worksheet: str, spreadsheet: str) -> pd.DataFrame:
    """
    Load the growth target from the Google Sheets
    """
    conn = google_sheet_connection()
    return conn.read(
        worksheet="awesome_growth_target",
        spreadsheet="https://docs.google.com/spreadsheets/d/1kqZeAgZbvVekAkLXwzZKOPic78mbBdFpU7Dg-oN0gJg",
    )
