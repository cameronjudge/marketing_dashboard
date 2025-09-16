import streamlit as st
import plotly.express as px
import pandas as pd
from src.db.redshift_connection import run_query, get_redshift_connection
from src.sql.upgrade.trial import trial_categories_categories

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
    df_long = df[['week'] + existing_cols].melt(
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