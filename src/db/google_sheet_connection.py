import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

@st.cache_data(ttl=600)
def load_growth_target():
    conn = st.connection("gcp_service_account", type=GSheetsConnection)
    return conn.read(
        worksheet="awesome_growth_target",
        spreadsheet="https://docs.google.com/spreadsheets/d/1kqZeAgZbvVekAkLXwzZKOPic78mbBdFpU7Dg-oN0gJg",
    )
