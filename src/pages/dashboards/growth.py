import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.db.redshift_connection import run_query
from src.sql.core_metrics.core_metrics import core_metrics
from src.sql.core_metrics.monthly_core_metrics import monthly_core_metrics


def growth_page() -> None:
    st.title('Growth')
    
    # Get core metrics data
    df = run_query(core_metrics)
    
    if df.empty:
        st.info('No data available yet.')
        return
    
    # Convert week to datetime and sort
    df['week'] = pd.to_datetime(df['week'])
    df = df.sort_values('week')
    
    # Helper function for latest value with WoW delta
    def latest_with_delta(df_orig: pd.DataFrame, col: str):
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
    
    # Net Growth WoW — Overall (New – Lost) users this week (all users)
    st.subheader('Net Growth WoW — Overall')
    st.caption('(New – Lost) users this week (all users)')
    
    # KPI for net installs
    net_installs_latest, net_installs_delta = latest_with_delta(df, 'net_installs')
    
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    with kpi_col1:
        if net_installs_latest is None or pd.isna(net_installs_latest):
            st.metric(label='Net Installs', value='—', delta=None)
        else:
            st.metric(
                label='Net Installs',
                value=f"{int(net_installs_latest):,}",
                delta=(int(net_installs_delta) if net_installs_delta is not None and pd.notna(net_installs_delta) else None)
            )
    
    # Create line chart for net installs trend
    fig_overall = px.line(
        df,
        x='week',
        y='net_installs',
        markers=True
    )
    
    # Add data labels on points
    fig_overall.update_traces(
        textposition='top center',
        texttemplate='%{y:,.0f}',
        mode='lines+markers+text'
    )
    
    # Add horizontal line at y=0 for reference
    fig_overall.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Apply styling
    fig_overall.update_layout(
        height=340,
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=0),
        xaxis_title='Week',
        yaxis_title='Net Installs',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(tickformat=',')
    )
    
    fig_overall.update_xaxes(showgrid=False)
    fig_overall.update_yaxes(showgrid=False)
    
    st.plotly_chart(fig_overall, width='stretch', config={'displayModeBar': False})
    
    # Net Growth WoW — Awesome (New – Lost) users this week (paid users only)
    st.subheader('Net Growth WoW — Awesome')
    st.caption('(New – Lost) users this week (paid users only)')
    
    # KPI for net upgrades (awesome users)
    net_upgrades_latest, net_upgrades_delta = latest_with_delta(df, 'core_net_upgrades')
    upgrades_latest, upgrades_delta = latest_with_delta(df, 'core_upgrades')
    downgrades_latest, downgrades_delta = latest_with_delta(df, 'core_downgrades')
    
    # Display net awesome KPIs
    awesome_kpi_cols = st.columns(3)
    awesome_kpis = [
        ('Net Awesome', net_upgrades_latest, net_upgrades_delta),
        ('New Awesome', upgrades_latest, upgrades_delta),
        ('Lost Awesome', downgrades_latest, downgrades_delta),
    ]
    
    for col, (label, val, delta) in zip(awesome_kpi_cols, awesome_kpis):
        with col:
            if val is None or pd.isna(val):
                st.metric(label=label, value='—', delta=None)
            else:
                delta_color = 'inverse' if label == 'Lost Awesome' else 'normal'
                st.metric(
                    label=label,
                    value=f"{int(val):,}",
                    delta=(int(delta) if delta is not None and pd.notna(delta) else None),
                    delta_color=delta_color
                )
    
    # Create line chart for net awesome trend
    fig_awesome = px.line(
        df,
        x='week',
        y='core_net_upgrades',
        markers=True
    )
    
    # Add data labels on points
    fig_awesome.update_traces(
        textposition='top center',
        texttemplate='%{y:,.0f}',
        mode='lines+markers+text'
    )
    
    # Add horizontal line at y=0 for reference
    fig_awesome.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Apply styling
    fig_awesome.update_layout(
        height=340,
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=0),
        xaxis_title='Week',
        yaxis_title='Net Awesome Users',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(tickformat=',')
    )
    
    fig_awesome.update_xaxes(showgrid=False)
    fig_awesome.update_yaxes(showgrid=False)
    
    st.plotly_chart(fig_awesome, width='stretch', config={'displayModeBar': False})
    
    # Monthly Growth Rate — Free vs Awesome
    st.subheader('Monthly Growth Rate — Free vs Awesome')
    st.caption('(This month\'s users – Last month\'s users) ÷ Last month\'s users')
    
    # Get monthly metrics data
    monthly_df = run_query(monthly_core_metrics)
    
    if monthly_df.empty:
        st.info('No monthly data available yet.')
        return
    
    # Convert month to datetime and sort
    monthly_df['month_date'] = pd.to_datetime(monthly_df['month'] + '-01')
    monthly_df = monthly_df.sort_values('month_date')
    
    # Filter out rows where we don't have growth rates (first month)
    monthly_df_filtered = monthly_df[monthly_df['total_growth_rate_pct'].notna()].copy()
    
    if monthly_df_filtered.empty:
        st.info('Not enough monthly data to calculate growth rates yet.')
        return
    
    # KPI for latest month growth rates with deltas
    if not monthly_df_filtered.empty:
        latest_month = monthly_df_filtered.iloc[-1]
        
        # Calculate deltas (change in growth rate from previous month)
        prev_month = monthly_df_filtered.iloc[-2] if len(monthly_df_filtered) >= 2 else None
        
        def calculate_growth_delta(current_rate, prev_rate):
            if prev_month is None or pd.isna(current_rate) or pd.isna(prev_rate):
                return None
            return current_rate - prev_rate
        
        total_delta = calculate_growth_delta(
            latest_month['total_growth_rate_pct'], 
            prev_month['total_growth_rate_pct'] if prev_month is not None else None
        )
        free_delta = calculate_growth_delta(
            latest_month['free_growth_rate_pct'], 
            prev_month['free_growth_rate_pct'] if prev_month is not None else None
        )
        awesome_delta = calculate_growth_delta(
            latest_month['awesome_growth_rate_pct'], 
            prev_month['awesome_growth_rate_pct'] if prev_month is not None else None
        )
        
        monthly_kpi_cols = st.columns(3)
        with monthly_kpi_cols[0]:
            st.metric(
                label='Overall Growth',
                value=f"{latest_month['total_growth_rate_pct']:.1f}%" if pd.notna(latest_month['total_growth_rate_pct']) else '—',
                delta=f"{total_delta:.1f}pp" if total_delta is not None else None
            )
        with monthly_kpi_cols[1]:
            st.metric(
                label='Free Growth',
                value=f"{latest_month['free_growth_rate_pct']:.1f}%" if pd.notna(latest_month['free_growth_rate_pct']) else '—',
                delta=f"{free_delta:.1f}pp" if free_delta is not None else None
            )
        with monthly_kpi_cols[2]:
            st.metric(
                label='Awesome Growth',
                value=f"{latest_month['awesome_growth_rate_pct']:.1f}%" if pd.notna(latest_month['awesome_growth_rate_pct']) else '—',
                delta=f"{awesome_delta:.1f}pp" if awesome_delta is not None else None
            )
    
    # Create combined bar and line chart
    fig_monthly = go.Figure()
    
    # Add Free growth rate bars
    fig_monthly.add_trace(go.Bar(
        x=monthly_df_filtered['month'],
        y=monthly_df_filtered['free_growth_rate_pct'],
        name='Free Growth %',
        marker_color='#b8b8ff',
        yaxis='y'
    ))
    
    # Add Awesome growth rate bars
    fig_monthly.add_trace(go.Bar(
        x=monthly_df_filtered['month'],
        y=monthly_df_filtered['awesome_growth_rate_pct'],
        name='Awesome Growth %',
        marker_color='#72a7ff',
        yaxis='y'
    ))
    
    # Add Overall growth rate line (overlay)
    fig_monthly.add_trace(go.Scatter(
        x=monthly_df_filtered['month'],
        y=monthly_df_filtered['total_growth_rate_pct'],
        mode='lines+markers',
        name='Overall Growth %',
        line=dict(color='#f59db1', width=3),
        marker=dict(size=8),
        yaxis='y'
    ))
    
    # Update layout for combined chart
    fig_monthly.update_layout(
        height=400,
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
        margin=dict(l=10, r=10, t=30, b=0),
        xaxis_title='Month',
        yaxis_title='Growth Rate (%)',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(tickformat='.1f')
    )
    
    # Add horizontal line at y=0 for reference
    fig_monthly.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig_monthly.update_xaxes(showgrid=False)
    fig_monthly.update_yaxes(showgrid=False)
    
    st.plotly_chart(fig_monthly, width='stretch', config={'displayModeBar': False})