import streamlit as st
import pandas as pd
import plotly.express as px

from src.db.redshift_connection import run_query
from src.sql.growth.net_growth import (
    gross_installs_wow,
    net_growth_installs_wow,
    net_growth_awesome_plan_wow,
)


def _format_week(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if column in df.columns:
        df[column] = pd.to_datetime(df[column])
        df = df.sort_values(column)
    return df


def _latest_with_delta(
    df: pd.DataFrame,
    date_column: str,
    value_column: str
) -> tuple[pd.Series | None, float | None]:
    if df is None or df.empty or value_column not in df.columns:
        return None, None
    temp = df.dropna(subset=[value_column]).copy()
    if temp.empty:
        return None, None
    if date_column in temp.columns:
        temp[date_column] = pd.to_datetime(temp[date_column])
        temp = temp.sort_values(date_column)
    if len(temp) == 1:
        latest_val = temp.iloc[-1][value_column]
        return latest_val, None
    latest_val = temp.iloc[-1][value_column]
    prev_val = temp.iloc[-2][value_column]
    try:
        delta_val = float(latest_val) - float(prev_val)
    except Exception:
        delta_val = None
    return latest_val, delta_val


def growth_page() -> None:
    st.title('Growth')

    # Prepare monthly SQL (limited to 12 months) and preload data for KPIs and charts
    monthly_activity_sql = """
        select monthly_date,
               total_active_installed_users,
               total_active_upgraded_users,
               monthly_install_growth_rate,
               monthly_upgrade_growth_rate
        from dbt.agg__monthly_shop_activity_metrics
        order by monthly_date desc
        limit 12
    """

    try:
        df_net_overall = run_query(net_growth_installs_wow)
    except Exception:
        df_net_overall = pd.DataFrame()

    try:
        df_net_awesome = run_query(net_growth_awesome_plan_wow)
    except Exception:
        df_net_awesome = pd.DataFrame()

    try:
        df_monthly = run_query(monthly_activity_sql)
    except Exception:
        df_monthly = pd.DataFrame()

    try:
        df_installs = run_query(gross_installs_wow)
    except Exception:
        df_installs = pd.DataFrame()

    # Derive monthly overall growth % for KPI
    if not df_monthly.empty and 'monthly_install_growth_rate' in df_monthly.columns:
        df_monthly['overall_growth_pct'] = df_monthly['monthly_install_growth_rate']

    # Key metrics (with deltas)
    st.subheader('Key metrics')

    net_overall_val, net_overall_delta = _latest_with_delta(
        df_net_overall, 'week_start', 'net_weekly_change'
    )
    net_awesome_val, net_awesome_delta = _latest_with_delta(
        df_net_awesome, 'week_start', 'net_weekly_change'
    )
    installs_val, installs_delta = _latest_with_delta(
        df_installs, 'week_start', 'gross_installs'
    )
    monthly_growth_val, monthly_growth_delta = _latest_with_delta(
        df_monthly, 'monthly_date', 'overall_growth_pct'
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            label='Weekly net adds (overall)',
            value=int(net_overall_val) if pd.notna(net_overall_val) else '—',
            delta=(
                int(net_overall_delta) if net_overall_delta is not None and pd.notna(net_overall_delta) else None
            ),
        )
    with k2:
        st.metric(
            label='Weekly net adds (Awesome)',
            value=int(net_awesome_val) if pd.notna(net_awesome_val) else '—',
            delta=(
                int(net_awesome_delta) if net_awesome_delta is not None and pd.notna(net_awesome_delta) else None
            ),
        )
    with k3:
        st.metric(
            label='Weekly gross installs',
            value=int(installs_val) if pd.notna(installs_val) else '—',
            delta=(
                int(installs_delta) if installs_delta is not None and pd.notna(installs_delta) else None
            ),
        )
    with k4:
        if monthly_growth_val is not None and pd.notna(monthly_growth_val):
            mgv = float(monthly_growth_val)
            mgd = (
                float(monthly_growth_delta) if monthly_growth_delta is not None and pd.notna(monthly_growth_delta) else None
            )
            st.metric(
                label='Monthly growth % (overall)',
                value=f"{mgv:.2f}%",
                delta=(f"{mgd:.2f}%" if mgd is not None else None),
            )
        else:
            st.metric(label='Monthly growth % (overall)', value='—', delta=None)

    # Net growth WoW — Overall (data preloaded above)

    if df_net_overall.empty:
        st.info('No weekly net growth (overall) data available.')
    else:
        df_net_overall = _format_week(df_net_overall, 'week_start')
        st.subheader('Net growth WoW — Overall')
        fig = px.line(
            df_net_overall,
            x='week_start',
            y='net_weekly_change',
            markers=True,
            title='Weekly net adds (overall)'
        )
        fig.update_layout(xaxis_title='Week', yaxis_title='Net adds')
        st.plotly_chart(fig, use_container_width=True)

    # Net growth WoW — Awesome (data preloaded above)

    if df_net_awesome.empty:
        st.info('No weekly net growth (Awesome) data available.')
    else:
        df_net_awesome = _format_week(df_net_awesome, 'week_start')
        st.subheader('Net growth WoW — Awesome')
        fig = px.line(
            df_net_awesome,
            x='week_start',
            y='net_weekly_change',
            markers=True,
            title='Weekly net adds (Awesome)'
        )
        fig.update_layout(xaxis_title='Week', yaxis_title='Net adds')
        st.plotly_chart(fig, use_container_width=True)

    # Net growth MoM (%) — Free vs Awesome, with overall (data preloaded above)

    if df_monthly.empty:
        st.info('No monthly growth data available.')
    else:
        if 'monthly_date' in df_monthly.columns:
            df_monthly['monthly_date'] = pd.to_datetime(df_monthly['monthly_date'])
            df_monthly = df_monthly.sort_values('monthly_date')
            df_monthly = df_monthly.tail(12)

        # Derive Free vs Awesome series and growth %
        df_monthly['free_active_users'] = (
            df_monthly['total_active_installed_users'] - df_monthly['total_active_upgraded_users']
        )

        # Compute percentage change for Free and Awesome
        df_monthly['free_growth_pct'] = df_monthly['free_active_users'].pct_change() * 100.0
        df_monthly['awesome_growth_pct'] = df_monthly['total_active_upgraded_users'].pct_change() * 100.0

        # Overall combined: use install growth rate already computed in the model
        df_monthly['overall_growth_pct'] = df_monthly['monthly_install_growth_rate']

        st.subheader('Net growth MoM (%) — Free vs Awesome, with overall')

        # Grouped bars for Free + Awesome
        df_bar = df_monthly[['monthly_date', 'free_growth_pct', 'awesome_growth_pct']].melt(
            id_vars='monthly_date',
            var_name='segment',
            value_name='growth_pct'
        )
        df_bar['segment'] = df_bar['segment'].map({
            'free_growth_pct': 'Free',
            'awesome_growth_pct': 'Awesome'
        })

        fig_bar = px.bar(
            df_bar,
            x='monthly_date',
            y='growth_pct',
            color='segment',
            barmode='group',
            title='Monthly growth % (Free vs Awesome)'
        )
        fig_bar.update_layout(xaxis_title='Month', yaxis_title='Growth %')

        # Overlay overall line
        fig_bar.add_scatter(
            x=df_monthly['monthly_date'],
            y=df_monthly['overall_growth_pct'],
            mode='lines+markers',
            name='Overall'
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    # New installs WoW (gross), grouped by source if available (data preloaded above)

    if df_installs.empty:
        st.info('No weekly gross installs data available.')
    else:
        df_installs = _format_week(df_installs, 'week_start')
        st.subheader('New installs WoW (gross) — by source')

        if 'source' in df_installs.columns:
            # Expect columns: week_start, source, gross_installs
            df_grouped = df_installs.copy()
            fig = px.bar(
                df_grouped,
                x='week_start',
                y='gross_installs',
                color='source',
                barmode='group',
                title='Weekly new installs by source'
            )
            fig.update_layout(xaxis_title='Week', yaxis_title='Installs')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info('Source breakdown not available in current query; showing totals only.')
            fig = px.bar(
                df_installs,
                x='week_start',
                y='gross_installs',
                title='Weekly new installs (total)'
            )
            fig.update_layout(xaxis_title='Week', yaxis_title='Installs')
            st.plotly_chart(fig, use_container_width=True)

    # New Awesome WoW users by source — requires route/source breakdown
    st.subheader('New Awesome WoW users by source')
    st.info('Stacked source breakdown (direct vs Free→trial→Awesome vs reopened) to be added when source fields are available. For now, see the Awesome net growth chart above.')


