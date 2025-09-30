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