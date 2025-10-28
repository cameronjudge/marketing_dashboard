import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.db.redshift_connection import run_query, get_redshift_connection
from src.sql.core_metrics.general_metrics import general_metrics


def general_metrics_page():
    st.set_page_config(
        page_title='General Metrics',
        layout='wide'
    )
    
    st.title('General Business Metrics')
    
    df = run_query(general_metrics)

    df['week'] = pd.to_datetime(df['week'])
    
    if df.empty:
        st.info('No general metrics data available yet.')
        return
    
    # Calculate WOW growth for each metric
    def calculate_wow_growth(data, metric_key):
        metric_data = data[data['key'] == metric_key].copy()
        if len(metric_data) < 2:
            return None, None, None
        
        metric_data = metric_data.sort_values('week')
        current_value = metric_data.iloc[-1]['value']
        previous_value = metric_data.iloc[-2]['value']
        
        wow_change = current_value - previous_value
        wow_percent = (wow_change / previous_value * 100) if previous_value != 0 else 0
        
        return current_value, wow_change, wow_percent
    
    # Key metrics for KPI cards
    key_metrics = [
        ('active_shops_count', 'Active Shops', '{:,.0f}'),
        ('annual_revenue', 'Annual Revenue', '${:,.0f}'),
        ('homepage_metrics__line_items_count', 'Line Items', '{:,.0f}'),
        ('real_awesome_count', 'Real Awesome Count', '{:,.0f}'),
        ('shopify_core_app_reviews_count', 'Core App Reviews', '{:,.0f}')
    ]
    
    # Display KPI cards
    st.subheader('Key Performance Indicators - Week over Week')
    
    kpi_cols = st.columns(len(key_metrics))
    
    for i, (metric_key, display_name, format_str) in enumerate(key_metrics):
        current_value, wow_change, wow_percent = calculate_wow_growth(df, metric_key)
        
        with kpi_cols[i]:
            if current_value is not None:
                st.metric(
                    label=display_name,
                    value=format_str.format(current_value),
                    delta=f"{wow_change:+,.0f} ({wow_percent:+.1f}%)" if wow_change is not None else None
                )
            else:
                st.metric(label=display_name, value="—", delta=None)
    
    st.divider()
    
    # Create trend charts
    st.subheader('Metrics Trends Over Time')
    
    # Group metrics by category for better visualization
    business_metrics = ['active_shops_count', 'annual_revenue']
    engagement_metrics = ['homepage_metrics__line_items_count', 'real_awesome_count']
    review_metrics = ['shopify_core_app_reviews_count', 'shopify_ali_app_reviews_count']
    
    # Business Growth Metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Business Growth Metrics**")
        
        business_data = df[df['key'].isin(business_metrics)].copy()
        
        if not business_data.empty:
            # Create separate charts for different scales
            active_shops_data = business_data[business_data['key'] == 'active_shops_count']
            
            if not active_shops_data.empty:
                fig_shops = px.line(
                    active_shops_data,
                    x='week',
                    y='value',
                    title='Active Shops Count',
                    markers=True
                )
                
                fig_shops.update_traces(line_color='#1f77b4')
                fig_shops.update_layout(
                    showlegend=False,
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis_title=None,
                    yaxis_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=300
                )
                fig_shops.update_xaxes(showgrid=False)
                fig_shops.update_yaxes(showgrid=False)
                
                st.plotly_chart(fig_shops, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No business metrics data available.")
    
    with col2:
        st.write("**Annual Revenue**")
        
        revenue_data = df[df['key'] == 'annual_revenue']
        
        if not revenue_data.empty:
            fig_revenue = px.line(
                revenue_data,
                x='week',
                y='value',
                title='Annual Revenue ($)',
                markers=True
            )
            
            fig_revenue.update_traces(line_color='#2ca02c')
            fig_revenue.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title=None,
                yaxis_title=None,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=300
            )
            fig_revenue.update_xaxes(showgrid=False)
            fig_revenue.update_yaxes(showgrid=False)
            
            st.plotly_chart(fig_revenue, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No revenue data available.")
    
    # Engagement Metrics
    st.subheader('Engagement Metrics')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Homepage Line Items**")
        
        line_items_data = df[df['key'] == 'homepage_metrics__line_items_count']
        
        if not line_items_data.empty:
            fig_line_items = px.line(
                line_items_data,
                x='week',
                y='value',
                title='Homepage Line Items Count',
                markers=True
            )
            
            fig_line_items.update_traces(line_color='#ff7f0e')
            fig_line_items.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title=None,
                yaxis_title=None,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=300
            )
            fig_line_items.update_xaxes(showgrid=False)
            fig_line_items.update_yaxes(showgrid=False)
            
            st.plotly_chart(fig_line_items, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No line items data available.")
    
    with col2:
        st.write("**Real Awesome Count**")
        
        awesome_data = df[df['key'] == 'real_awesome_count']
        
        if not awesome_data.empty:
            fig_awesome = px.line(
                awesome_data,
                x='week',
                y='value',
                title='Real Awesome Count',
                markers=True
            )
            
            fig_awesome.update_traces(line_color='#d62728')
            fig_awesome.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title=None,
                yaxis_title=None,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=300
            )
            fig_awesome.update_xaxes(showgrid=False)
            fig_awesome.update_yaxes(showgrid=False)
            
            st.plotly_chart(fig_awesome, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No awesome count data available.")
    
    # Review Metrics
    st.subheader('App Reviews Metrics')
    
    review_data = df[df['key'].isin(review_metrics)]
    
    if not review_data.empty:
        fig_reviews = px.line(
            review_data,
            x='week',
            y='value',
            color='key',
            title='Shopify App Reviews Count',
            markers=True
        )
        
        # Update legend labels
        fig_reviews.for_each_trace(
            lambda trace: trace.update(name=trace.name.replace('shopify_', '').replace('_app_reviews_count', '').replace('_', ' ').title())
        )
        
        fig_reviews.update_layout(
            showlegend=True,
            margin=dict(l=10, r=10, t=30, b=60),
            xaxis_title=None,
            yaxis_title=None,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=400,
            legend=dict(
                orientation='h',
                yanchor='top',
                y=-0.15,
                xanchor='center',
                x=0.5
            )
        )
        fig_reviews.update_xaxes(showgrid=False)
        fig_reviews.update_yaxes(showgrid=False)
        
        st.plotly_chart(fig_reviews, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No review metrics data available.")
    
    # Net Growth Charts
    st.subheader('Net Growth Analysis')
    st.write("*Week-over-week net growth for key business metrics*")
    
    # Calculate net growth for the three key metrics
    target_metrics = [
        ('active_shops_count', 'Active Shops', '#1f77b4'),
        ('real_awesome_count', 'Real Awesome Count', '#d62728'), 
        ('annual_revenue', 'Annual Revenue', '#2ca02c')
    ]
    
    # Function to calculate net growth
    def calculate_net_growth(data, metric_key):
        metric_data = data[data['key'] == metric_key].copy()
        if len(metric_data) < 2:
            return pd.DataFrame()
        
        metric_data = metric_data.sort_values('week')
        
        # Calculate week-over-week net growth
        metric_data['previous_value'] = metric_data['value'].shift(1)
        metric_data['net_growth'] = metric_data['value'] - metric_data['previous_value']
        metric_data['growth_rate'] = (metric_data['net_growth'] / metric_data['previous_value'] * 100).fillna(0)
        
        return metric_data.dropna()
    
    # Create net growth charts
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Active Shops Net Growth**")
        
        active_shops_growth = calculate_net_growth(df, 'active_shops_count')
        
        if not active_shops_growth.empty:
            fig_shops_growth = px.line(
                active_shops_growth,
                x='week',
                y='net_growth',
                title='Weekly Net Growth - Active Shops',
                markers=True
            )
            
            fig_shops_growth.update_traces(line_color='#1f77b4')
            
            fig_shops_growth.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title=None,
                yaxis_title='Net Growth',
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=350
            )
            fig_shops_growth.update_xaxes(showgrid=False)
            fig_shops_growth.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            
            # Add zero line
            fig_shops_growth.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            st.plotly_chart(fig_shops_growth, use_container_width=True, config={'displayModeBar': False})
            
            # Show latest growth
            latest_growth = active_shops_growth.iloc[-1]['net_growth']
            latest_rate = active_shops_growth.iloc[-1]['growth_rate']
            st.metric("Latest Weekly Growth", f"{latest_growth:+,.0f}", f"{latest_rate:+.2f}%")
        else:
            st.info("Insufficient data for growth calculation.")
    
    with col2:
        st.write("**Real Awesome Count Net Growth**")
        
        awesome_growth = calculate_net_growth(df, 'real_awesome_count')
        
        if not awesome_growth.empty:
            fig_awesome_growth = px.line(
                awesome_growth,
                x='week',
                y='net_growth',
                title='Weekly Net Growth - Real Awesome Count',
                markers=True
            )
            
            fig_awesome_growth.update_traces(line_color='#d62728')
            
            fig_awesome_growth.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title=None,
                yaxis_title='Net Growth',
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=350
            )
            fig_awesome_growth.update_xaxes(showgrid=False)
            fig_awesome_growth.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            
            # Add zero line
            fig_awesome_growth.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            st.plotly_chart(fig_awesome_growth, use_container_width=True, config={'displayModeBar': False})
            
            # Show latest growth
            latest_growth = awesome_growth.iloc[-1]['net_growth']
            latest_rate = awesome_growth.iloc[-1]['growth_rate']
            st.metric("Latest Weekly Growth", f"{latest_growth:+,.0f}", f"{latest_rate:+.2f}%")
        else:
            st.info("Insufficient data for growth calculation.")
    
    with col3:
        st.write("**Annual Revenue Net Growth**")
        
        revenue_growth = calculate_net_growth(df, 'annual_revenue')
        
        if not revenue_growth.empty:
            fig_revenue_growth = px.line(
                revenue_growth,
                x='week',
                y='net_growth',
                title='Weekly Net Growth - Annual Revenue',
                markers=True
            )
            
            fig_revenue_growth.update_traces(line_color='#2ca02c')
            
            fig_revenue_growth.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title=None,
                yaxis_title='Net Growth ($)',
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=350
            )
            fig_revenue_growth.update_xaxes(showgrid=False)
            fig_revenue_growth.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            
            # Add zero line
            fig_revenue_growth.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            st.plotly_chart(fig_revenue_growth, use_container_width=True, config={'displayModeBar': False})
            
            # Show latest growth
            latest_growth = revenue_growth.iloc[-1]['net_growth']
            latest_rate = revenue_growth.iloc[-1]['growth_rate']
            st.metric("Latest Weekly Growth", f"${latest_growth:+,.0f}", f"{latest_rate:+.2f}%")
        else:
            st.info("Insufficient data for growth calculation.")
    
    # Combined Net Growth Trends
    st.subheader('Combined Net Growth Trends')
    
    # Create a combined chart showing all three metrics (normalized)
    combined_growth_data = []
    
    for metric_key, display_name, color in target_metrics:
        growth_data = calculate_net_growth(df, metric_key)
        if not growth_data.empty:
            for _, row in growth_data.iterrows():
                combined_growth_data.append({
                    'week': row['week'],
                    'metric': display_name,
                    'growth_rate': row['growth_rate'],
                    'net_growth': row['net_growth']
                })
    
    if combined_growth_data:
        combined_df = pd.DataFrame(combined_growth_data)
        
        # Growth rate comparison chart
        fig_combined_rate = px.line(
            combined_df,
            x='week',
            y='growth_rate',
            color='metric',
            title='Weekly Growth Rate Comparison (%)',
            markers=True
        )
        
        fig_combined_rate.update_layout(
            showlegend=True,
            margin=dict(l=10, r=10, t=30, b=60),
            xaxis_title=None,
            yaxis_title='Growth Rate (%)',
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=400,
            legend=dict(
                orientation='h',
                yanchor='top',
                y=-0.15,
                xanchor='center',
                x=0.5
            )
        )
        fig_combined_rate.update_xaxes(showgrid=False)
        fig_combined_rate.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        
        # Add zero line
        fig_combined_rate.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        st.plotly_chart(fig_combined_rate, use_container_width=True, config={'displayModeBar': False})
    
    # Growth Summary Table
    st.subheader('Growth Summary Statistics')
    
    growth_summary = []
    
    for metric_key, display_name, _ in target_metrics:
        growth_data = calculate_net_growth(df, metric_key)
        if not growth_data.empty:
            avg_growth = growth_data['net_growth'].mean()
            avg_growth_rate = growth_data['growth_rate'].mean()
            total_growth = growth_data['net_growth'].sum()
            positive_weeks = (growth_data['net_growth'] > 0).sum()
            total_weeks = len(growth_data)
            
            growth_summary.append({
                'Metric': display_name,
                'Avg Weekly Growth': f"{avg_growth:+,.0f}",
                'Avg Growth Rate': f"{avg_growth_rate:+.2f}%",
                'Total Net Growth': f"{total_growth:+,.0f}",
                'Positive Growth Weeks': f"{positive_weeks}/{total_weeks}",
                'Growth Success Rate': f"{(positive_weeks/total_weeks*100):.1f}%"
            })
    
    if growth_summary:
        summary_df = pd.DataFrame(growth_summary)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # # Data Quality and Coverage
    # st.subheader('Data Coverage Summary')
    
    # col1, col2 = st.columns(2)
    
    # with col1:
    #     st.write("**Metrics Coverage**")
        
    #     coverage_data = []
    #     unique_metrics = df['key'].unique()
        
    #     for metric in unique_metrics:
    #         metric_data = df[df['key'] == metric]
    #         weeks_count = len(metric_data)
    #         latest_week = metric_data['week'].max().strftime('%Y-%m-%d')
            
    #         coverage_data.append({
    #             'Metric': metric.replace('_', ' ').title(),
    #             'Weeks of Data': weeks_count,
    #             'Latest Week': latest_week
    #         })
        
    #     coverage_df = pd.DataFrame(coverage_data)
    #     st.dataframe(coverage_df, use_container_width=True, hide_index=True)
    
    # with col2:
    #     st.write("**Summary Statistics**")
        
    #     total_weeks = len(df['week'].unique())
    #     total_metrics = len(df['key'].unique())
    #     date_range = f"{df['week'].min().strftime('%Y-%m-%d')} to {df['week'].max().strftime('%Y-%m-%d')}"
        
    #     st.metric("Total Weeks", total_weeks)
    #     st.metric("Total Metrics", total_metrics)
    #     st.write(f"**Date Range**: {date_range}")
    
    return