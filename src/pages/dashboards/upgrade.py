import streamlit as st
import plotly.express as px
import pandas as pd
from src.db.redshift_connection import run_query, get_redshift_connection
from src.sql.core_metrics.core_metrics import core_metrics

def upgrade_page() -> None:
    st.title('Upgrade')
    
    # Get core metrics data
    df = run_query(core_metrics)
    
    if df.empty:
        st.info('No data available yet.')
        return
    
    # Convert week to datetime and sort
    df['week'] = pd.to_datetime(df['week'])
    df = df.sort_values('week')
    
    # Header row for Trial Categories: title + inline selector
    tc_left, tc_right = st.columns([3, 2])
    with tc_left:
        st.subheader('Trial Categories')

    # Keep only weekly category columns
    category_cols = [
        'home_trials',
        'upsell_trials',
        'optin_trials',
        'article_trials',
        'welcome_trials',
    ]

    # Filter to available columns only
    existing_cols = [c for c in category_cols if c in df.columns]

    # Friendly category labels (reused for KPIs and chart)
    label_map = {
        'home_trials': 'Home',
        'upsell_trials': 'Upsell',
        'optin_trials': 'Opt-in',
        'article_trials': 'Article',
        'welcome_trials': 'Welcome',
    }

    # KPI metrics with WoW deltas
    if existing_cols:

        def latest_with_delta(df_cat: pd.DataFrame, value_col: str) -> tuple[pd.Series | None, float | None]:
            temp = df_cat[['week', value_col]].dropna().copy()
            if temp.empty:
                return None, None
            temp = temp.sort_values('week')
            latest_val = temp.iloc[-1][value_col]
            if len(temp) < 2:
                return latest_val, None
            prev_val = temp.iloc[-2][value_col]
            try:
                delta_val = float(latest_val) - float(prev_val)
            except Exception:
                delta_val = None
            return latest_val, delta_val

        cols = st.columns(len(existing_cols))
        for idx, col in enumerate(existing_cols):
            latest, delta = latest_with_delta(df, col)
            with cols[idx]:
                if latest is None or pd.isna(latest):
                    st.metric(label=label_map.get(col, col), value='—', delta=None)
                else:
                    st.metric(
                        label=label_map.get(col, col),
                        value=f"{int(latest):,}",
                        delta=(int(delta) if delta is not None and pd.notna(delta) else None),
                    )
    # Select filter for Trial Categories chart (does not affect KPIs)
    available_trial_labels = [label_map.get(c, c) for c in existing_cols]
    with tc_right:
        selected_trial_labels = st.multiselect(
            ' ', options=available_trial_labels, default=available_trial_labels,
            key='trial_categories_select', label_visibility='collapsed'
        )
    selected_trial_cols = [c for c in existing_cols if label_map.get(c, c) in selected_trial_labels]

    if not selected_trial_cols:
        st.info('Select at least one category to display.')
    else:
        df_long = df[['week'] + selected_trial_cols].melt(
            id_vars='week', var_name='category', value_name='trials'
        )
        df_long['category'] = df_long['category'].map(lambda x: label_map.get(x, x))

        fig = px.area(
            df_long,
            x='week',
            y='trials',
            color='category',
        )
        fig.update_layout(
            height=340,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
            xaxis_title='Week', yaxis_title='Trials',
            yaxis=dict(tickformat=','),
            margin=dict(t=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Upgrades by source (stacked bar)
    up_left, up_right = st.columns([3, 2])
    with up_left:
        st.subheader('Upgrades by source')
    
    # Transform core metrics data for upgrade visualization
    df_up = df[['week', 'direct_upgrades', 'trial_conversions', 'reopened_shops']].copy()
    df_up = df_up.melt(id_vars=['week'], var_name='upgrade_path', value_name='count_of_upgrades')
    df_up['week_start'] = df_up['week']
    
    # Map column names to display names
    path_mapping = {
        'direct_upgrades': 'direct',
        'trial_conversions': 'free_trial', 
        'reopened_shops': 'reopened'
    }
    df_up['upgrade_path'] = df_up['upgrade_path'].map(path_mapping)

    category_order = ['direct', 'free_trial', 'reopened']
    color_map = {
        'direct': '#72a7ff',
        'free_trial': '#b8b8ff',
        'reopened': '#f59db1',
    }
    df_up['upgrade_path'] = pd.Categorical(
        df_up['upgrade_path'], categories=category_order, ordered=True
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

    # Compute totals and format KPIs
    direct_latest, direct_delta = latest_with_delta_direct(df, 'direct_upgrades')
    free_trial_latest, free_trial_delta = latest_with_delta_direct(df, 'trial_conversions')
    reopened_latest, reopened_delta = latest_with_delta_direct(df, 'reopened_shops')
    total_latest = sum(v for v in [direct_latest, free_trial_latest, reopened_latest] if v is not None) if any(v is not None for v in [direct_latest, free_trial_latest, reopened_latest]) else None
    total_delta = (
        (direct_delta if direct_delta is not None else 0)
        + (free_trial_delta if free_trial_delta is not None else 0)
        + (reopened_delta if reopened_delta is not None else 0)
        if all(d is not None for d in [direct_delta, free_trial_delta, reopened_delta])
        else None
    )
    
    kpi_label_map = {
        'direct': 'Direct',
        'free_trial': 'Free trial',
        'reopened': 'Reopened',
        'total': 'Total'
    }
    
    kpi_cols = st.columns(4)
    kpis = [
        ('direct', direct_latest, direct_delta),
        ('free_trial', free_trial_latest, free_trial_delta),
        ('reopened', reopened_latest, reopened_delta),
        ('total', total_latest, total_delta),
    ]
    
    for col, (key, val, delta) in zip(kpi_cols, kpis):
        with col:
            if val is None or pd.isna(val):
                st.metric(label=kpi_label_map.get(key, key), value='—', delta=None)
            else:
                st.metric(
                    label=kpi_label_map.get(key, key),
                    value=f"{int(val):,}",
                    delta=(int(delta) if delta is not None and pd.notna(delta) else None),
                )

    # Select filter for chart sources
    available_paths = category_order
    with up_right:
        selected_paths = st.multiselect(
            ' ', options=available_paths, default=available_paths,
            key='upgrades_sources_select', label_visibility='collapsed'
        )
    chart_df = df_up[df_up['upgrade_path'].astype(str).isin(selected_paths)] if selected_paths else df_up.iloc[0:0]

    if chart_df.empty:
        st.info('Select at least one source to display.')
        return

    fig2 = px.bar(
        chart_df,
        x='week_start',
        y='count_of_upgrades',
        color='upgrade_path',
        barmode='stack',
        category_orders={'upgrade_path': category_order},
        color_discrete_map=color_map,
    )
    fig2.update_layout(
        height=340,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
        bargap=0.15,
        xaxis_title='Week', yaxis_title='Upgrades',
        yaxis=dict(tickformat=','),
        margin=dict(t=10)
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Net Awesome (Net Upgrades) Chart
    st.subheader('Net Awesome (Upgrades - Downgrades)')
    
    # Create net upgrades chart data
    net_df = df[['week', 'core_upgrades', 'core_downgrades', 'core_net_upgrades']].copy()
    
    # KPI for net upgrades with WoW delta
    net_latest, net_delta = latest_with_delta_direct(df, 'core_net_upgrades')
    upgrades_latest, upgrades_delta = latest_with_delta_direct(df, 'core_upgrades')
    downgrades_latest, downgrades_delta = latest_with_delta_direct(df, 'core_downgrades')
    
    # Display net upgrades KPIs
    net_kpi_cols = st.columns(3)
    net_kpis = [
        ('Net Upgrades', net_latest, net_delta),
        ('Total Upgrades', upgrades_latest, upgrades_delta),
        ('Total Downgrades', downgrades_latest, downgrades_delta),
    ]
    
    for col, (label, val, delta) in zip(net_kpi_cols, net_kpis):
        with col:
            if val is None or pd.isna(val):
                st.metric(label=label, value='—', delta=None)
            else:
                delta_color = 'inverse' if label == 'Total Downgrades' else 'normal'
                st.metric(
                    label=label,
                    value=f"{int(val):,}",
                    delta=(int(delta) if delta is not None and pd.notna(delta) else None),
                    delta_color=delta_color
                )
    
    # Create line chart for net upgrades trend
    fig_net = px.line(
        net_df,
        x='week',
        y='core_net_upgrades',
        title='Weekly Net Upgrades Trend',
        markers=True
    )
    
    # Add data labels on points
    fig_net.update_traces(
        textposition='top center',
        texttemplate='%{y:,.0f}',
        mode='lines+markers+text'
    )
    
    # Add horizontal line at y=0 for reference
    fig_net.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Apply styling
    fig_net.update_layout(
        height=340,
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=0),
        xaxis_title='Week',
        yaxis_title='Net Upgrades',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(tickformat=',')
    )
    
    fig_net.update_xaxes(showgrid=False)
    fig_net.update_yaxes(showgrid=False)
    
    st.plotly_chart(fig_net, use_container_width=True)

    # Trial Conversions by Type
    st.subheader('Trial Conversion Rates by Type')
    
    # Define conversion rate columns that should be available from the query
    cvr_cols = {
        'home': 'home_cvr_pct',
        'upsell': 'upsell_cvr_pct', 
        'optin': 'optin_cvr_pct',
        'article': 'article_cvr_pct',
        'welcome': 'welcome_cvr_pct'
    }
    
    # Define completed and conversion columns
    completed_cols = {
        'home': 'home_completed',
        'upsell': 'upsell_completed',
        'optin': 'optin_completed', 
        'article': 'article_completed',
        'welcome': 'welcome_completed'
    }
    
    conversion_cols = {
        'home': 'home_conversions',
        'upsell': 'upsell_conversions',
        'optin': 'optin_conversions',
        'article': 'article_conversions', 
        'welcome': 'welcome_conversions'
    }
    
    # Filter to only include trial types that have data
    available_cvr_types = [trial_type for trial_type in cvr_cols.keys() 
                          if cvr_cols[trial_type] in df.columns and completed_cols[trial_type] in df.columns]
    
    if available_cvr_types:
        # KPI metrics for conversion rates with WoW deltas
        def latest_with_delta_cvr(df_orig: pd.DataFrame, col: str):
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
        
        # Display conversion rate KPIs
        conv_kpi_cols = st.columns(len(available_cvr_types))
        for idx, trial_type in enumerate(available_cvr_types):
            cvr_col = cvr_cols[trial_type]
            completed_col = completed_cols[trial_type]
            conversions_col = conversion_cols[trial_type]
            
            latest_cvr, delta_cvr = latest_with_delta_cvr(df, cvr_col)
            latest_completed, _ = latest_with_delta_cvr(df, completed_col)
            latest_conversions, _ = latest_with_delta_cvr(df, conversions_col)
            
            with conv_kpi_cols[idx]:
                if latest_cvr is None or pd.isna(latest_cvr):
                    st.metric(label=f"{label_map.get(f'{trial_type}_trials', trial_type.title())} CVR", value='—', delta=None)
                else:
                    # Show additional context in help text
                    help_text = None
                    if latest_completed is not None and latest_conversions is not None:
                        help_text = f"{int(latest_conversions)} conversions / {int(latest_completed)} completed trials"
                    
                    st.metric(
                        label=f"{label_map.get(f'{trial_type}_trials', trial_type.title())} CVR",
                        value=f"{latest_cvr:.1f}%",
                        delta=(f"{delta_cvr:.1f}pp" if delta_cvr is not None and pd.notna(delta_cvr) else None),
                        help=help_text
                    )
        
        # Create conversion rate chart
        cvr_chart_cols = ['week'] + [cvr_cols[t] for t in available_cvr_types]
        conv_chart_df = df[cvr_chart_cols].melt(
            id_vars='week', var_name='trial_type', value_name='conversion_rate'
        )
        
        # Map CVR column names back to friendly names
        cvr_label_map = {cvr_cols[trial_type]: label_map.get(f'{trial_type}_trials', trial_type.title()) 
                        for trial_type in available_cvr_types}
        conv_chart_df['trial_type'] = conv_chart_df['trial_type'].map(cvr_label_map)
        
        # Filter for chart display
        conv_left, conv_right = st.columns([3, 2])
        with conv_right:
            available_conv_labels = list(cvr_label_map.values())
            # Default to 'Home' if available, otherwise use all
            default_selection = ['Home'] if 'Home' in available_conv_labels else available_conv_labels
            selected_conv_labels = st.multiselect(
                ' ', options=available_conv_labels, default=default_selection,
                key='conversion_rates_select', label_visibility='collapsed'
            )
        
        filtered_conv_df = conv_chart_df[conv_chart_df['trial_type'].isin(selected_conv_labels)] if selected_conv_labels else conv_chart_df.iloc[0:0]
        
        if not filtered_conv_df.empty:
            fig_conv = px.line(
                filtered_conv_df,
                x='week',
                y='conversion_rate',
                color='trial_type',
                markers=True
            )
            
            # Add data labels on points
            fig_conv.update_traces(
                textposition='top center',
                texttemplate='%{y:.1f}%',
                mode='lines+markers+text'
            )
            
            # Apply styling
            fig_conv.update_layout(
                height=340,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
                margin=dict(l=10, r=10, t=30, b=0),
                xaxis_title='Week',
                yaxis_title='Conversion Rate (%)',
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(tickformat='.1f', range=[0, None])
            )
            
            fig_conv.update_xaxes(showgrid=False)
            fig_conv.update_yaxes(showgrid=False)
            
            st.plotly_chart(fig_conv, use_container_width=True)
        else:
            st.info('Select at least one trial type to display conversion rates.')
    else:
        st.info('No trial conversion rate data available.')