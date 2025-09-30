import streamlit as st
import pandas as pd
import plotly.express as px
from src.db.bigquery_connection import run_query
from src.sql.google_analytics.google_analytics import google_analytics_query

def google_analytics_page() -> None:
    st.set_page_config(
        page_title='Google Analytics',
        layout='wide'
    )
    
    st.title('Google Analytics')
    
    df = run_query(google_analytics_query)
    if df.empty:
        st.info('No data available yet.')
    else:
        # Convert event_date from YYYYMMDD format to datetime
        df['event_date'] = pd.to_datetime(df['event_date'], format='%Y%m%d')
        df['week'] = df['event_date'].dt.to_period('W').dt.start_time
        
        # Top metrics for key mediums with WoW deltas
        def latest_with_delta_medium(frame: pd.DataFrame, medium: str):
            temp = frame[frame['medium_aggregated'] == medium].groupby('week')['events_count'].sum().reset_index()
            if temp.empty:
                return None, None
            temp = temp.sort_values('week')
            latest_val = temp.iloc[-1]['events_count']
            if len(temp) < 2:
                return latest_val, None
            prev_val = temp.iloc[-2]['events_count']
            try:
                delta_val = float(latest_val) - float(prev_val)
            except Exception:
                delta_val = None
            return latest_val, delta_val
        
        # Calculate metrics for key mediums
        organic_latest, organic_delta = latest_with_delta_medium(df, 'organic_placement')
        paid_latest, paid_delta = latest_with_delta_medium(df, 'paid_search')
        partner_latest, partner_delta = latest_with_delta_medium(df, 'partner')
        website_latest, website_delta = latest_with_delta_medium(df, 'website')
        
        # Display top metrics
        kpi_cols = st.columns(4)
        kpis = [
            ('Organic', organic_latest, organic_delta),
            ('Paid Search', paid_latest, paid_delta),
            ('Partner', partner_latest, partner_delta),
            ('Website', website_latest, website_delta),
        ]
        
        for col, (label, val, delta) in zip(kpi_cols, kpis):
            with col:
                if val is None or pd.isna(val):
                    st.metric(label=label, value='—', delta=None)
                else:
                    st.metric(
                        label=label,
                        value=f"{int(val):,}",
                        delta=(int(delta) if delta is not None and pd.notna(delta) else None)
                    )
        
        st.divider()
        
        # Cascading Filters
        col1, col2, col3, col4 = st.columns(4)
        
        # Start with full dataset for first filter
        current_df = df.copy()
        
        with col1:
            medium_options = sorted(current_df['medium_aggregated'].dropna().unique().tolist())
            selected_mediums = st.multiselect('Medium', medium_options, default=[])
        
        # Filter for next dropdown
        if selected_mediums:
            current_df = current_df[current_df['medium_aggregated'].isin(selected_mediums)]
        
        with col2:
            source_options = sorted(current_df['source_aggregated'].dropna().unique().tolist())
            selected_sources = st.multiselect('Source', source_options, default=[])
        
        # Filter for next dropdown
        if selected_sources:
            current_df = current_df[current_df['source_aggregated'].isin(selected_sources)]
        
        with col3:
            campaign_options = sorted(current_df['campaign_aggregated'].dropna().unique().tolist())
            selected_campaigns = st.multiselect('Campaign', campaign_options, default=[])
        
        # Filter for next dropdown
        if selected_campaigns:
            current_df = current_df[current_df['campaign_aggregated'].isin(selected_campaigns)]
        
        with col4:
            campaign_details_options = sorted(current_df['campaign_details_aggregated'].dropna().unique().tolist())
            selected_campaign_details = st.multiselect('Campaign Details', campaign_details_options, default=[])
        
        # Apply all filters to original dataframe
        filtered_df = df.copy()
        
        if selected_mediums:
            filtered_df = filtered_df[filtered_df['medium_aggregated'].isin(selected_mediums)]
        
        if selected_sources:
            filtered_df = filtered_df[filtered_df['source_aggregated'].isin(selected_sources)]
        
        if selected_campaigns:
            filtered_df = filtered_df[filtered_df['campaign_aggregated'].isin(selected_campaigns)]
        
        if selected_campaign_details:
            filtered_df = filtered_df[filtered_df['campaign_details_aggregated'].isin(selected_campaign_details)]
        
        # Determine which dimension to color by based on filter selection stage
        if selected_campaign_details:
            # Most specific - color by campaign details
            color_column = 'campaign_details_aggregated'
            title = 'Weekly Events Count by Campaign Details'
        elif selected_campaigns:
            # Color by campaigns
            color_column = 'campaign_aggregated'
            title = 'Weekly Events Count by Campaign'
        elif selected_sources:
            # Color by sources
            color_column = 'source_aggregated'
            title = 'Weekly Events Count by Source'
        elif selected_mediums:
            # Color by mediums
            color_column = 'medium_aggregated'
            title = 'Weekly Events Count by Medium'
        else:
            # No filters - single color
            color_column = None
            title = 'Weekly Events Count'
        
        # Add week column for grouping
        filtered_df['week'] = filtered_df['event_date'].dt.to_period('W').dt.start_time
        
        if color_column:
            # Aggregate by week and the selected dimension
            weekly_events = filtered_df.groupby(['week', color_column])['events_count'].sum().reset_index()
            
            # Create stacked bar chart with colors
            fig = px.bar(
                weekly_events,
                x='week',
                y='events_count',
                color=color_column,
                title=title.replace('Daily', 'Weekly')
            )
            
            # Show legend under the chart
            show_legend = True
            legend_config = dict(
                orientation='h',
                yanchor='top',
                y=-0.1,
                xanchor='center',
                x=0.5
            )
        else:
            # Aggregate by week only for simple bar chart
            weekly_events = filtered_df.groupby('week')['events_count'].sum().reset_index()
            
            # Create simple bar chart without colors
            fig = px.bar(
                weekly_events,
                x='week',
                y='events_count',
                title=title.replace('Daily', 'Weekly')
            )
            
            # No legend needed
            show_legend = False
            legend_config = dict()
        
        # Apply consistent dashboard styling
        fig.update_layout(
            showlegend=show_legend,
            margin=dict(l=10, r=10, t=30, b=60 if show_legend else 0),
            xaxis_title=None,
            yaxis_title=None,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=legend_config
        )
        
        # Update axes to match dashboard style
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)

        st.plotly_chart(fig, use_container_width=True)
        
        # Sources breakdown table
        st.subheader('Sources Breakdown')
        
        # Date filter for table
        col1, col2 = st.columns(2)
        with col1:
            min_date = filtered_df['event_date'].min().date()
            max_date = filtered_df['event_date'].max().date()
            start_date = st.date_input('Start Date', value=min_date, min_value=min_date, max_value=max_date)
        
        with col2:
            end_date = st.date_input('End Date', value=max_date, min_value=min_date, max_value=max_date)
        
        # Filter by date range
        table_df = filtered_df[
            (filtered_df['event_date'].dt.date >= start_date) & 
            (filtered_df['event_date'].dt.date <= end_date)
        ]
        
        # Aggregate by source
        sources_table = table_df.groupby('source_aggregated')['events_count'].sum().reset_index()
        sources_table = sources_table.sort_values('events_count', ascending=False)
        sources_table.columns = ['Source', 'Events Count']
        
        st.dataframe(sources_table, use_container_width=True)
