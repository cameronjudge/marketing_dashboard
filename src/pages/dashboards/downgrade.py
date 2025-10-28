import streamlit as st
import plotly.express as px
import pandas as pd
from src.db.redshift_connection import run_query, get_redshift_connection
from src.sql.core_metrics.core_metrics import core_metrics


def downgrade_page() -> None:
    st.title('Downgrade')

    # Get core metrics data
    df = run_query(core_metrics)
    
    if df.empty:
        st.info('No data available yet.')
        return
    
    # Convert week to datetime and sort
    df['week'] = pd.to_datetime(df['week'])
    df = df.sort_values('week')

    # Header row: title + inline source selector
    header_left, header_right = st.columns([3, 2])
    with header_left:
        st.subheader('Downgrades by source')
    
    # Transform core metrics data for downgrade visualization
    # Since core_metrics only has total downgrades, we'll create a simple structure
    df_down = df[['week', 'core_downgrades']].copy()
    df_down['week_start'] = df_down['week']
    df_down['downgrade_path'] = 'downgrade'
    df_down['count_of_downgrades'] = df_down['core_downgrades']

    # Consistent ordering and colors
    category_order = ['downgrade']
    color_map = {
        'downgrade': '#f59db1',
    }
    df_down['downgrade_path'] = pd.Categorical(
        df_down['downgrade_path'], categories=category_order, ordered=True
    )

    # KPI metrics with WoW deltas using original df columns
    def latest_with_delta_direct(df_orig: pd.DataFrame, col: str):
        temp = df_orig[['week', col]].dropna().copy()
        if temp.empty:
            return None, None
        temp = temp.sort_values('week')
        latest_val = temp.iloc[-1][col]
        if len(temp) < 2:
            return latest_val, None
        prev_val = temp.iloc[-2][col]
        try:
            delta_val = float(latest_val) - float(prev_val)
        except Exception:
            delta_val = None
        return latest_val, delta_val

    kpi_label_map = {
        'total': 'Total Downgrades',
    }
    
    # Get downgrade metrics
    total_latest, total_delta = latest_with_delta_direct(df, 'core_downgrades')
    
    kpi_cols = st.columns(1)
    kpis = [
        ('total', total_latest, total_delta),
    ]
    
    for col, (key, val, delta) in zip(kpi_cols, kpis):
        with col:
            if val is None or pd.isna(val):
                st.metric(label=kpi_label_map.get(key, key), value='—', delta=None, delta_color='inverse')
            else:
                st.metric(
                    label=kpi_label_map.get(key, key),
                    value=f"{int(val):,}",
                    delta=(int(delta) if delta is not None and pd.notna(delta) else None),
                    delta_color='inverse'
                )

    # Select filter for chart sources (does not affect KPIs)
    available_paths = category_order
    with header_right:
        selected_paths = st.multiselect(
            ' ', options=available_paths, default=available_paths,
            key='downgrades_sources_select', label_visibility='collapsed'
        )
    chart_df = df_down[df_down['downgrade_path'].astype(str).isin(selected_paths)] if selected_paths else df_down.iloc[0:0]
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
        color_discrete_map=color_map,
    )
    fig.update_layout(
        height=340,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
        bargap=0.15,
        xaxis_title='Week',
        yaxis_title='Downgrades',
        yaxis=dict(tickformat=','),
        margin=dict(t=10)
    )
    st.plotly_chart(fig, width='stretch')


