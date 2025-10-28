import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.db.bigquery_connection import run_query
from src.sql.google_analytics.google_analytics import ga_installs, ga_view_app
from src.utils.plotly_config import render_plotly_chart

def google_analytics_page() -> None:
    st.set_page_config(
        page_title='Google Analytics',
        layout='wide'
    )
    
    st.title('Listing Analytics')
    
    df = run_query(ga_installs)
    if df.empty:
        st.info('No data available yet.')
    else:
        # Convert event_date from YYYYMMDD format to datetime
        df['event_date'] = pd.to_datetime(df['event_date'], format='%Y%m%d')
        df['week'] = df['event_date'].dt.to_period('W').dt.start_time
        
        # Get views data for top metrics
        views_df = run_query(ga_view_app)
        
        # Function to calculate week-over-week metrics
        def calculate_wow_metrics(df_installs, df_views):
            # Aggregate weekly data for both datasets
            weekly_installs = df_installs.groupby('week')['events_count'].sum().reset_index().sort_values('week')
            
            if not df_views.empty:
                df_views['event_date'] = pd.to_datetime(df_views['event_date'], format='%Y%m%d')
                df_views['week'] = df_views['event_date'].dt.to_period('W').dt.start_time
                weekly_views = df_views.groupby('week')['events_count'].sum().reset_index().sort_values('week')
            else:
                weekly_views = pd.DataFrame(columns=['week', 'events_count'])
            
            # Get last two weeks of data
            if len(weekly_installs) >= 2:
                last_week_installs = weekly_installs.iloc[-1]['events_count']
                prev_week_installs = weekly_installs.iloc[-2]['events_count']
                installs_delta = last_week_installs - prev_week_installs
            else:
                last_week_installs = weekly_installs.iloc[-1]['events_count'] if len(weekly_installs) > 0 else 0
                installs_delta = None
            
            if len(weekly_views) >= 2:
                last_week_views = weekly_views.iloc[-1]['events_count']
                prev_week_views = weekly_views.iloc[-2]['events_count']
                views_delta = last_week_views - prev_week_views
            else:
                last_week_views = weekly_views.iloc[-1]['events_count'] if len(weekly_views) > 0 else 0
                views_delta = None
            
            # Calculate conversion rates
            if last_week_views > 0:
                last_week_conversion = (last_week_installs / last_week_views) * 100
            else:
                last_week_conversion = 0
                
            if len(weekly_views) >= 2 and len(weekly_installs) >= 2 and prev_week_views > 0:
                prev_week_conversion = (prev_week_installs / prev_week_views) * 100
                conversion_delta = last_week_conversion - prev_week_conversion
            else:
                conversion_delta = None
            
            # Total events (views + installs)
            total_events = last_week_views + last_week_installs
            if views_delta is not None and installs_delta is not None:
                total_delta = views_delta + installs_delta
            else:
                total_delta = None
            
            return {
                'views': (last_week_views, views_delta),
                'installs': (last_week_installs, installs_delta),
                'conversion': (last_week_conversion, conversion_delta),
                'total': (total_events, total_delta)
            }


        # top navigation
        overview, overview_trends, organic, organic_trends, partner, paid, website = st.tabs(['Overview', 'Overview - Trends', 'Organic', 'Organic - Trends', 'Partner', 'Paid', 'Website'])
        
        # Calculate metrics
        metrics = calculate_wow_metrics(df, views_df)
        
        # Display top metrics
        with overview:
            kpi_cols = st.columns(4)
            kpis = [
                ('Views', metrics['views'][0], metrics['views'][1]),
                ('Installs', metrics['installs'][0], metrics['installs'][1]),
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
                
                weekly_installs = filtered_df.groupby('week')['events_count'].sum().reset_index()
                weekly_installs.columns = ['week', 'installs']
                
                # Merge views and installs data
                combined_df = pd.merge(weekly_views, weekly_installs, on='week', how='outer').fillna(0)
                
                # Create two columns for the new charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Chart 1: Views and Installs tracking
                    fig_tracking = px.line(
                        combined_df.melt(id_vars=['week'], value_vars=['views', 'installs'], 
                                    var_name='metric', value_name='count'),
                        x='week',
                        y='count',
                        color='metric',
                        title='Weekly Views vs Installs',
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
                    # Chart 2: Conversion rate (installs / views)
                    combined_df['conversion_rate'] = (combined_df['installs'] / combined_df['views'] * 100).fillna(0)
                    
                    fig_conversion = px.line(
                        combined_df,
                        x='week',
                        y='conversion_rate',
                        title='Weekly Install Conversion Rate (%)',
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
            st.subheader('Medium Breakdown')
            
            # Date filter for table - default to last completed week
            col1, col2 = st.columns(2)
            
            # Calculate last completed week (Monday to Sunday)
            today = pd.Timestamp.now().normalize()
            days_since_monday = today.weekday()  # Monday = 0, Sunday = 6
            last_monday = today - pd.Timedelta(days=days_since_monday + 7)  # Previous week's Monday
            last_sunday = last_monday + pd.Timedelta(days=6)  # Previous week's Sunday
            
            # Get available date range from data
            min_date = filtered_df['event_date'].min().date()
            max_date = filtered_df['event_date'].max().date()
            
            # Use last completed week as default, but allow user to change
            default_start = max(last_monday.date(), min_date)
            default_end = min(last_sunday.date(), max_date)
            
            with col1:
                start_date = st.date_input('Start Date', value=default_start, min_value=min_date, max_value=max_date)
            
            with col2:
                end_date = st.date_input('End Date', value=default_end, min_value=min_date, max_value=max_date)
            
            # Filter by date range for current period
            table_df = filtered_df[
                (filtered_df['event_date'].dt.date >= start_date) & 
                (filtered_df['event_date'].dt.date <= end_date)
            ]
            
            # Calculate previous period for WoW comparison
            period_length = (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days + 1
            prev_start_date = pd.Timestamp(start_date) - pd.Timedelta(days=period_length)
            prev_end_date = pd.Timestamp(start_date) - pd.Timedelta(days=1)
            
            # Filter for previous period
            prev_table_df = filtered_df[
                (filtered_df['event_date'].dt.date >= prev_start_date.date()) & 
                (filtered_df['event_date'].dt.date <= prev_end_date.date())
            ]
            
            # Aggregate current period by source
            current_sources = table_df.groupby('source_aggregated')['events_count'].sum().reset_index()
            current_sources.columns = ['Source', 'Current_Events']
            
            # Aggregate previous period by source
            prev_sources = prev_table_df.groupby('source_aggregated')['events_count'].sum().reset_index()
            prev_sources.columns = ['Source', 'Previous_Events']
            
            # Merge current and previous data
            sources_table = pd.merge(current_sources, prev_sources, on='Source', how='left')
            sources_table['Previous_Events'] = sources_table['Previous_Events'].fillna(0)
            
            # Calculate WoW delta
            sources_table['WoW_Delta'] = sources_table['Current_Events'] - sources_table['Previous_Events']
            sources_table['WoW_Percent'] = ((sources_table['Current_Events'] - sources_table['Previous_Events']) / 
                                          sources_table['Previous_Events'].replace(0, 1) * 100).round(1)
            
            # Handle cases where previous period had 0 events
            sources_table.loc[sources_table['Previous_Events'] == 0, 'WoW_Percent'] = None
            
            # Format the final table
            sources_table = sources_table.sort_values('Current_Events', ascending=False)
            
            # Create display table with formatted columns
            display_table = sources_table[['Source', 'Current_Events', 'WoW_Delta', 'WoW_Percent']].copy()
            display_table.columns = ['Source', 'Events Count', 'WoW Δ', 'WoW %']
            
            # Format the WoW % column to show percentage with proper handling of None values
            display_table['WoW %'] = display_table['WoW %'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
            )
            
            st.dataframe(display_table, width='stretch')
        
        with overview_trends:
            st.subheader('Trends Analysis')
            
            # Installs - last 30 days
            st.subheader('Installs - last 30 days')
            
            # Filter to installs events only (last 30 days)
            installs_last_30 = df[df['event_date'] >= (df['event_date'].max() - pd.Timedelta(days=30))].copy()
            
            # Aggregate by date
            installs_daily = installs_last_30.groupby('event_date')['events_count'].sum().reset_index()
            
            fig_installs = px.line(
                installs_daily,
                x='event_date',
                y='events_count',
                title='Installs - last 30 days',
                markers=True
            )
            
            fig_installs.update_traces(line_color='#2E8B57')  # Sea green color
            
            fig_installs.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title=None,
                yaxis_title=None,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            
            fig_installs.update_xaxes(showgrid=False)
            fig_installs.update_yaxes(showgrid=False)
            
            st.plotly_chart(fig_installs, use_container_width=True)
            
            st.divider()
            
            # Prepare data for trends - combine both installs and view_item data
            combined_trends_df = df.copy()
            combined_trends_df['event_type'] = 'installs'
            
            if not views_df.empty:
                views_trends_df = views_df.copy()
                views_trends_df['event_date'] = pd.to_datetime(views_trends_df['event_date'], format='%Y%m%d')
                views_trends_df['event_type'] = 'view_item'
                combined_trends_df = pd.concat([combined_trends_df, views_trends_df], ignore_index=True)
            
            # Language Trends - Last 8 completed weeks (top 10)
            st.subheader('Language - Last 8 completed weeks (top 10)')
            
            # Calculate last 8 completed weeks
            latest_date = combined_trends_df['event_date'].max()
            # Find the start of the current week (Monday)
            current_week_start = latest_date - pd.Timedelta(days=latest_date.weekday())
            # Go back 8 weeks from the start of current week to get 8 completed weeks
            eight_weeks_ago = current_week_start - pd.Timedelta(weeks=8)
            last_completed_week_end = current_week_start - pd.Timedelta(days=1)
            
            # Filter to last 8 completed weeks
            language_df = combined_trends_df[
                (combined_trends_df['event_date'] >= eight_weeks_ago) & 
                (combined_trends_df['event_date'] <= last_completed_week_end)
            ].copy()
            
            # Add week column for weekly aggregation
            language_df['week'] = language_df['event_date'].dt.to_period('W').dt.start_time
            
            # Get top 10 languages by total events
            top_languages = language_df.groupby('locale_aggregated')['events_count'].sum().nlargest(10).index.tolist()
            language_df = language_df[language_df['locale_aggregated'].isin(top_languages)]
            
            # Aggregate by week and language
            language_weekly = language_df.groupby(['week', 'locale_aggregated'])['events_count'].sum().reset_index()
            
            # Create language trends chart
            fig_language = px.line(
                language_weekly,
                x='week',
                y='events_count',
                color='locale_aggregated',
                title='Language - Last 8 completed weeks (top 10)',
                markers=True
            )
            
            fig_language.update_layout(
                showlegend=True,
                margin=dict(l=10, r=10, t=30, b=60),
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
            
            fig_language.update_xaxes(showgrid=False)
            fig_language.update_yaxes(showgrid=False)
            
            st.plotly_chart(fig_language, use_container_width=True)
            
            # Individual language charts with WoW data and conversion rates
            st.subheader('Individual Language Trends')
            st.caption("📊 Conversion Rate = (Installs from ga_installs ÷ Views from ga_view_app) × 100 by language and week")
            
            # Create 2 columns for the grid
            col1, col2 = st.columns(2)
            
            for i, language in enumerate(top_languages):
                # Get installs data for this language (from ga_installs - last 8 completed weeks)
                installs_lang_data = df[
                    (df['locale_aggregated'] == language) & 
                    (df['event_date'] >= eight_weeks_ago) & 
                    (df['event_date'] <= last_completed_week_end)
                ].copy()
                installs_lang_data['week'] = installs_lang_data['event_date'].dt.to_period('W').dt.start_time
                installs_weekly = installs_lang_data.groupby('week')['events_count'].sum().reset_index()
                installs_weekly = installs_weekly.rename(columns={'events_count': 'installs_count'})
                
                # Get views data for this language (from ga_view_app - last 8 completed weeks)
                if not views_df.empty:
                    views_df_processed = views_df.copy()
                    views_df_processed['event_date'] = pd.to_datetime(views_df_processed['event_date'], format='%Y%m%d')
                    views_lang_data = views_df_processed[
                        (views_df_processed['locale_aggregated'] == language) & 
                        (views_df_processed['event_date'] >= eight_weeks_ago) & 
                        (views_df_processed['event_date'] <= last_completed_week_end)
                    ].copy()
                    views_lang_data['week'] = views_lang_data['event_date'].dt.to_period('W').dt.start_time
                    views_weekly = views_lang_data.groupby('week')['events_count'].sum().reset_index()
                    views_weekly = views_weekly.rename(columns={'events_count': 'views_count'})
                    
                    # Merge installs and views data properly
                    combined_data = pd.merge(installs_weekly, views_weekly, on='week', how='outer').fillna(0)
                    
                    # Calculate proper conversion rate
                    combined_data['conversion_rate'] = combined_data.apply(
                        lambda row: (row['installs_count'] / row['views_count'] * 100) 
                        if row['views_count'] > 0 
                        else 0, axis=1
                    ).round(2)
                else:
                    combined_data = installs_weekly.copy()
                    combined_data = combined_data.rename(columns={'installs_count': 'installs_count'})
                    combined_data['views_count'] = 0
                    combined_data['conversion_rate'] = 0
                
                # Calculate WoW change for installs
                combined_data = combined_data.sort_values('week')
                combined_data['prev_week_installs'] = combined_data['installs_count'].shift(1)
                combined_data['wow_change'] = ((combined_data['installs_count'] - combined_data['prev_week_installs']) / combined_data['prev_week_installs'] * 100).round(1)
                
                # Create subplot with secondary y-axis
                fig_individual = make_subplots(
                    specs=[[{"secondary_y": True}]],
                    subplot_titles=[language]
                )
                
                # Add bar chart for installs (left axis)
                fig_individual.add_trace(
                    go.Bar(
                        x=combined_data['week'],
                        y=combined_data['installs_count'],
                        name='Installs',
                        marker_color='#1f77b4',
                        text=combined_data['installs_count'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else ""),
                        textposition='outside',
                        hovertemplate='<b>Week:</b> %{x}<br><b>Installs:</b> %{y}<br><b>WoW Change:</b> %{customdata:.1f}%<extra></extra>',
                        customdata=combined_data['wow_change']
                    ),
                    secondary_y=False
                )
                
                # Add line chart for conversion rate (right axis) if data available
                if not views_df.empty and 'conversion_rate' in combined_data.columns:
                    fig_individual.add_trace(
                        go.Scatter(
                            x=combined_data['week'],
                            y=combined_data['conversion_rate'],
                            mode='lines+markers+text',
                            name='Conversion Rate',
                            line=dict(color='#ff7f0e', width=2),
                            marker=dict(size=6),
                            text=combined_data['conversion_rate'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) and x > 0 else ""),
                            textposition='top center',
                            hovertemplate='<b>Week:</b> %{x}<br><b>Conversion Rate:</b> %{y:.2f}%<br><b>Views:</b> %{customdata[0]}<br><b>Installs:</b> %{customdata[1]}<extra></extra>',
                            customdata=list(zip(combined_data['views_count'], combined_data['installs_count']))
                        ),
                        secondary_y=True
                    )
                
                # Update layout
                fig_individual.update_layout(
                    showlegend=True,
                    margin=dict(l=10, r=10, t=80, b=10),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=380,
                    legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.1,
                        xanchor='center',
                        x=0.5
                    )
                )
                
                # Set y-axes titles and adjust range to provide space for labels
                max_installs = combined_data['installs_count'].max() if not combined_data.empty else 100
                fig_individual.update_yaxes(
                    title_text="Installs", 
                    secondary_y=False, 
                    showgrid=False,
                    range=[0, max_installs * 1.15]  # Add 15% padding above max value
                )
                fig_individual.update_yaxes(title_text="Conversion Rate (%)", secondary_y=True, showgrid=False)
                fig_individual.update_xaxes(showgrid=False, title_text=None)
                
                # Alternate between columns
                if i % 2 == 0:
                    with col1:
                        st.plotly_chart(fig_individual, use_container_width=True)
                else:
                    with col2:
                        st.plotly_chart(fig_individual, use_container_width=True)
            
            # Medium Trends - Last 8 completed weeks
            st.subheader('Medium - Last 8 completed weeks')
            
            # Aggregate by date and medium
            medium_daily = language_df.groupby(['event_date', 'medium_aggregated'])['events_count'].sum().reset_index()
            
            # Get all mediums for individual charts
            all_mediums = medium_daily['medium_aggregated'].unique()
            
            # Create combined medium trends chart
            fig_medium_combined = px.line(
                medium_daily,
                x='event_date',
                y='events_count',
                color='medium_aggregated',
                title='Medium - Last 8 completed weeks',
                markers=True
            )
            
            fig_medium_combined.update_layout(
                showlegend=True,
                margin=dict(l=10, r=10, t=30, b=60),
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
            
            fig_medium_combined.update_xaxes(showgrid=False)
            fig_medium_combined.update_yaxes(showgrid=False)
            
            st.plotly_chart(fig_medium_combined, use_container_width=True, config={'displayModeBar': False})
            
            # Individual medium charts with WoW data and conversion rates
            st.subheader('Individual Medium Trends')
            st.caption("📊 Conversion Rate = (Installs from ga_installs ÷ Views from ga_view_app) × 100 by medium and week")
            
            # Create grid layout for medium charts
            cols = st.columns(2)
            
            for i, medium in enumerate(all_mediums):
                # Get installs data for this medium (from ga_installs - last 8 completed weeks)
                installs_medium_data = df[
                    (df['medium_aggregated'] == medium) & 
                    (df['event_date'] >= eight_weeks_ago) & 
                    (df['event_date'] <= last_completed_week_end)
                ].copy()
                installs_medium_data['week'] = installs_medium_data['event_date'].dt.to_period('W').dt.start_time
                installs_weekly = installs_medium_data.groupby('week')['events_count'].sum().reset_index()
                installs_weekly = installs_weekly.rename(columns={'events_count': 'installs_count'})
                
                # Get views data for this medium (from ga_view_app - last 8 completed weeks)
                if not views_df.empty:
                    views_df_processed = views_df.copy()
                    views_df_processed['event_date'] = pd.to_datetime(views_df_processed['event_date'], format='%Y%m%d')
                    views_medium_data = views_df_processed[
                        (views_df_processed['medium_aggregated'] == medium) & 
                        (views_df_processed['event_date'] >= eight_weeks_ago) & 
                        (views_df_processed['event_date'] <= last_completed_week_end)
                    ].copy()
                    views_medium_data['week'] = views_medium_data['event_date'].dt.to_period('W').dt.start_time
                    views_weekly = views_medium_data.groupby('week')['events_count'].sum().reset_index()
                    views_weekly = views_weekly.rename(columns={'events_count': 'views_count'})
                    
                    # Merge installs and views data properly
                    combined_data = pd.merge(installs_weekly, views_weekly, on='week', how='outer').fillna(0)
                    
                    # Calculate proper conversion rate
                    combined_data['conversion_rate'] = combined_data.apply(
                        lambda row: (row['installs_count'] / row['views_count'] * 100) 
                        if row['views_count'] > 0 
                        else 0, axis=1
                    ).round(2)
                else:
                    combined_data = installs_weekly.copy()
                    combined_data['views_count'] = 0
                    combined_data['conversion_rate'] = 0
                
                # Calculate WoW change for installs
                combined_data = combined_data.sort_values('week')
                combined_data['prev_week_installs'] = combined_data['installs_count'].shift(1)
                combined_data['wow_change'] = ((combined_data['installs_count'] - combined_data['prev_week_installs']) / combined_data['prev_week_installs'] * 100).round(1)
                
                # Create subplot with secondary y-axis
                fig_medium_individual = make_subplots(
                    specs=[[{"secondary_y": True}]],
                    subplot_titles=[medium.replace('_', ' ').title()]
                )
                
                # Add bar chart for installs (left axis)
                fig_medium_individual.add_trace(
                    go.Bar(
                        x=combined_data['week'],
                        y=combined_data['installs_count'],
                        name='Installs',
                        marker_color='#2ca02c',
                        text=combined_data['installs_count'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else ""),
                        textposition='outside',
                        hovertemplate='<b>Week:</b> %{x}<br><b>Installs:</b> %{y}<br><b>WoW Change:</b> %{customdata:.1f}%<extra></extra>',
                        customdata=combined_data['wow_change']
                    ),
                    secondary_y=False
                )
                
                # Add line chart for conversion rate (right axis) if data available
                if not views_df.empty and 'conversion_rate' in combined_data.columns:
                    fig_medium_individual.add_trace(
                        go.Scatter(
                            x=combined_data['week'],
                            y=combined_data['conversion_rate'],
                            mode='lines+markers+text',
                            name='Conversion Rate',
                            line=dict(color='#d62728', width=2),
                            marker=dict(size=6),
                            text=combined_data['conversion_rate'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) and x > 0 else ""),
                            textposition='top center',
                            hovertemplate='<b>Week:</b> %{x}<br><b>Conversion Rate:</b> %{y:.2f}%<br><b>Views:</b> %{customdata[0]}<br><b>Installs:</b> %{customdata[1]}<extra></extra>',
                            customdata=list(zip(combined_data['views_count'], combined_data['installs_count']))
                        ),
                        secondary_y=True
                    )
                
                # Update layout
                fig_medium_individual.update_layout(
                    showlegend=True,
                    margin=dict(l=10, r=10, t=80, b=10),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=380,
                    legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.1,
                        xanchor='center',
                        x=0.5
                    )
                )
                
                # Set y-axes titles and adjust range to provide space for labels
                max_installs = combined_data['installs_count'].max() if not combined_data.empty else 100
                fig_medium_individual.update_yaxes(
                    title_text="Installs", 
                    secondary_y=False, 
                    showgrid=False,
                    range=[0, max_installs * 1.15]  # Add 15% padding above max value
                )
                fig_medium_individual.update_yaxes(title_text="Conversion Rate (%)", secondary_y=True, showgrid=False)
                fig_medium_individual.update_xaxes(showgrid=False, title_text=None)
                
                # Alternate between columns
                with cols[i % 2]:
                    st.plotly_chart(fig_medium_individual, use_container_width=True, config={'displayModeBar': False})
            


        
        with organic:
            st.subheader('Organic Traffic Analysis')
            
            # Filter data for organic traffic only
            organic_df = df[df['medium_aggregated'].isin(['organic_search', 'organic_placement', 'organic_uncategorised'])].copy()
            
            if organic_df.empty:
                st.info('No organic traffic data available.')
                return
            
            # Create sub-tabs for different organic categories
            organic_search, organic_explore, organic_uncategorised = st.tabs(['Organic - Search', 'Organic - Explore', 'Organic - Uncategorised'])
            
            with organic_search:
                st.subheader('Organic - Search')
                
                # Filter for organic search only
                search_df = organic_df[organic_df['medium_aggregated'] == 'organic_search'].copy()
                
                if not search_df.empty:
                    # Campaign performance table
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.write("**Campaign Performance**")
                        
                        # Calculate week-over-week changes for campaigns
                        search_df['week'] = search_df['event_date'].dt.to_period('W').dt.start_time
                        
                        # Get last two weeks of data
                        weeks = sorted(search_df['week'].unique())
                        if len(weeks) >= 2:
                            current_week = weeks[-1]
                            previous_week = weeks[-2]
                            
                            current_data = search_df[search_df['week'] == current_week].groupby('campaign_aggregated')['events_count'].sum()
                            previous_data = search_df[search_df['week'] == previous_week].groupby('campaign_aggregated')['events_count'].sum()
                            
                            # Calculate percentage changes
                            campaign_performance = pd.DataFrame({
                                'Campaign': current_data.index,
                                'Installs': current_data.values
                            })
                            
                            # Calculate percentage change
                            pct_changes = []
                            for campaign in current_data.index:
                                if campaign in previous_data.index and previous_data[campaign] > 0:
                                    pct_change = ((current_data[campaign] - previous_data[campaign]) / previous_data[campaign]) * 100
                                    pct_changes.append(f"{pct_change:.1f}%")
                                else:
                                    pct_changes.append("N/A")
                            
                            campaign_performance['% Δ'] = pct_changes
                            campaign_performance = campaign_performance.sort_values('Installs', ascending=False)
                            
                            st.dataframe(campaign_performance, width='stretch', hide_index=True)
                        else:
                            # Fallback if not enough weeks of data
                            campaign_totals = search_df.groupby('campaign_aggregated')['events_count'].sum().reset_index()
                            campaign_totals.columns = ['Campaign', 'Installs']
                            campaign_totals = campaign_totals.sort_values('Installs', ascending=False)
                            st.dataframe(campaign_totals, width='stretch', hide_index=True)
                    
                    with col2:
                        st.write("**Campaign Trends**")
                        
                        # Campaign trends chart
                        campaign_daily = search_df.groupby(['event_date', 'campaign_aggregated'])['events_count'].sum().reset_index()
                        
                        fig_search_trends = px.line(
                            campaign_daily,
                            x='event_date',
                            y='events_count',
                            color='campaign_aggregated',
                            markers=True
                        )
                        
                        fig_search_trends.update_layout(
                            showlegend=True,
                            margin=dict(l=10, r=10, t=10, b=40),
                            xaxis_title=None,
                            yaxis_title=None,
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            height=300,
                            legend=dict(
                                orientation='h',
                                yanchor='top',
                                y=-0.2,
                                xanchor='center',
                                x=0.5
                            )
                        )
                        
                        fig_search_trends.update_xaxes(showgrid=False)
                        fig_search_trends.update_yaxes(showgrid=False)
                        
                        st.plotly_chart(fig_search_trends, use_container_width=True, config={'displayModeBar': False})
                    
                    # Search Keywords section (simulated with campaign details)
                    st.write("**Search Keywords Performance**")
                    
                    # Use campaign_details_aggregated as proxy for keywords, filtered to campaign=search only
                    keywords_df = search_df[
                        (search_df['campaign_details_aggregated'].notna()) & 
                        (search_df['campaign_details_aggregated'] != '') &
                        (search_df['campaign_aggregated'] == 'search')
                    ].copy()
                    
                    if not keywords_df.empty:
                        # Calculate keyword performance with week-over-week changes
                        if len(weeks) >= 2:
                            current_kw_data = keywords_df[keywords_df['week'] == current_week].groupby('campaign_details_aggregated')['events_count'].sum()
                            previous_kw_data = keywords_df[keywords_df['week'] == previous_week].groupby('campaign_details_aggregated')['events_count'].sum()
                            
                            keyword_performance = pd.DataFrame({
                                'Search-KWs': current_kw_data.index,
                                'Installs': current_kw_data.values
                            })
                            
                            # Calculate percentage change for keywords
                            kw_pct_changes = []
                            for keyword in current_kw_data.index:
                                if keyword in previous_kw_data.index and previous_kw_data[keyword] > 0:
                                    pct_change = ((current_kw_data[keyword] - previous_kw_data[keyword]) / previous_kw_data[keyword]) * 100
                                    kw_pct_changes.append(f"{pct_change:.1f}%")
                                else:
                                    kw_pct_changes.append("N/A")
                            
                            keyword_performance['% Δ'] = kw_pct_changes
                            keyword_performance = keyword_performance.sort_values('Installs', ascending=False)
                            
                            st.dataframe(keyword_performance, width='stretch', hide_index=True)
                        else:
                            # Fallback for keywords
                            keyword_totals = keywords_df.groupby('campaign_details_aggregated')['events_count'].sum().reset_index()
                            keyword_totals.columns = ['Search-KWs', 'Installs']
                            keyword_totals = keyword_totals.sort_values('Installs', ascending=False)
                            st.dataframe(keyword_totals, width='stretch', hide_index=True)
                    else:
                        st.info("No keyword data available for organic search.")
                else:
                    st.info("No organic search data available.")
            
            with organic_explore:
                st.subheader('Organic - Explore')
                
                # Filter for organic placement (exploration)
                explore_df = organic_df[organic_df['medium_aggregated'] == 'organic_placement'].copy()
                
                if not explore_df.empty:
                    # Campaign performance for explore
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.write("**Campaign Performance**")
                        
                        explore_df['week'] = explore_df['event_date'].dt.to_period('W').dt.start_time
                        weeks = sorted(explore_df['week'].unique())
                        
                        if len(weeks) >= 2:
                            current_week = weeks[-1]
                            previous_week = weeks[-2]
                            
                            current_explore_data = explore_df[explore_df['week'] == current_week].groupby('campaign_aggregated')['events_count'].sum()
                            previous_explore_data = explore_df[explore_df['week'] == previous_week].groupby('campaign_aggregated')['events_count'].sum()
                            
                            explore_performance = pd.DataFrame({
                                'Campaign': current_explore_data.index,
                                'Installs': current_explore_data.values
                            })
                            
                            # Calculate percentage change
                            explore_pct_changes = []
                            for campaign in current_explore_data.index:
                                if campaign in previous_explore_data.index and previous_explore_data[campaign] > 0:
                                    pct_change = ((current_explore_data[campaign] - previous_explore_data[campaign]) / previous_explore_data[campaign]) * 100
                                    explore_pct_changes.append(f"{pct_change:.1f}%")
                                else:
                                    explore_pct_changes.append("N/A")
                            
                            explore_performance['% Δ'] = explore_pct_changes
                            explore_performance = explore_performance.sort_values('Installs', ascending=False)
                            
                            st.dataframe(explore_performance, width='stretch', hide_index=True)
                        else:
                            explore_totals = explore_df.groupby('campaign_aggregated')['events_count'].sum().reset_index()
                            explore_totals.columns = ['Campaign', 'Installs']
                            explore_totals = explore_totals.sort_values('Installs', ascending=False)
                            st.dataframe(explore_totals, width='stretch', hide_index=True)
                    
                    with col2:
                        st.write("**Campaign Trends**")
                        
                        explore_daily = explore_df.groupby(['event_date', 'campaign_aggregated'])['events_count'].sum().reset_index()
                        
                        fig_explore_trends = px.line(
                            explore_daily,
                            x='event_date',
                            y='events_count',
                            color='campaign_aggregated',
                            markers=True
                        )
                        
                        fig_explore_trends.update_layout(
                            showlegend=True,
                            margin=dict(l=10, r=10, t=10, b=40),
                            xaxis_title=None,
                            yaxis_title=None,
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            height=300,
                            legend=dict(
                                orientation='h',
                                yanchor='top',
                                y=-0.2,
                                xanchor='center',
                                x=0.5
                            )
                        )
                        
                        fig_explore_trends.update_xaxes(showgrid=False)
                        fig_explore_trends.update_yaxes(showgrid=False)
                        
                        st.plotly_chart(fig_explore_trends, use_container_width=True, config={'displayModeBar': False})
                    
                    # Campaign/Placement breakdown
                    st.write("**Campaign/Placement Breakdown**")
                    
                    # Calculate WoW data for placement breakdown
                    if len(weeks) >= 2:
                        current_week = weeks[-1]
                        previous_week = weeks[-2]
                        
                        # Current week placement data
                        current_placement_data = explore_df[explore_df['week'] == current_week].groupby(['campaign_aggregated', 'campaign_details_aggregated'])['events_count'].sum().reset_index()
                        current_placement_data = current_placement_data[current_placement_data['campaign_details_aggregated'].notna() & 
                                                                      (current_placement_data['campaign_details_aggregated'] != '')]
                        current_placement_data.columns = ['Campaign', 'Placement', 'Current_Installs']
                        
                        # Previous week placement data
                        previous_placement_data = explore_df[explore_df['week'] == previous_week].groupby(['campaign_aggregated', 'campaign_details_aggregated'])['events_count'].sum().reset_index()
                        previous_placement_data = previous_placement_data[previous_placement_data['campaign_details_aggregated'].notna() & 
                                                                        (previous_placement_data['campaign_details_aggregated'] != '')]
                        previous_placement_data.columns = ['Campaign', 'Placement', 'Previous_Installs']
                        
                        # Merge current and previous data
                        placement_df = pd.merge(current_placement_data, previous_placement_data, on=['Campaign', 'Placement'], how='left')
                        placement_df['Previous_Installs'] = placement_df['Previous_Installs'].fillna(0)
                        
                        # Calculate WoW delta and percentage
                        placement_df['WoW_Delta'] = placement_df['Current_Installs'] - placement_df['Previous_Installs']
                        placement_df['WoW_Percent'] = ((placement_df['Current_Installs'] - placement_df['Previous_Installs']) / 
                                                      placement_df['Previous_Installs'].replace(0, 1) * 100).round(1)
                        
                        # Handle cases where previous week had 0 installs
                        placement_df.loc[placement_df['Previous_Installs'] == 0, 'WoW_Percent'] = None
                        
                        # Format for display
                        placement_df = placement_df.sort_values('Current_Installs', ascending=False)
                        
                        # Create display table
                        display_placement_df = placement_df[['Campaign', 'Placement', 'Current_Installs', 'WoW_Delta', 'WoW_Percent']].copy()
                        display_placement_df.columns = ['Campaign', 'Placement', 'Installs', 'WoW Δ', 'WoW %']
                        
                        # Format the WoW % column
                        display_placement_df['WoW %'] = display_placement_df['WoW %'].apply(
                            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
                        )
                        
                        if not display_placement_df.empty:
                            st.dataframe(display_placement_df, width='stretch', hide_index=True)
                        else:
                            st.info("No detailed placement data available.")
                    else:
                        # Fallback if not enough weeks of data
                        placement_df = explore_df.groupby(['campaign_aggregated', 'campaign_details_aggregated'])['events_count'].sum().reset_index()
                        placement_df = placement_df[placement_df['campaign_details_aggregated'].notna() & 
                                                  (placement_df['campaign_details_aggregated'] != '')]
                        placement_df.columns = ['Campaign', 'Placement', 'Installs']
                        placement_df = placement_df.sort_values('Installs', ascending=False)
                        
                        if not placement_df.empty:
                            st.dataframe(placement_df, width='stretch', hide_index=True)
                        else:
                            st.info("No detailed placement data available.")
                    
                    # Additional breakdowns in columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Category Breakdown**")
                        
                        if len(weeks) >= 2:
                            current_week = weeks[-1]
                            previous_week = weeks[-2]
                            
                            # Current week category data
                            current_category_data = explore_df[explore_df['week'] == current_week].groupby('surface_type_parsed')['events_count'].sum().reset_index()
                            current_category_data = current_category_data[current_category_data['surface_type_parsed'].notna()]
                            current_category_data.columns = ['Category', 'Current_Installs']
                            
                            # Previous week category data
                            previous_category_data = explore_df[explore_df['week'] == previous_week].groupby('surface_type_parsed')['events_count'].sum().reset_index()
                            previous_category_data = previous_category_data[previous_category_data['surface_type_parsed'].notna()]
                            previous_category_data.columns = ['Category', 'Previous_Installs']
                            
                            # Merge and calculate WoW
                            category_df = pd.merge(current_category_data, previous_category_data, on='Category', how='left')
                            category_df['Previous_Installs'] = category_df['Previous_Installs'].fillna(0)
                            category_df['WoW_Delta'] = category_df['Current_Installs'] - category_df['Previous_Installs']
                            category_df['WoW_Percent'] = ((category_df['Current_Installs'] - category_df['Previous_Installs']) / 
                                                         category_df['Previous_Installs'].replace(0, 1) * 100).round(1)
                            category_df.loc[category_df['Previous_Installs'] == 0, 'WoW_Percent'] = None
                            
                            # Format for display
                            category_df = category_df.sort_values('Current_Installs', ascending=False)
                            display_category_df = category_df[['Category', 'Current_Installs', 'WoW_Delta', 'WoW_Percent']].copy()
                            display_category_df.columns = ['Category', 'Installs', 'WoW Δ', 'WoW %']
                            display_category_df['WoW %'] = display_category_df['WoW %'].apply(
                                lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
                            )
                            
                            if not display_category_df.empty:
                                st.dataframe(display_category_df, width='stretch', hide_index=True)
                            else:
                                st.info("No category data available.")
                        else:
                            # Fallback if not enough weeks of data
                            category_df = explore_df.groupby('surface_type_parsed')['events_count'].sum().reset_index()
                            category_df = category_df[category_df['surface_type_parsed'].notna()]
                            category_df.columns = ['Category', 'Installs']
                            category_df = category_df.sort_values('Installs', ascending=False)
                            
                            if not category_df.empty:
                                st.dataframe(category_df, width='stretch', hide_index=True)
                            else:
                                st.info("No category data available.")
                    
                    with col2:
                        st.write("**Story Breakdown**")
                        
                        if len(weeks) >= 2:
                            current_week = weeks[-1]
                            previous_week = weeks[-2]
                            
                            # Current week story data
                            current_story_data = explore_df[explore_df['week'] == current_week].groupby('surface_detail_parsed')['events_count'].sum().reset_index()
                            current_story_data = current_story_data[current_story_data['surface_detail_parsed'].notna()]
                            current_story_data.columns = ['Story', 'Current_Installs']
                            
                            # Previous week story data
                            previous_story_data = explore_df[explore_df['week'] == previous_week].groupby('surface_detail_parsed')['events_count'].sum().reset_index()
                            previous_story_data = previous_story_data[previous_story_data['surface_detail_parsed'].notna()]
                            previous_story_data.columns = ['Story', 'Previous_Installs']
                            
                            # Merge and calculate WoW
                            story_df = pd.merge(current_story_data, previous_story_data, on='Story', how='left')
                            story_df['Previous_Installs'] = story_df['Previous_Installs'].fillna(0)
                            story_df['WoW_Delta'] = story_df['Current_Installs'] - story_df['Previous_Installs']
                            story_df['WoW_Percent'] = ((story_df['Current_Installs'] - story_df['Previous_Installs']) / 
                                                      story_df['Previous_Installs'].replace(0, 1) * 100).round(1)
                            story_df.loc[story_df['Previous_Installs'] == 0, 'WoW_Percent'] = None
                            
                            # Format for display
                            story_df = story_df.sort_values('Current_Installs', ascending=False)
                            display_story_df = story_df[['Story', 'Current_Installs', 'WoW_Delta', 'WoW_Percent']].copy()
                            display_story_df.columns = ['Story', 'Installs', 'WoW Δ', 'WoW %']
                            display_story_df['WoW %'] = display_story_df['WoW %'].apply(
                                lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
                            )
                            
                            if not display_story_df.empty:
                                st.dataframe(display_story_df, width='stretch', hide_index=True)
                            else:
                                st.info("No story data available.")
                        else:
                            # Fallback if not enough weeks of data
                            story_df = explore_df.groupby('surface_detail_parsed')['events_count'].sum().reset_index()
                            story_df = story_df[story_df['surface_detail_parsed'].notna()]
                            story_df.columns = ['Story', 'Installs']
                            story_df = story_df.sort_values('Installs', ascending=False)
                            
                            if not story_df.empty:
                                st.dataframe(story_df, width='stretch', hide_index=True)
                            else:
                                st.info("No story data available.")
                else:
                    st.info("No organic explore data available.")
            
            with organic_uncategorised:
                st.subheader('Organic - Uncategorised (check - disregard)')
                
                # Filter for uncategorised organic traffic
                uncategorised_df = organic_df[organic_df['medium_aggregated'] == 'organic_uncategorised'].copy()
                
                if not uncategorised_df.empty:
                    # Show raw data for investigation
                    st.write("**Raw Data for Investigation**")
                    
                    # Select relevant columns for analysis
                    analysis_columns = [
                        'st_source_parsed', 'surface_type_parsed', 'surface_detail_parsed',
                        'utm_medium_parsed', 'utm_source_parsed', 'st_campaign_parsed',
                        'events_count'
                    ]
                    
                    # Aggregate by the analysis columns
                    uncategorised_summary = uncategorised_df.groupby([col for col in analysis_columns if col != 'events_count'])['events_count'].sum().reset_index()
                    uncategorised_summary = uncategorised_summary.sort_values('events_count', ascending=False)
                    
                    # Rename columns for display
                    display_columns = {
                        'st_source_parsed': 'Surface Source',
                        'surface_type_parsed': 'Surface Type',
                        'surface_detail_parsed': 'Surface Detail',
                        'utm_medium_parsed': 'UTM Medium',
                        'utm_source_parsed': 'UTM Source',
                        'st_campaign_parsed': 'ST Campaign',
                        'events_count': 'Achievement ID / Event count'
                    }
                    
                    uncategorised_summary = uncategorised_summary.rename(columns=display_columns)
                    
                    st.dataframe(uncategorised_summary, width='stretch', hide_index=True)
                    
                    # Summary stats
                    total_uncategorised = uncategorised_summary['Achievement ID / Event count'].sum()
                    st.metric("Total Uncategorised Events", f"{total_uncategorised:,}")
                else:
                    st.info("No uncategorised organic data available.")
        
        with organic_trends:
            st.subheader('Organic Trends Analysis')
            
            # Filter data for organic traffic only
            organic_trends_df = df[df['medium_aggregated'].isin(['organic_search', 'organic_placement'])].copy()
            
            if organic_trends_df.empty:
                st.info('No organic trends data available.')
                return
            
            # Filter to last 30 days for trends
            last_30_days = organic_trends_df['event_date'] >= (organic_trends_df['event_date'].max() - pd.Timedelta(days=30))
            organic_trends_df = organic_trends_df[last_30_days].copy()
            
            # Organic Search Trends - Last 30 Days
            st.subheader('Organic_Search - Last 30 Days')
            
            search_trends_df = organic_trends_df[organic_trends_df['medium_aggregated'] == 'organic_search'].copy()
            
            if not search_trends_df.empty:
                # Aggregate by date and campaign for organic search
                search_daily = search_trends_df.groupby(['event_date', 'campaign_aggregated'])['events_count'].sum().reset_index()
                
                # Create the organic search trends chart
                fig_organic_search = px.line(
                    search_daily,
                    x='event_date',
                    y='events_count',
                    color='campaign_aggregated',
                    title='Organic_Search - Last 30 Days',
                    markers=True
                )
                
                # Update layout to match the style in the image
                fig_organic_search.update_layout(
                    showlegend=True,
                    margin=dict(l=10, r=10, t=30, b=60),
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
                
                fig_organic_search.update_xaxes(showgrid=False)
                fig_organic_search.update_yaxes(showgrid=False)
                
                st.plotly_chart(fig_organic_search, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No organic search trends data available.")
            
            # Organic Explore Trends - Last 30 Days
            st.subheader('Organic_Explore - Last 30 Days')
            
            explore_trends_df = organic_trends_df[organic_trends_df['medium_aggregated'] == 'organic_placement'].copy()
            
            # Initialize color_column for later use
            color_column = 'campaign_aggregated'  # default
            
            if not explore_trends_df.empty:
                # For organic explore, we'll use different dimensions based on available data
                # First, let's try campaign_aggregated, then fall back to surface_type_parsed
                
                # Check if we have meaningful campaign data
                campaign_data = explore_trends_df.groupby(['event_date', 'campaign_aggregated'])['events_count'].sum().reset_index()
                campaign_counts = campaign_data['campaign_aggregated'].value_counts()
                
                # If we have good campaign diversity, use campaigns
                if len(campaign_counts) > 1 and campaign_counts.iloc[0] < len(campaign_data) * 0.8:
                    explore_daily = campaign_data
                    color_column = 'campaign_aggregated'
                else:
                    # Otherwise use surface_type as it represents different placement types
                    explore_daily = explore_trends_df.groupby(['event_date', 'surface_type_parsed'])['events_count'].sum().reset_index()
                    explore_daily = explore_daily[explore_daily['surface_type_parsed'].notna()]
                    color_column = 'surface_type_parsed'
                
                if not explore_daily.empty:
                    # Create the organic explore trends chart
                    fig_organic_explore = px.line(
                        explore_daily,
                        x='event_date',
                        y='events_count',
                        color=color_column,
                        title='Organic_Explore - Last 30 Days',
                        markers=True
                    )
                    
                    # Update layout to match the style in the image
                    fig_organic_explore.update_layout(
                        showlegend=True,
                        margin=dict(l=10, r=10, t=30, b=60),
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
                    
                    fig_organic_explore.update_xaxes(showgrid=False)
                    fig_organic_explore.update_yaxes(showgrid=False)
                    
                    st.plotly_chart(fig_organic_explore, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No meaningful organic explore trends data available.")
            else:
                st.info("No organic explore trends data available.")
            
            # Additional trend analysis
            st.subheader('Organic Traffic Summary')
            
            # Create summary metrics for the last 30 days
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_organic_search = search_trends_df['events_count'].sum() if not search_trends_df.empty else 0
                st.metric("Total Organic Search Events", f"{total_organic_search:,}")
            
            with col2:
                total_organic_explore = explore_trends_df['events_count'].sum() if not explore_trends_df.empty else 0
                st.metric("Total Organic Explore Events", f"{total_organic_explore:,}")
            
            with col3:
                total_organic = total_organic_search + total_organic_explore
                st.metric("Total Organic Events", f"{total_organic:,}")
            
            # Show top performing campaigns/sources for each organic type
            if not search_trends_df.empty or not explore_trends_df.empty:
                st.subheader('Top Performers - Last 30 Days')
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Top Organic Search Campaigns**")
                    if not search_trends_df.empty:
                        top_search = search_trends_df.groupby('campaign_aggregated')['events_count'].sum().sort_values(ascending=False).head(5)
                        search_df_display = pd.DataFrame({
                            'Campaign': top_search.index,
                            'Events': top_search.values
                        })
                        st.dataframe(search_df_display, width='stretch', hide_index=True)
                    else:
                        st.info("No search data available")
                
                with col2:
                    st.write("**Top Organic Explore Sources**")
                    if not explore_trends_df.empty:
                        # Use the same logic as the chart for consistency
                        if color_column == 'campaign_aggregated':
                            top_explore = explore_trends_df.groupby('campaign_aggregated')['events_count'].sum().sort_values(ascending=False).head(5)
                            explore_df_display = pd.DataFrame({
                                'Campaign': top_explore.index,
                                'Events': top_explore.values
                            })
                        else:
                            top_explore = explore_trends_df.groupby('surface_type_parsed')['events_count'].sum().sort_values(ascending=False).head(5)
                            explore_df_display = pd.DataFrame({
                                'Surface Type': top_explore.index,
                                'Events': top_explore.values
                            })
                        st.dataframe(explore_df_display, width='stretch', hide_index=True)
                    else:
                        st.info("No explore data available")
        
        with partner:
            st.subheader('Partner Traffic Analysis')
            st.write("*Partner traffic from Shopify App Store partners section*")
            
            # Filter data for partner traffic - looking for partners surface type in organic placement
            # Based on actual data structure, partner traffic comes through Shopify partners page
            partner_df = df[
                (df['surface_type_parsed'] == 'partners') | 
                (df['campaign_aggregated'] == 'partners')
            ].copy()
            
            # Also get partner views data
            partner_views_df = pd.DataFrame()
            if not views_df.empty:
                partner_views_df = views_df[
                    (views_df['surface_type_parsed'] == 'partners') | 
                    (views_df['campaign_aggregated'] == 'partners')
                ].copy()
            
            if partner_df.empty and partner_views_df.empty:
                st.info('No partner traffic data available.')
                st.write("""
                **Note**: Partner traffic is identified by:
                - `surface_type_parsed = 'partners'` (Shopify Partners page)
                - `campaign_aggregated = 'partners'`
                
                This traffic typically comes from the Shopify App Store partners section.
                """)
                return
            
            # Partner Trends by Source - Last 6 months
            st.subheader('Partner Trends by Source - Last 6 months')
            
            # Filter to last 6 months (approximately 180 days)
            six_months_ago = df['event_date'].max() - pd.Timedelta(days=180)
            
            # Filter partner data for last 6 months
            partner_trends_df = partner_df[partner_df['event_date'] >= six_months_ago].copy()
            partner_views_trends_df = partner_views_df[partner_views_df['event_date'] >= six_months_ago].copy() if not partner_views_df.empty else pd.DataFrame()
            
            if not partner_trends_df.empty:
                # Create trend lines by source
                source_daily = partner_trends_df.groupby(['event_date', 'source_aggregated'])['events_count'].sum().reset_index()
                
                fig_partner_sources = px.line(
                    source_daily,
                    x='event_date',
                    y='events_count',
                    color='source_aggregated',
                    title='Partner Traffic by Source - Last 6 months',
                    markers=True
                )
                
                fig_partner_sources.update_layout(
                    showlegend=True,
                    margin=dict(l=10, r=10, t=30, b=60),
                    xaxis_title=None,
                    yaxis_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=500,
                    legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.15,
                        xanchor='center',
                        x=0.5
                    )
                )
                
                fig_partner_sources.update_xaxes(showgrid=False)
                fig_partner_sources.update_yaxes(showgrid=False)
                
                st.plotly_chart(fig_partner_sources, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No partner data available for the last 6 months.")
            
            # Partner Performance Table - Last Week with Previous Period Comparison
            st.subheader('Partner Performance - Last Week vs Previous Week')
            
            # Calculate week boundaries
            latest_date = df['event_date'].max()
            current_week_start = latest_date - pd.Timedelta(days=latest_date.weekday())  # Start of current week (Monday)
            last_week_start = current_week_start - pd.Timedelta(days=7)
            last_week_end = current_week_start - pd.Timedelta(days=1)
            previous_week_start = last_week_start - pd.Timedelta(days=7)
            previous_week_end = last_week_start - pd.Timedelta(days=1)
            
            # Filter data for last week and previous week
            last_week_installs = partner_df[
                (partner_df['event_date'] >= last_week_start) & 
                (partner_df['event_date'] <= last_week_end)
            ].copy()
            
            previous_week_installs = partner_df[
                (partner_df['event_date'] >= previous_week_start) & 
                (partner_df['event_date'] <= previous_week_end)
            ].copy()
            
            last_week_views = partner_views_df[
                (partner_views_df['event_date'] >= last_week_start) & 
                (partner_views_df['event_date'] <= last_week_end)
            ].copy() if not partner_views_df.empty else pd.DataFrame()
            
            previous_week_views = partner_views_df[
                (partner_views_df['event_date'] >= previous_week_start) & 
                (partner_views_df['event_date'] <= previous_week_end)
            ].copy() if not partner_views_df.empty else pd.DataFrame()
            
            # Create performance comparison table
            performance_data = []
            
            # Get all unique sources from both weeks
            all_sources = set()
            if not last_week_installs.empty:
                all_sources.update(last_week_installs['source_aggregated'].unique())
            if not previous_week_installs.empty:
                all_sources.update(previous_week_installs['source_aggregated'].unique())
            if not last_week_views.empty:
                all_sources.update(last_week_views['source_aggregated'].unique())
            if not previous_week_views.empty:
                all_sources.update(previous_week_views['source_aggregated'].unique())
            
            for source in all_sources:
                # Calculate metrics for last week
                lw_installs = last_week_installs[last_week_installs['source_aggregated'] == source]['events_count'].sum()
                lw_views = last_week_views[last_week_views['source_aggregated'] == source]['events_count'].sum() if not last_week_views.empty else 0
                
                # Calculate metrics for previous week
                pw_installs = previous_week_installs[previous_week_installs['source_aggregated'] == source]['events_count'].sum()
                pw_views = previous_week_views[previous_week_views['source_aggregated'] == source]['events_count'].sum() if not previous_week_views.empty else 0
                
                # Calculate deltas
                installs_delta = lw_installs - pw_installs
                views_delta = lw_views - pw_views
                
                # Calculate percentage changes
                installs_pct = (installs_delta / pw_installs * 100) if pw_installs > 0 else 0
                views_pct = (views_delta / pw_views * 100) if pw_views > 0 else 0
                
                # Calculate conversion rates
                lw_conversion = (lw_installs / lw_views * 100) if lw_views > 0 else 0
                pw_conversion = (pw_installs / pw_views * 100) if pw_views > 0 else 0
                conversion_delta = lw_conversion - pw_conversion
                
                performance_data.append({
                    'Source': source,
                    'Page Views': f"{lw_views:,}",
                    'Page Views Δ': f"{views_delta:+,} ({views_pct:+.1f}%)" if pw_views > 0 else f"{views_delta:+,}",
                    'Installs': f"{lw_installs:,}",
                    'Installs Δ': f"{installs_delta:+,} ({installs_pct:+.1f}%)" if pw_installs > 0 else f"{installs_delta:+,}",
                    'Conversion Rate': f"{lw_conversion:.2f}%",
                    'Conversion Δ': f"{conversion_delta:+.2f}%" if pw_views > 0 and lw_views > 0 else "N/A"
                })
            
            if performance_data:
                performance_df = pd.DataFrame(performance_data)
                performance_df = performance_df.sort_values('Installs', key=lambda x: x.str.replace(',', '').astype(int), ascending=False)
                
                st.dataframe(performance_df, width='stretch', hide_index=True)
                
                # Summary metrics
                st.subheader('Partner Summary - Last Week')
                
                col1, col2, col3, col4 = st.columns(4)
                
                total_lw_views = last_week_views['events_count'].sum() if not last_week_views.empty else 0
                total_pw_views = previous_week_views['events_count'].sum() if not previous_week_views.empty else 0
                total_lw_installs = last_week_installs['events_count'].sum() if not last_week_installs.empty else 0
                total_pw_installs = previous_week_installs['events_count'].sum() if not previous_week_installs.empty else 0
                
                views_change = total_lw_views - total_pw_views
                installs_change = total_lw_installs - total_pw_installs
                
                overall_lw_conversion = (total_lw_installs / total_lw_views * 100) if total_lw_views > 0 else 0
                overall_pw_conversion = (total_pw_installs / total_pw_views * 100) if total_pw_views > 0 else 0
                conversion_change = overall_lw_conversion - overall_pw_conversion
                
                with col1:
                    st.metric("Total Page Views", f"{total_lw_views:,}", delta=(int(views_change) if pd.notna(views_change) else None))
                
                with col2:
                    st.metric("Total Installs", f"{total_lw_installs:,}", delta=(int(installs_change) if pd.notna(installs_change) else None))
                
                with col3:
                    st.metric("Overall Conversion Rate", f"{overall_lw_conversion:.2f}%", delta=f"{conversion_change:.2f}%")
                
                with col4:
                    partner_sources_count = len(all_sources)
                    st.metric("Active Partner Sources", partner_sources_count)
            else:
                st.info("No partner performance data available for the selected time periods.")
        
        with paid:
            st.subheader('Paid Traffic Analysis')
            
            # Filter data for paid traffic
            # Note: Based on actual data analysis, there's currently no paid_search traffic in the dataset
            # This section will show a message about data availability
            paid_df = df[df['medium_aggregated'] == 'paid_search'].copy()
            
            # Also get paid views data
            paid_views_df = pd.DataFrame()
            if not views_df.empty:
                paid_views_df = views_df[views_df['medium_aggregated'] == 'paid_search'].copy()
            
            if paid_df.empty and paid_views_df.empty:
                st.info('No paid search traffic data available in the current dataset.')
                st.write("""
                **Note**: The current Google Analytics data doesn't contain any paid search traffic 
                (`medium_aggregated = 'paid_search'`). This could mean:
                
                - No paid campaigns are currently running
                - Paid traffic is classified differently in the data
                - Paid campaigns haven't generated significant traffic yet
                
                Once paid search campaigns are active and generating data, this section will display:
                - Campaign performance trends
                - Cost per click (CPC) and cost per acquisition (CPA) metrics  
                - Week-over-week performance comparisons
                - Top performing paid campaigns
                """)
                return
            
            # Paid Keywords Trends - Last 6 months (Top 10)
            st.subheader('Paid Keywords Trends - Last 6 months (Top 10)')
            
            # Filter to last 6 months (approximately 180 days)
            six_months_ago = df['event_date'].max() - pd.Timedelta(days=180)
            
            # Filter paid data for last 6 months
            paid_trends_df = paid_df[paid_df['event_date'] >= six_months_ago].copy()
            paid_views_trends_df = paid_views_df[paid_views_df['event_date'] >= six_months_ago].copy() if not paid_views_df.empty else pd.DataFrame()
            
            if not paid_trends_df.empty:
                # Get top 10 keywords/campaigns by total installs
                top_keywords = paid_trends_df.groupby('campaign_aggregated')['events_count'].sum().nlargest(10).index.tolist()
                
                # Filter data to top 10 keywords only
                top_keywords_df = paid_trends_df[paid_trends_df['campaign_aggregated'].isin(top_keywords)]
                
                # Create trend lines by keywords
                keyword_daily = top_keywords_df.groupby(['event_date', 'campaign_aggregated'])['events_count'].sum().reset_index()
                
                fig_paid_keywords = px.line(
                    keyword_daily,
                    x='event_date',
                    y='events_count',
                    color='campaign_aggregated',
                    title='Top 10 Paid Keywords/Campaigns - Last 6 months',
                    markers=True
                )
                
                fig_paid_keywords.update_layout(
                    showlegend=True,
                    margin=dict(l=10, r=10, t=30, b=60),
                    xaxis_title=None,
                    yaxis_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=500,
                    legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.15,
                        xanchor='center',
                        x=0.5
                    )
                )
                
                fig_paid_keywords.update_xaxes(showgrid=False)
                fig_paid_keywords.update_yaxes(showgrid=False)
                
                st.plotly_chart(fig_paid_keywords, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No paid keywords data available for the last 6 months.")
            
            # Paid Keywords Performance Table - Last Week vs Previous Week
            st.subheader('Paid Keywords Performance - Last Week vs Previous Week')
            
            # Calculate week boundaries
            latest_date = df['event_date'].max()
            current_week_start = latest_date - pd.Timedelta(days=latest_date.weekday())
            last_week_start = current_week_start - pd.Timedelta(days=7)
            last_week_end = current_week_start - pd.Timedelta(days=1)
            previous_week_start = last_week_start - pd.Timedelta(days=7)
            previous_week_end = last_week_start - pd.Timedelta(days=1)
            
            # Filter data for last week and previous week
            last_week_paid_installs = paid_df[
                (paid_df['event_date'] >= last_week_start) & 
                (paid_df['event_date'] <= last_week_end)
            ].copy()
            
            previous_week_paid_installs = paid_df[
                (paid_df['event_date'] >= previous_week_start) & 
                (paid_df['event_date'] <= previous_week_end)
            ].copy()
            
            last_week_paid_views = paid_views_df[
                (paid_views_df['event_date'] >= last_week_start) & 
                (paid_views_df['event_date'] <= last_week_end)
            ].copy() if not paid_views_df.empty else pd.DataFrame()
            
            previous_week_paid_views = paid_views_df[
                (paid_views_df['event_date'] >= previous_week_start) & 
                (paid_views_df['event_date'] <= previous_week_end)
            ].copy() if not paid_views_df.empty else pd.DataFrame()
            
            # Create performance comparison table by campaign
            paid_performance_data = []
            
            # Get all unique campaigns from both weeks
            all_campaigns = set()
            if not last_week_paid_installs.empty:
                all_campaigns.update(last_week_paid_installs['campaign_aggregated'].unique())
            if not previous_week_paid_installs.empty:
                all_campaigns.update(previous_week_paid_installs['campaign_aggregated'].unique())
            if not last_week_paid_views.empty:
                all_campaigns.update(last_week_paid_views['campaign_aggregated'].unique())
            if not previous_week_paid_views.empty:
                all_campaigns.update(previous_week_paid_views['campaign_aggregated'].unique())
            
            for campaign in all_campaigns:
                # Calculate metrics for last week
                lw_installs = last_week_paid_installs[last_week_paid_installs['campaign_aggregated'] == campaign]['events_count'].sum()
                lw_views = last_week_paid_views[last_week_paid_views['campaign_aggregated'] == campaign]['events_count'].sum() if not last_week_paid_views.empty else 0
                
                # Calculate metrics for previous week
                pw_installs = previous_week_paid_installs[previous_week_paid_installs['campaign_aggregated'] == campaign]['events_count'].sum()
                pw_views = previous_week_paid_views[previous_week_paid_views['campaign_aggregated'] == campaign]['events_count'].sum() if not previous_week_paid_views.empty else 0
                
                # Calculate deltas
                installs_delta = lw_installs - pw_installs
                views_delta = lw_views - pw_views
                
                # Calculate percentage changes
                installs_pct = (installs_delta / pw_installs * 100) if pw_installs > 0 else 0
                views_pct = (views_delta / pw_views * 100) if pw_views > 0 else 0
                
                # Calculate conversion rates
                lw_conversion = (lw_installs / lw_views * 100) if lw_views > 0 else 0
                pw_conversion = (pw_installs / pw_views * 100) if pw_views > 0 else 0
                conversion_delta = lw_conversion - pw_conversion
                
                # Calculate cost metrics (simulated - would need actual cost data)
                # For now, we'll show placeholder values
                cpc = "N/A"  # Cost per click
                cpa = "N/A"  # Cost per acquisition
                
                paid_performance_data.append({
                    'Keywords': campaign,
                    'Page Views': f"{lw_views:,}",
                    'Page Views Δ': f"{views_delta:+,} ({views_pct:+.1f}%)" if pw_views > 0 else f"{views_delta:+,}",
                    'Installs': f"{lw_installs:,}",
                    'Installs Δ': f"{installs_delta:+,} ({installs_pct:+.1f}%)" if pw_installs > 0 else f"{installs_delta:+,}",
                    'Conversion Rate': f"{lw_conversion:.2f}%",
                    'Conversion Δ': f"{conversion_delta:+.2f}%" if pw_views > 0 and lw_views > 0 else "N/A"
                })
            
            if paid_performance_data:
                paid_performance_df = pd.DataFrame(paid_performance_data)
                paid_performance_df = paid_performance_df.sort_values('Installs', key=lambda x: x.str.replace(',', '').astype(int), ascending=False)
                
                st.dataframe(paid_performance_df, width='stretch', hide_index=True)
                
                # Summary metrics
                st.subheader('Paid Summary - Last Week')
                
                col1, col2, col3, col4 = st.columns(4)
                
                total_lw_clicks = last_week_paid_views['events_count'].sum() if not last_week_paid_views.empty else 0
                total_pw_clicks = previous_week_paid_views['events_count'].sum() if not previous_week_paid_views.empty else 0
                total_lw_installs = last_week_paid_installs['events_count'].sum() if not last_week_paid_installs.empty else 0
                total_pw_installs = previous_week_paid_installs['events_count'].sum() if not previous_week_paid_installs.empty else 0
                
                clicks_change = total_lw_clicks - total_pw_clicks
                installs_change = total_lw_installs - total_pw_installs
                
                overall_lw_cvr = (total_lw_installs / total_lw_clicks * 100) if total_lw_clicks > 0 else 0
                overall_pw_cvr = (total_pw_installs / total_pw_clicks * 100) if total_pw_clicks > 0 else 0
                cvr_change = overall_lw_cvr - overall_pw_cvr
                
                with col1:
                    st.metric("Total Clicks", f"{total_lw_clicks:,}", delta=(int(clicks_change) if pd.notna(clicks_change) else None))
                
                with col2:
                    st.metric("Total Installs", f"{total_lw_installs:,}", delta=(int(installs_change) if pd.notna(installs_change) else None))
                
                with col3:
                    st.metric("Overall CVR", f"{overall_lw_cvr:.2f}%", delta=f"{cvr_change:.2f}%")
                
                with col4:
                    active_campaigns = len(all_campaigns)
                    st.metric("Active Campaigns", active_campaigns)
            else:
                st.info("No paid performance data available for the selected time periods.")
            
            # Campaign Performance Analysis
            st.subheader('Top Performing Campaigns - Last 30 Days')
            
            # Filter to last 30 days
            thirty_days_ago = df['event_date'].max() - pd.Timedelta(days=30)
            paid_30d_df = paid_df[paid_df['event_date'] >= thirty_days_ago].copy()
            
            if not paid_30d_df.empty:
                # Top campaigns by installs
                top_campaigns = paid_30d_df.groupby('campaign_aggregated')['events_count'].sum().sort_values(ascending=False).head(10)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Top Campaigns by Installs**")
                    top_campaigns_df = pd.DataFrame({
                        'Campaign': top_campaigns.index,
                        'Installs': top_campaigns.values
                    })
                    st.dataframe(top_campaigns_df, width='stretch', hide_index=True)
                
                with col2:
                    st.write("**Campaign Performance Chart**")
                    fig_top_campaigns = px.bar(
                        top_campaigns_df.head(5),
                        x='Installs',
                        y='Campaign',
                        orientation='h',
                        title='Top 5 Campaigns by Installs'
                    )
                    
                    fig_top_campaigns.update_layout(
                        showlegend=False,
                        margin=dict(l=10, r=10, t=30, b=10),
                        xaxis_title=None,
                        yaxis_title=None,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        height=300
                    )
                    
                    fig_top_campaigns.update_xaxes(showgrid=False)
                    fig_top_campaigns.update_yaxes(showgrid=False)
                    
                    st.plotly_chart(fig_top_campaigns, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No paid campaign data available for the last 30 days.")
        
        with website:
            st.subheader('Website Traffic Analysis')
            
            # Filter data for website traffic
            website_df = df[df['medium_aggregated'] == 'website'].copy()
            
            # Also get website views data
            website_views_df = pd.DataFrame()
            if not views_df.empty:
                website_views_df = views_df[views_df['medium_aggregated'] == 'website'].copy()
            
            if website_df.empty and website_views_df.empty:
                st.info('No website traffic data available.')
                return
            
            # Website Traffic Trend by Source
            st.subheader('Website Traffic Trend by Source')
            
            # Note: Based on data analysis, website traffic all comes from 'judgeme' source
            # So we'll show trend by campaign/page type instead for more meaningful insights
            
            if not website_df.empty:
                # Create trend line by campaign (page type) since source is always 'judgeme'
                campaign_daily = website_df.groupby(['event_date', 'campaign_aggregated'])['events_count'].sum().reset_index()
                
                fig_website_trend = px.line(
                    campaign_daily,
                    x='event_date',
                    y='events_count',
                    color='campaign_aggregated',
                    title='Website Traffic Trend by Page Type (Source: Judge.me)',
                    markers=True
                )
                
                fig_website_trend.update_layout(
                    showlegend=True,
                    margin=dict(l=10, r=10, t=30, b=60),
                    xaxis_title=None,
                    yaxis_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=500,
                    legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.15,
                        xanchor='center',
                        x=0.5
                    )
                )
                
                fig_website_trend.update_xaxes(showgrid=False)
                fig_website_trend.update_yaxes(showgrid=False)
                
                st.plotly_chart(fig_website_trend, use_container_width=True, config={'displayModeBar': False})
                
                # Add note about data structure
                st.info("**Note**: All website traffic comes from 'judgeme' source, so the chart shows trends by page type for more meaningful analysis.")
            else:
                st.info("No website data available.")
            
            # Website Performance Table - Last Week with Previous Period Comparison
            st.subheader('Website Performance - Last Week vs Previous Week')
            
            # Calculate week boundaries
            latest_date = df['event_date'].max()
            current_week_start = latest_date - pd.Timedelta(days=latest_date.weekday())
            last_week_start = current_week_start - pd.Timedelta(days=7)
            last_week_end = current_week_start - pd.Timedelta(days=1)
            previous_week_start = last_week_start - pd.Timedelta(days=7)
            previous_week_end = last_week_start - pd.Timedelta(days=1)
            
            # Filter data for last week and previous week
            last_week_website_installs = website_df[
                (website_df['event_date'] >= last_week_start) & 
                (website_df['event_date'] <= last_week_end)
            ].copy()
            
            previous_week_website_installs = website_df[
                (website_df['event_date'] >= previous_week_start) & 
                (website_df['event_date'] <= previous_week_end)
            ].copy()
            
            last_week_website_views = website_views_df[
                (website_views_df['event_date'] >= last_week_start) & 
                (website_views_df['event_date'] <= last_week_end)
            ].copy() if not website_views_df.empty else pd.DataFrame()
            
            previous_week_website_views = website_views_df[
                (website_views_df['event_date'] >= previous_week_start) & 
                (website_views_df['event_date'] <= previous_week_end)
            ].copy() if not website_views_df.empty else pd.DataFrame()
            
            # Create performance comparison table by source
            website_performance_data = []
            
            # Get all unique sources from both weeks
            all_website_sources = set()
            if not last_week_website_installs.empty:
                all_website_sources.update(last_week_website_installs['source_aggregated'].unique())
            if not previous_week_website_installs.empty:
                all_website_sources.update(previous_week_website_installs['source_aggregated'].unique())
            if not last_week_website_views.empty:
                all_website_sources.update(last_week_website_views['source_aggregated'].unique())
            if not previous_week_website_views.empty:
                all_website_sources.update(previous_week_website_views['source_aggregated'].unique())
            
            for source in all_website_sources:
                # Calculate metrics for last week
                lw_installs = last_week_website_installs[last_week_website_installs['source_aggregated'] == source]['events_count'].sum()
                lw_views = last_week_website_views[last_week_website_views['source_aggregated'] == source]['events_count'].sum() if not last_week_website_views.empty else 0
                
                # Calculate metrics for previous week
                pw_installs = previous_week_website_installs[previous_week_website_installs['source_aggregated'] == source]['events_count'].sum()
                pw_views = previous_week_website_views[previous_week_website_views['source_aggregated'] == source]['events_count'].sum() if not previous_week_website_views.empty else 0
                
                # Calculate deltas
                installs_delta = lw_installs - pw_installs
                views_delta = lw_views - pw_views
                
                # Calculate percentage changes
                installs_pct = (installs_delta / pw_installs * 100) if pw_installs > 0 else 0
                views_pct = (views_delta / pw_views * 100) if pw_views > 0 else 0
                
                # Calculate conversion rates
                lw_conversion = (lw_installs / lw_views * 100) if lw_views > 0 else 0
                pw_conversion = (pw_installs / pw_views * 100) if pw_views > 0 else 0
                conversion_delta = lw_conversion - pw_conversion
                
                website_performance_data.append({
                    'Source': source,
                    'Page Views': f"{lw_views:,}",
                    'Page Views Δ': f"{views_delta:+,} ({views_pct:+.1f}%)" if pw_views > 0 else f"{views_delta:+,}",
                    'Installs': f"{lw_installs:,}",
                    'Installs Δ': f"{installs_delta:+,} ({installs_pct:+.1f}%)" if pw_installs > 0 else f"{installs_delta:+,}",
                    'Conversion Rate': f"{lw_conversion:.2f}%",
                    'Conversion Δ': f"{conversion_delta:+.2f}%" if pw_views > 0 and lw_views > 0 else "N/A"
                })
            
            if website_performance_data:
                website_performance_df = pd.DataFrame(website_performance_data)
                website_performance_df = website_performance_df.sort_values('Installs', key=lambda x: x.str.replace(',', '').astype(int), ascending=False)
                
                st.dataframe(website_performance_df, width='stretch', hide_index=True)
                
                # Summary metrics
                st.subheader('Website Summary - Last Week')
                
                col1, col2, col3, col4 = st.columns(4)
                
                total_lw_views = last_week_website_views['events_count'].sum() if not last_week_website_views.empty else 0
                total_pw_views = previous_week_website_views['events_count'].sum() if not previous_week_website_views.empty else 0
                total_lw_installs = last_week_website_installs['events_count'].sum() if not last_week_website_installs.empty else 0
                total_pw_installs = previous_week_website_installs['events_count'].sum() if not previous_week_website_installs.empty else 0
                
                views_change = total_lw_views - total_pw_views
                installs_change = total_lw_installs - total_pw_installs
                
                overall_lw_conversion = (total_lw_installs / total_lw_views * 100) if total_lw_views > 0 else 0
                overall_pw_conversion = (total_pw_installs / total_pw_views * 100) if total_pw_views > 0 else 0
                conversion_change = overall_lw_conversion - overall_pw_conversion
                
                with col1:
                    st.metric("Total Page Views", f"{total_lw_views:,}", delta=(int(views_change) if pd.notna(views_change) else None))
                
                with col2:
                    st.metric("Total Installs", f"{total_lw_installs:,}", delta=(int(installs_change) if pd.notna(installs_change) else None))
                
                with col3:
                    st.metric("Overall Conversion Rate", f"{overall_lw_conversion:.2f}%", delta=f"{conversion_change:.2f}%")
                
                with col4:
                    website_sources_count = len(all_website_sources)
                    st.metric("Active Website Sources", website_sources_count)
            else:
                st.info("No website performance data available for the selected time periods.")
            
            # Top Website Sources Analysis - Last 30 Days
            st.subheader('Top Website Sources - Last 30 Days')
            
            # Filter to last 30 days
            thirty_days_ago = df['event_date'].max() - pd.Timedelta(days=30)
            website_30d_df = website_df[website_df['event_date'] >= thirty_days_ago].copy()
            website_views_30d_df = website_views_df[website_views_df['event_date'] >= thirty_days_ago].copy() if not website_views_df.empty else pd.DataFrame()
            
            if not website_30d_df.empty or not website_views_30d_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Top Sources by Installs**")
                    if not website_30d_df.empty:
                        top_sources_installs = website_30d_df.groupby('source_aggregated')['events_count'].sum().sort_values(ascending=False).head(10)
                        
                        top_sources_installs_df = pd.DataFrame({
                            'Source': top_sources_installs.index,
                            'Installs': top_sources_installs.values
                        })
                        st.dataframe(top_sources_installs_df, width='stretch', hide_index=True)
                    else:
                        st.info("No website installs data available.")
                
                with col2:
                    st.write("**Top Sources by Page Views**")
                    if not website_views_30d_df.empty:
                        top_sources_views = website_views_30d_df.groupby('source_aggregated')['events_count'].sum().sort_values(ascending=False).head(10)
                        
                        top_sources_views_df = pd.DataFrame({
                            'Source': top_sources_views.index,
                            'Page Views': top_sources_views.values
                        })
                        st.dataframe(top_sources_views_df, width='stretch', hide_index=True)
                    else:
                        st.info("No website page views data available.")
                
                # Website source performance chart
                if not website_30d_df.empty:
                    st.subheader('Website Source Performance Chart - Last 30 Days')
                    
                    # Create a horizontal bar chart for top sources
                    top_5_sources = website_30d_df.groupby('source_aggregated')['events_count'].sum().sort_values(ascending=False).head(5)
                    
                    fig_website_sources = px.bar(
                        x=top_5_sources.values,
                        y=top_5_sources.index,
                        orientation='h',
                        title='Top 5 Website Sources by Installs - Last 30 Days',
                        labels={'x': 'Installs', 'y': 'Source'}
                    )
                    
                    fig_website_sources.update_layout(
                        showlegend=False,
                        margin=dict(l=10, r=10, t=30, b=10),
                        xaxis_title=None,
                        yaxis_title=None,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        height=400
                    )
                    
                    fig_website_sources.update_xaxes(showgrid=False)
                    fig_website_sources.update_yaxes(showgrid=False)
                    
                    st.plotly_chart(fig_website_sources, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No website data available for the last 30 days.")
