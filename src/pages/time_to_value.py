import streamlit as st
import plotly.express as px
import pandas as pd
from src.db.redshift_connection import run_query, get_redshift_connection
from src.sql.sql import time_to_first_review_query

def time_to_value_page() -> None:
    st.title('Time To Value')

    tabs = st.tabs([
        'Finance',
        'Market',
        'Growth',
        'Upgrade',
        'Downgrade',
        'Churn',
        'Onboarding'
    ])

    with tabs[0]:
        st.subheader('Finance')
        st.info('Finance metrics coming soon.')

    with tabs[1]:
        st.subheader('Market')
        st.info('Market metrics coming soon.')

    with tabs[2]:
        st.subheader('Growth')
        st.info('Growth metrics coming soon.')

    with tabs[3]:
        st.subheader('Upgrade')
        st.info('Upgrade metrics coming soon.')

    with tabs[4]:
        st.subheader('Downgrade')
        st.info('Downgrade metrics coming soon.')

    with tabs[5]:
        st.subheader('Churn')
        st.info('Churn metrics coming soon.')

    with tabs[6]:
        st.subheader('Onboarding')

        # Fetch weekly metrics from Redshift
        df = run_query(time_to_first_review_query)

        if df.empty:
            st.info('No data available yet.')
        else:
            # Normalize and order
            if 'week' in df.columns:
                df['week'] = pd.to_datetime(df['week'])
            df = df.sort_values('week')

            # Latest values for mean and median
            metric_cols = ['avg_days_to_first_review', 'median_days_to_first_review']
            latest_row = df.dropna(subset=metric_cols).tail(1)

            if latest_row.empty:
                st.info('No metric values available yet.')
            else:
                latest = latest_row.iloc[0]
                prev_row = df.dropna(subset=metric_cols).iloc[:-1].tail(1)

                avg_val = round(float(latest['avg_days_to_first_review']), 2)
                median_val = round(float(latest['median_days_to_first_review']), 2)

                avg_delta = None
                median_delta = None
                if not prev_row.empty:
                    avg_delta = round(
                        float(latest['avg_days_to_first_review']) - float(prev_row.iloc[0]['avg_days_to_first_review']),
                        2
                    )
                    median_delta = round(
                        float(latest['median_days_to_first_review']) - float(prev_row.iloc[0]['median_days_to_first_review']),
                        2
                    )

                # Display metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label='Avg days to first review', value=avg_val, delta=avg_delta)
                with col2:
                    st.metric(label='Median days to first review', value=median_val, delta=median_delta)

                # Trend chart for mean and median
                fig = px.line(
                    df,
                    x='week',
                    y=['avg_days_to_first_review', 'median_days_to_first_review'],
                    title='Time to first review (weekly)',
                    labels={'value': 'Days', 'week': 'Week', 'variable': 'Metric'}
                )
                st.plotly_chart(fig, use_container_width=True)
                