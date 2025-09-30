import streamlit as st
import pandas as pd
import plotly.express as px

from src.db.redshift_connection import run_query
from src.sql.growth.net_growth import (
    gross_installs_wow,
    net_growth_installs_wow,
    net_growth_awesome_plan_wow,
)
from src.sql.upgrade.trial import trial_categories_categories
from src.sql.sql import time_to_first_review_query
from src.utils.chart_builder import build_sparkline_area, format_number, format_percent


def _latest_with_delta(df: pd.DataFrame, date_column: str, value_column: str) -> tuple[pd.Series | None, float | None]:
    if df is None or df.empty or value_column not in df.columns:
        return None, None
    temp = df.dropna(subset=[value_column]).copy()
    if temp.empty:
        return None, None
    if date_column in temp.columns:
        temp[date_column] = pd.to_datetime(temp[date_column])
        temp = temp.sort_values(date_column)
    if len(temp) == 1:
        return temp.iloc[-1][value_column], None
    latest_val = temp.iloc[-1][value_column]
    prev_val = temp.iloc[-2][value_column]
    try:
        delta_val = float(latest_val) - float(prev_val)
    except Exception:
        delta_val = None
    return latest_val, delta_val


def _sparkline(df: pd.DataFrame, x_col: str, y_col: str, title: str, height: int = 110):
    if df is None or df.empty or y_col not in df.columns:
        return None
    fig = px.area(df, x=x_col, y=y_col, title=title)
    fig.update_layout(
        showlegend=False,
        height=height,
        margin=dict(l=10, r=10, t=30, b=0),
        xaxis_title=None,
        yaxis_title=None,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def home_page() -> None:
    st.title('🏠 Home - INCORRECT DATA USED AS A PLACEHOLDER DISPLAY')


    # Queries
    try:
        df_net_overall = run_query(net_growth_installs_wow)
    except Exception:
        df_net_overall = pd.DataFrame()

    try:
        df_net_awesome = run_query(net_growth_awesome_plan_wow)
    except Exception:
        df_net_awesome = pd.DataFrame()

    try:
        df_installs = run_query(gross_installs_wow)
    except Exception:
        df_installs = pd.DataFrame()

    # Monthly activity for overall growth %
    monthly_activity_sql = """
        select monthly_date,
               total_active_installed_users,
               total_active_upgraded_users,
               monthly_install_growth_rate
        from dbt.agg__monthly_shop_activity_metrics
        order by monthly_date
        limit 12
    """
    try:
        df_monthly = run_query(monthly_activity_sql)
    except Exception:
        df_monthly = pd.DataFrame()
    if not df_monthly.empty and 'monthly_date' in df_monthly.columns:
        df_monthly['monthly_date'] = pd.to_datetime(df_monthly['monthly_date'])
        df_monthly = df_monthly.sort_values('monthly_date')
        df_monthly['overall_growth_pct'] = df_monthly.get('monthly_install_growth_rate')

    # Trial categories (sum to total weekly trials)
    try:
        df_trials = run_query(trial_categories_categories)
    except Exception:
        df_trials = pd.DataFrame()
    trial_cols = ['home_trials', 'upsell_trials', 'optin_trials', 'article_trials', 'welcome_trials', 'cs_trials']
    if not df_trials.empty:
        if 'week' in df_trials.columns:
            df_trials['week'] = pd.to_datetime(df_trials['week'])
            df_trials = df_trials.sort_values('week')
        existing = [c for c in trial_cols if c in df_trials.columns]
        if existing:
            df_trials['total_trials'] = df_trials[existing].sum(axis=1)

    # Time to first review (weekly)
    try:
        df_ttf = run_query(time_to_first_review_query)
    except Exception:
        df_ttf = pd.DataFrame()
    if not df_ttf.empty and 'week' in df_ttf.columns:
        df_ttf['week'] = pd.to_datetime(df_ttf['week'])
        df_ttf = df_ttf.sort_values('week')

    # Group: Growth
    st.markdown('### Growth')
    g1, g2, g3 = st.columns(3)
    with g1:
        val, delta = _latest_with_delta(df_net_overall, 'week_start', 'net_weekly_change')
        st.metric('Weekly net adds (overall)', format_number(val) if pd.notna(val) else '—', format_number(delta) if delta is not None and pd.notna(delta) else None)
        fig = build_sparkline_area(
            df_net_overall.sort_values('week_start').tail(12) if not df_net_overall.empty else df_net_overall,
            'week_start', 'net_weekly_change', ''
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with g2:
        val, delta = _latest_with_delta(df_net_awesome, 'week_start', 'net_weekly_change')
        st.metric('Weekly net adds (Awesome)', format_number(val) if pd.notna(val) else '—', format_number(delta) if delta is not None and pd.notna(delta) else None)
        fig = build_sparkline_area(
            df_net_awesome.sort_values('week_start').tail(12) if not df_net_awesome.empty else df_net_awesome,
            'week_start', 'net_weekly_change', ''
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with g3:
        val, delta = _latest_with_delta(df_monthly, 'monthly_date', 'overall_growth_pct')
        if val is not None and pd.notna(val):
            st.metric('Monthly growth % (overall)', format_percent(val), format_percent(delta) if delta is not None and pd.notna(delta) else None)
        else:
            st.metric('Monthly growth % (overall)', '—', None)
        fig = build_sparkline_area(
            df_monthly.tail(12) if not df_monthly.empty else df_monthly,
            'monthly_date', 'overall_growth_pct', ''
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # Group: Acquisition
    st.markdown('### Acquisition')
    a1, a2, _ = st.columns(3)
    with a1:
        val, delta = _latest_with_delta(df_installs, 'week_start', 'gross_installs')
        st.metric('Weekly gross installs', format_number(val) if pd.notna(val) else '—', format_number(delta) if delta is not None and pd.notna(delta) else None)
        fig = build_sparkline_area(
            df_installs.sort_values('week_start').tail(12) if not df_installs.empty else df_installs,
            'week_start', 'gross_installs', ''
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with a2:
        val, delta = _latest_with_delta(df_trials, 'week', 'total_trials') if not df_trials.empty and 'total_trials' in df_trials.columns else (None, None)
        st.metric('Weekly trial starts (total)', format_number(val) if val is not None and pd.notna(val) else '—', format_number(delta) if delta is not None and pd.notna(delta) else None)
        fig = build_sparkline_area(
            df_trials.sort_values('week').tail(12) if not df_trials.empty else df_trials,
            'week', 'total_trials', ''
        ) if not df_trials.empty and 'total_trials' in df_trials.columns else None
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # Group: Onboarding
    st.markdown('### Onboarding')
    o1, _, _ = st.columns(3)
    with o1:
        val, delta = _latest_with_delta(df_ttf, 'week', 'avg_days_to_first_review')
        if val is not None and pd.notna(val):
            st.metric('Avg days to first review', format_number(val), format_number(delta) if delta is not None and pd.notna(delta) else None, delta_color='inverse')
        else:
            st.metric('Avg days to first review', '—', None, delta_color='inverse')
        fig = build_sparkline_area(
            df_ttf.tail(12) if not df_ttf.empty else df_ttf,
            'week', 'avg_days_to_first_review', ''
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
