import streamlit as st
import pandas as pd
import plotly.express as px

from src.db.redshift_connection import run_query
from src.sql.core_metrics.core_metrics import core_metrics
from src.sql.core_metrics.monthly_core_metrics import monthly_core_metrics
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
    st.title('🏠 Home Dashboard')

    # Get core metrics data (weekly)
    try:
        df_core = run_query(core_metrics)
    except Exception:
        df_core = pd.DataFrame()
    
    if not df_core.empty:
        df_core['week'] = pd.to_datetime(df_core['week'])
        df_core = df_core.sort_values('week')
        
        # Calculate total trials from core metrics
        trial_cols = ['home_trials', 'upsell_trials', 'optin_trials', 'article_trials', 'welcome_trials']
        existing_trial_cols = [c for c in trial_cols if c in df_core.columns]
        if existing_trial_cols:
            df_core['total_trials'] = df_core[existing_trial_cols].sum(axis=1)

    # Get monthly metrics data
    try:
        df_monthly = run_query(monthly_core_metrics)
    except Exception:
        df_monthly = pd.DataFrame()
    
    if not df_monthly.empty:
        df_monthly['month'] = pd.to_datetime(df_monthly['month'])
        df_monthly = df_monthly.sort_values('month')

    # Group: Growth
    st.markdown('### Growth')
    g1, g2, g3 = st.columns(3)
    with g1:
        # Weekly net installs from core metrics
        val, delta = _latest_with_delta(df_core, 'week', 'net_installs') if not df_core.empty else (None, None)
        st.metric('Weekly net installs', format_number(val) if val is not None and pd.notna(val) else '—', format_number(delta) if delta is not None and pd.notna(delta) else None)
        fig = build_sparkline_area(
            df_core.tail(12) if not df_core.empty else df_core,
            'week', 'net_installs', ''
        ) if not df_core.empty else None
        if fig:
            st.plotly_chart(fig, width='stretch')
    with g2:
        # Weekly net upgrades from core metrics
        val, delta = _latest_with_delta(df_core, 'week', 'core_net_upgrades') if not df_core.empty else (None, None)
        st.metric('Weekly net upgrades', format_number(val) if val is not None and pd.notna(val) else '—', format_number(delta) if delta is not None and pd.notna(delta) else None)
        fig = build_sparkline_area(
            df_core.tail(12) if not df_core.empty else df_core,
            'week', 'core_net_upgrades', ''
        ) if not df_core.empty else None
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with g3:
        # Monthly total growth rate from monthly metrics
        val, delta = _latest_with_delta(df_monthly, 'month', 'total_growth_rate_pct') if not df_monthly.empty else (None, None)
        if val is not None and pd.notna(val):
            st.metric('Monthly growth %', format_percent(val), format_percent(delta) if delta is not None and pd.notna(delta) else None)
        else:
            st.metric('Monthly growth %', '—', None)
        fig = build_sparkline_area(
            df_monthly.tail(12) if not df_monthly.empty else df_monthly,
            'month', 'total_growth_rate_pct', ''
        ) if not df_monthly.empty else None
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # Group: Acquisition
    st.markdown('### Acquisition')
    a1, a2, a3 = st.columns(3)
    with a1:
        # Weekly upgrades from core metrics
        val, delta = _latest_with_delta(df_core, 'week', 'core_upgrades') if not df_core.empty else (None, None)
        st.metric('Weekly upgrades', format_number(val) if val is not None and pd.notna(val) else '—', format_number(delta) if delta is not None and pd.notna(delta) else None)
        fig = build_sparkline_area(
            df_core.tail(12) if not df_core.empty else df_core,
            'week', 'core_upgrades', ''
        ) if not df_core.empty else None
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with a2:
        # Weekly trial starts from core metrics
        val, delta = _latest_with_delta(df_core, 'week', 'total_trials') if not df_core.empty and 'total_trials' in df_core.columns else (None, None)
        st.metric('Weekly trial starts', format_number(val) if val is not None and pd.notna(val) else '—', format_number(delta) if delta is not None and pd.notna(delta) else None)
        fig = build_sparkline_area(
            df_core.tail(12) if not df_core.empty else df_core,
            'week', 'total_trials', ''
        ) if not df_core.empty and 'total_trials' in df_core.columns else None
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with a3:
        # Trial conversions from core metrics
        val, delta = _latest_with_delta(df_core, 'week', 'trial_conversions') if not df_core.empty else (None, None)
        st.metric('Weekly trial conversions', format_number(val) if val is not None and pd.notna(val) else '—', format_number(delta) if delta is not None and pd.notna(delta) else None)
        fig = build_sparkline_area(
            df_core.tail(12) if not df_core.empty else df_core,
            'week', 'trial_conversions', ''
        ) if not df_core.empty else None
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            