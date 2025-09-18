import streamlit as st
import plotly.express as px
import pandas as pd
from src.db.redshift_connection import run_query, get_redshift_connection
from src.sql.downgrade.awesome_downgrade import awesome_downgrade_rate


def downgrade_page() -> None:
    st.title('Downgrade')

    st.subheader('Downgrades by source')
    df = run_query(awesome_downgrade_rate)
    if df.empty:
        st.info('No downgrade data available yet.')
        return

    df['week_start'] = pd.to_datetime(df['week_start'])
    df = df.sort_values('week_start')

    category_order = ['cancelled', 'free_trial', 'downgrade', 'other']
    if 'downgrade_path' in df.columns:
        df['downgrade_path'] = pd.Categorical(
            df['downgrade_path'], categories=category_order, ordered=True
        )

    # KPI metrics (exclude 'other') with WoW deltas
    kpi_order = ['cancelled', 'free_trial', 'downgrade']
    present_kpis = [k for k in kpi_order if k in df['downgrade_path'].astype(str).unique().tolist()]

    def latest_with_delta_downgrades(frame: pd.DataFrame, path: str):
        temp = frame[frame['downgrade_path'] == path][['week_start', 'count_of_downgrades']].dropna().copy()
        if temp.empty:
            return None, None
        temp = temp.sort_values('week_start')
        latest_val = temp.iloc[-1]['count_of_downgrades']
        if len(temp) < 2:
            return latest_val, None
        prev_val = temp.iloc[-2]['count_of_downgrades']
        try:
            delta_val = float(latest_val) - float(prev_val)
        except Exception:
            delta_val = None
        return latest_val, delta_val

    kpi_label_map = {
        'cancelled': 'Cancelled',
        'free_trial': 'Free trial',
        'downgrade': 'Downgrade',
    }
    if present_kpis:
        kpi_cols = st.columns(len(present_kpis))
        for idx, key in enumerate(present_kpis):
            latest, delta = latest_with_delta_downgrades(df, key)
            with kpi_cols[idx]:
                if latest is None or pd.isna(latest):
                    st.metric(label=kpi_label_map.get(key, key), value='—', delta=None)
                else:
                    st.metric(
                        label=kpi_label_map.get(key, key),
                        value=int(latest),
                        delta=(int(delta) if delta is not None and pd.notna(delta) else None),
                    )

    # Select filter for chart sources (does not affect KPIs)
    available_paths = [p for p in category_order if p in df['downgrade_path'].astype(str).unique().tolist()]
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_paths = st.multiselect(
            'Sources', options=available_paths, default=available_paths, key='downgrades_sources_select'
        )
    chart_df = df[df['downgrade_path'].astype(str).isin(selected_paths)] if selected_paths else df.iloc[0:0]
    if chart_df.empty:
        st.info('Select at least one source to display.')
        return

    fig = px.bar(
        chart_df,
        x='week_start',
        y='count_of_downgrades',
        color='downgrade_path',
        barmode='stack',
        category_orders={'downgrade_path': category_order},
        title='Weekly downgrades by source (completed weeks)'
    )
    fig.update_layout(xaxis_title='Week', yaxis_title='Downgrades')
    st.plotly_chart(fig, use_container_width=True)


