import sys
from pathlib import Path
import streamlit as st
import psycopg2
import pandas as pd

# Cache connection parameters instead of connection object
@st.cache_resource
def get_redshift_params():
    return {
        "host": st.secrets["host"],
        "port": st.secrets["port"],
        "database": st.secrets["database"],
        "user": st.secrets["user"],
        "password": st.secrets["password"]
    }

# Create fresh connection each time
def get_redshift_connection():
    params = get_redshift_params()
    return psycopg2.connect(**params)

# cache data from running query
@st.cache_data
def run_query(query):
    with get_redshift_connection() as conn:
        return pd.read_sql_query(query, conn)
        