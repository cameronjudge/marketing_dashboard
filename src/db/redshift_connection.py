import sys
from pathlib import Path
import streamlit as st
import psycopg2
import pandas as pd

# streamlit cache connection to redshift
@st.cache_resource
def get_redshift_connection():
    return psycopg2.connect(
        host=st.secrets["host"],
        port=st.secrets["port"],
        database=st.secrets["database"],
        user=st.secrets["user"],
        password=st.secrets["password"]
    )

# cache data from running query
@st.cache_data
def run_query(query):
    with get_redshift_connection() as conn:
        return pd.read_sql_query(query, conn)



