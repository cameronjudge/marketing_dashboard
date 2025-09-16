import streamlit as st
import pandas as pd 
from google.oauth2 import service_account
from google.cloud import bigquery

@st.cache_resource(ttl="1h")
def get_bigquery_client():
    """
    Create a bigquery client
    """
    info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/bigquery"],
    )
    return bigquery.Client(credentials=credentials, project=info["project_id"])


@st.cache_data(ttl="1h")
def run_query(query):
    """
    Run a bigquery query
    """
    client = get_bigquery_client()
    return client.query(query).to_dataframe()



if __name__ == "__main__":
    example_query = 'SELECT * FROM `review-site-307404.analytics_476622290.events_*` LIMIT 100'
    df = run_query(example_query)
    print(df)
    