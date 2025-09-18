import streamlit as st
import plotly.express as px
import pandas as pd
from src.db.redshift_connection import run_query, get_redshift_connection
from src.sql.upgrade.trial import trial_categories_categories
from src.sql.upgrade.awesome import new_awesome_by_source

def upgrade_page() -> None:
    st.title('Upgrade')
    
    st.subheader('Trial Categories')

    df = run_query(trial_categories_categories)

    if df.empty:
        st.info('No trial data available yet.')
        return

    # Keep only weekly category columns
    category_cols = [
        'home_trials',
        'upsell_trials',
        'optin_trials',
        'article_trials',
        'welcome_trials',
        'cs_trials',
    ]

    # Normalize and order by week
    if 'week' in df.columns:
        df['week'] = pd.to_datetime(df['week'])
        df = df.sort_values('week')

    # Filter to available columns only
    existing_cols = [c for c in category_cols if c in df.columns]

    # Friendly category labels (reused for KPIs and chart)
    label_map = {
        'home_trials': 'Home',
        'upsell_trials': 'Upsell',
        'optin_trials': 'Opt-in',
        'article_trials': 'Article',
        'welcome_trials': 'Welcome',
        'cs_trials': 'Customer Success',
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
                        value=int(latest),
                        delta=(int(delta) if delta is not None and pd.notna(delta) else None),
                    )
    # Select filter for Trial Categories chart (does not affect KPIs)
    available_trial_labels = [label_map.get(c, c) for c in existing_cols]
    col_tc_select, _ = st.columns(2)
    with col_tc_select:
        selected_trial_labels = st.multiselect(
            'Categories', options=available_trial_labels, default=available_trial_labels, key='trial_categories_select'
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
            title='Weekly trial starts by category (completed weeks)',
        )
        fig.update_layout(xaxis_title='Week', yaxis_title='Trials')
        st.plotly_chart(fig, use_container_width=True)

    # Upgrades by source (stacked bar)
    st.subheader('Upgrades by source')
    df_up = run_query(new_awesome_by_source)
    if df_up.empty:
        st.info('No upgrade data available yet.')
        return
    df_up['week_start'] = pd.to_datetime(df_up['week_start'])
    df_up = df_up.sort_values('week_start')

    category_order = ['direct', 'free_trial', 'reopened', 'other']
    if 'upgrade_path' in df_up.columns:
        df_up['upgrade_path'] = pd.Categorical(
            df_up['upgrade_path'], categories=category_order, ordered=True
        )

    # KPI metrics (exclude 'other') with WoW deltas
    kpi_order = ['direct', 'free_trial', 'reopened']
    present_kpis = [k for k in kpi_order if k in df_up['upgrade_path'].astype(str).unique().tolist()]

    def latest_with_delta_upgrades(frame: pd.DataFrame, path: str):
        temp = frame[frame['upgrade_path'] == path][['week_start', 'count_of_upgrades']].dropna().copy()
        if temp.empty:
            return None, None
        temp = temp.sort_values('week_start')
        latest_val = temp.iloc[-1]['count_of_upgrades']
        if len(temp) < 2:
            return latest_val, None
        prev_val = temp.iloc[-2]['count_of_upgrades']
        try:
            delta_val = float(latest_val) - float(prev_val)
        except Exception:
            delta_val = None
        return latest_val, delta_val

    kpi_label_map = {
        'direct': 'Direct',
        'free_trial': 'Free trial',
        'reopened': 'Reopened',
    }
    if present_kpis:
        cols2 = st.columns(len(present_kpis))
        for idx, key in enumerate(present_kpis):
            latest, delta = latest_with_delta_upgrades(df_up, key)
            with cols2[idx]:
                if latest is None or pd.isna(latest):
                    st.metric(label=kpi_label_map.get(key, key), value='—', delta=None)
                else:
                    st.metric(
                        label=kpi_label_map.get(key, key),
                        value=int(latest),
                        delta=(int(delta) if delta is not None and pd.notna(delta) else None),
                    )

    # Select filter for chart sources
    available_paths = [p for p in category_order if p in df_up['upgrade_path'].astype(str).unique().tolist()]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_paths = st.multiselect(
            'Sources', options=available_paths, default=available_paths, key='upgrades_sources_select'
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
        title='Weekly upgrades by source (completed weeks)'
    )
    fig2.update_layout(xaxis_title='Week', yaxis_title='Upgrades')
    st.plotly_chart(fig2, use_container_width=True)