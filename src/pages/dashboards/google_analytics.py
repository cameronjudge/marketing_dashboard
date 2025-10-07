import streamlit as st
import pandas as pd
import plotly.express as px
from src.db.bigquery_connection import run_query
from src.sql.google_analytics.google_analytics import ga_add_to_cart, ga_view_app

def google_analytics_page() -> None:
    st.set_page_config(
        page_title='Google Analytics',
        layout='wide'
    )
    
    st.title('Listing Analytics')
    
    df = run_query(ga_add_to_cart)
    if df.empty:
        st.info('No data available yet.')
    else:
        # Convert event_date from YYYYMMDD format to datetime
        df['event_date'] = pd.to_datetime(df['event_date'], format='%Y%m%d')
        df['week'] = df['event_date'].dt.to_period('W').dt.start_time
        
        # Get views data for top metrics
        views_df = run_query(ga_view_app)
        
        # Function to calculate week-over-week metrics
        def calculate_wow_metrics(df_carts, df_views):
            # Aggregate weekly data for both datasets
            weekly_carts = df_carts.groupby('week')['events_count'].sum().reset_index().sort_values('week')
            
            if not df_views.empty:
                df_views['event_date'] = pd.to_datetime(df_views['event_date'], format='%Y%m%d')
                df_views['week'] = df_views['event_date'].dt.to_period('W').dt.start_time
                weekly_views = df_views.groupby('week')['events_count'].sum().reset_index().sort_values('week')
            else:
                weekly_views = pd.DataFrame(columns=['week', 'events_count'])
            
            # Get last two weeks of data
            if len(weekly_carts) >= 2:
                last_week_carts = weekly_carts.iloc[-1]['events_count']
                prev_week_carts = weekly_carts.iloc[-2]['events_count']
                carts_delta = last_week_carts - prev_week_carts
            else:
                last_week_carts = weekly_carts.iloc[-1]['events_count'] if len(weekly_carts) > 0 else 0
                carts_delta = None
            
            if len(weekly_views) >= 2:
                last_week_views = weekly_views.iloc[-1]['events_count']
                prev_week_views = weekly_views.iloc[-2]['events_count']
                views_delta = last_week_views - prev_week_views
            else:
                last_week_views = weekly_views.iloc[-1]['events_count'] if len(weekly_views) > 0 else 0
                views_delta = None
            
            # Calculate conversion rates
            if last_week_views > 0:
                last_week_conversion = (last_week_carts / last_week_views) * 100
            else:
                last_week_conversion = 0
                
            if len(weekly_views) >= 2 and len(weekly_carts) >= 2 and prev_week_views > 0:
                prev_week_conversion = (prev_week_carts / prev_week_views) * 100
                conversion_delta = last_week_conversion - prev_week_conversion
            else:
                conversion_delta = None
            
            # Total events (views + carts)
            total_events = last_week_views + last_week_carts
            if views_delta is not None and carts_delta is not None:
                total_delta = views_delta + carts_delta
            else:
                total_delta = None
            
            return {
                'views': (last_week_views, views_delta),
                'carts': (last_week_carts, carts_delta),
                'conversion': (last_week_conversion, conversion_delta),
                'total': (total_events, total_delta)
            }
        
        # Calculate metrics
        metrics = calculate_wow_metrics(df, views_df)
        
        # Display top metrics
        kpi_cols = st.columns(4)
        kpis = [
            ('Views', metrics['views'][0], metrics['views'][1]),
            ('Add to Carts', metrics['carts'][0], metrics['carts'][1]),
            ('Conversion Rate', metrics['conversion'][0], metrics['conversion'][1]),
        ]
        
        for col, (label, val, delta) in zip(kpi_cols, kpis):
            with col:
                if val is None or pd.isna(val):
                    st.metric(label=label, value='—', delta=None)
                else:
                    if label == 'Conversion Rate':
                        st.metric(
                            label=label,
                            value=f"{val:.1f}%",
                            delta=(f"{delta:.1f}%" if delta is not None and pd.notna(delta) else None)
                        )
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
        
        # Add data labels on bars
        fig.update_traces(
            texttemplate='%{y:,.0f}',
            textposition='outside'
        )
        
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
        
        # New charts section
        st.divider()
        
        if not views_df.empty:
            # Convert event_date and add week column for views
            views_df['event_date'] = pd.to_datetime(views_df['event_date'], format='%Y%m%d')
            views_df['week'] = views_df['event_date'].dt.to_period('W').dt.start_time
            
            # Apply same filters to views data
            filtered_views_df = views_df.copy()
            
            if selected_mediums:
                filtered_views_df = filtered_views_df[filtered_views_df['medium_aggregated'].isin(selected_mediums)]
            
            if selected_sources:
                filtered_views_df = filtered_views_df[filtered_views_df['source_aggregated'].isin(selected_sources)]
            
            if selected_campaigns:
                filtered_views_df = filtered_views_df[filtered_views_df['campaign_aggregated'].isin(selected_campaigns)]
            
            if selected_campaign_details:
                filtered_views_df = filtered_views_df[filtered_views_df['campaign_details_aggregated'].isin(selected_campaign_details)]
            
            # Aggregate weekly data
            weekly_views = filtered_views_df.groupby('week')['events_count'].sum().reset_index()
            weekly_views.columns = ['week', 'views']
            
            weekly_carts = filtered_df.groupby('week')['events_count'].sum().reset_index()
            weekly_carts.columns = ['week', 'add_to_carts']
            
            # Merge views and carts data
            combined_df = pd.merge(weekly_views, weekly_carts, on='week', how='outer').fillna(0)
            
            # Create two columns for the new charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Chart 1: Views and Add to Carts tracking
                fig_tracking = px.line(
                    combined_df.melt(id_vars=['week'], value_vars=['views', 'add_to_carts'], 
                                   var_name='metric', value_name='count'),
                    x='week',
                    y='count',
                    color='metric',
                    title='Weekly Views vs Add to Carts',
                    markers=True
                )
                
                # Add data labels on points
                for trace in fig_tracking.data:
                    trace.textposition = 'top center'
                    trace.texttemplate = '%{y:,.0f}'
                    trace.mode = 'lines+markers+text'
                
                # Apply styling
                fig_tracking.update_layout(
                    showlegend=True,
                    margin=dict(l=10, r=10, t=30, b=0),
                    xaxis_title=None,
                    yaxis_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.1,
                        xanchor='center',
                        x=0.5
                    )
                )
                
                fig_tracking.update_xaxes(showgrid=False)
                fig_tracking.update_yaxes(showgrid=False)
                
                st.plotly_chart(fig_tracking, use_container_width=True)
            
            with col2:
                # Chart 2: Conversion rate (add to cart / views)
                combined_df['conversion_rate'] = (combined_df['add_to_carts'] / combined_df['views'] * 100).fillna(0)
                
                fig_conversion = px.line(
                    combined_df,
                    x='week',
                    y='conversion_rate',
                    title='Weekly Add to Cart Conversion Rate (%)',
                    markers=True
                )
                
                # Add data labels on points
                fig_conversion.update_traces(
                    textposition='top center',
                    texttemplate='%{y:.1f}%',
                    mode='lines+markers+text'
                )
                
                # Apply styling
                fig_conversion.update_layout(
                    showlegend=False,
                    margin=dict(l=10, r=10, t=30, b=0),
                    xaxis_title=None,
                    yaxis_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                
                fig_conversion.update_xaxes(showgrid=False)
                fig_conversion.update_yaxes(showgrid=False, range=[0, None])
                
                st.plotly_chart(fig_conversion, use_container_width=True)
        
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
