import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.db.redshift_connection import run_query, get_redshift_connection
from src.sql.core_metrics.integrations import integrations


def integrations_page():
    st.title('🔗 Integrations & Partnerships')
    
    # Load data
    with st.spinner('Loading integration data...'):
        df = run_query(integrations)
    
    if df.empty:
        st.error("No integration data available")
        return
    
    # Clean and prepare data
    df = df.copy()
    
    def safe_convert_percentage(series):
        """Safely convert percentage strings to floats"""
        return pd.to_numeric(
            series.astype(str).str.replace('%', '').str.replace('None', '').str.strip(),
            errors='coerce'
        )
    
    def safe_convert_currency(series):
        """Safely convert currency strings to floats"""
        return pd.to_numeric(
            series.astype(str).str.replace('$', '').str.replace(',', '').str.replace('None', '').str.strip(),
            errors='coerce'
        )
    
    def safe_convert_days(series):
        """Safely convert day strings to integers"""
        return pd.to_numeric(
            series.astype(str).str.replace(' days', '').str.replace('None', '').str.strip(),
            errors='coerce'
        )
    
    # Convert percentage strings to floats
    percentage_cols = ['Downgrade %', 'Churn %', 'Free Churn %', 'Awesome Conv %']
    for col in percentage_cols:
        if col in df.columns:
            df[col] = safe_convert_percentage(df[col])
    
    # Convert LTV strings to floats
    if 'LTV' in df.columns:
        df['LTV'] = safe_convert_currency(df['LTV'])
    
    # Convert lifetime strings to integers
    if 'Lifetime' in df.columns:
        df['Lifetime'] = safe_convert_days(df['Lifetime'])
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_integrations = len(df)
        st.metric("Total Integrations", total_integrations)
    
    with col2:
        total_shops = df['Total Shops'].sum()
        st.metric("Total Shops", f"{total_shops:,}")
    
    with col3:
        awesome_only_count = len(df[df['Tier'] == 'Awesome-Only'])
        st.metric("Awesome-Only", awesome_only_count)
    
    with col4:
        avg_conversion = df['Awesome Conv %'].mean()
        if pd.notna(avg_conversion):
            st.metric("Avg Conversion", f"{avg_conversion:.1f}%")
        else:
            st.metric("Avg Conversion", "N/A")
    
    st.divider()
    
    # Tier distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Integration Distribution by Tier")
        tier_counts = df['Tier'].value_counts()
        fig_tier = px.pie(
            values=tier_counts.values,
            names=tier_counts.index,
            title="Integrations by Tier",
            color_discrete_map={
                'Awesome-Only': '#FF6B6B',
                'Available-to-All': '#4ECDC4',
                'Unknown': '#95A5A6'
            }
        )
        fig_tier.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_tier, width='stretch')
    
    with col2:
        st.subheader("Shop Volume by Tier")
        tier_shops = df.groupby('Tier')['Total Shops'].sum()
        fig_shops = px.bar(
            x=tier_shops.index,
            y=tier_shops.values,
            title="Total Shops by Tier",
            color=tier_shops.index,
            color_discrete_map={
                'Awesome-Only': '#FF6B6B',
                'Available-to-All': '#4ECDC4',
                'Unknown': '#95A5A6'
            }
        )
        fig_shops.update_layout(showlegend=False)
        st.plotly_chart(fig_shops, width='stretch')
    
    # Top integrations by shop count
    st.subheader("📊 Top Integrations by Shop Count")
    
    top_integrations = df.nlargest(15, 'Total Shops')
    
    fig_top = px.bar(
        top_integrations,
        x='Total Shops',
        y='Integration',
        orientation='h',
        color='Tier',
        title="Top 15 Integrations by Total Shops",
        color_discrete_map={
            'Awesome-Only': '#FF6B6B',
            'Available-to-All': '#4ECDC4',
            'Unknown': '#95A5A6'
        }
    )
    fig_top.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_top, width='stretch')
    
    # Performance metrics comparison
    st.subheader("🎯 Performance Metrics Analysis")
    
    # Create tabs for different metrics
    tab1, tab2, tab3, tab4 = st.tabs(["Conversion Rates", "Churn Analysis", "LTV Analysis", "Lifetime Analysis"])
    
    with tab1:
        st.write("**Awesome Conversion Rates by Integration**")
        
        # Filter for integrations with meaningful data
        conv_data = df[df['Awesome Conv %'].notna() & (df['Total Shops'] >= 20)].copy()
        conv_data = conv_data.sort_values('Awesome Conv %', ascending=True).tail(20)
        
        fig_conv = px.bar(
            conv_data,
            x='Awesome Conv %',
            y='Integration',
            orientation='h',
            color='Tier',
            title="Top 20 Integrations by Awesome Conversion Rate",
            color_discrete_map={
                'Awesome-Only': '#FF6B6B',
                'Available-to-All': '#4ECDC4',
                'Unknown': '#95A5A6'
            }
        )
        fig_conv.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
        fig_conv.add_vline(x=conv_data['Awesome Conv %'].mean(), line_dash="dash", 
                          annotation_text=f"Average: {conv_data['Awesome Conv %'].mean():.1f}%")
        st.plotly_chart(fig_conv, width='stretch')
    
    with tab2:
        st.write("**Churn Rate Analysis**")
        
        # Awesome vs Free churn comparison
        churn_data = df[(df['Churn %'].notna()) & (df['Free Churn %'].notna()) & (df['Total Shops'] >= 20)].copy()
        
        fig_churn = go.Figure()
        
        fig_churn.add_trace(go.Scatter(
            x=churn_data['Churn %'],
            y=churn_data['Free Churn %'],
            mode='markers',
            marker=dict(
                size=churn_data['Total Shops'] / 20,
                color=churn_data['Tier'].map({
                    'Awesome-Only': '#FF6B6B',
                    'Available-to-All': '#4ECDC4',
                    'Unknown': '#95A5A6'
                }),
                opacity=0.7
            ),
            text=churn_data['Integration'],
            hovertemplate='<b>%{text}</b><br>Awesome Churn: %{x}%<br>Free Churn: %{y}%<extra></extra>'
        ))
        
        fig_churn.add_shape(
            type="line",
            x0=0, y0=0, x1=100, y1=100,
            line=dict(color="gray", width=1, dash="dash")
        )
        
        fig_churn.update_layout(
            title="Awesome vs Free Churn Rates",
            xaxis_title="Awesome Churn Rate (%)",
            yaxis_title="Free Churn Rate (%)",
            height=500
        )
        
        st.plotly_chart(fig_churn, width='stretch')
        st.caption("Bubble size represents total shops. Points below the diagonal line indicate lower churn for awesome users.")
    
    with tab3:
        st.write("**Lifetime Value Analysis**")
        
        ltv_data = df[(df['LTV'].notna()) & (df['Total Shops'] >= 20)].copy()
        ltv_data = ltv_data.sort_values('LTV', ascending=True).tail(20)
        
        fig_ltv = px.bar(
            ltv_data,
            x='LTV',
            y='Integration',
            orientation='h',
            color='Tier',
            title="Top 20 Integrations by Average LTV",
            color_discrete_map={
                'Awesome-Only': '#FF6B6B',
                'Available-to-All': '#4ECDC4',
                'Unknown': '#95A5A6'
            }
        )
        fig_ltv.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
        fig_ltv.add_vline(x=ltv_data['LTV'].mean(), line_dash="dash", 
                         annotation_text=f"Average: ${ltv_data['LTV'].mean():.0f}")
        st.plotly_chart(fig_ltv, width='stretch')
    
    with tab4:
        st.write("**Customer Lifetime Analysis**")
        
        lifetime_data = df[(df['Lifetime'].notna()) & (df['Total Shops'] >= 20)].copy()
        lifetime_data = lifetime_data.sort_values('Lifetime', ascending=True).tail(20)
        
        fig_lifetime = px.bar(
            lifetime_data,
            x='Lifetime',
            y='Integration',
            orientation='h',
            color='Tier',
            title="Top 20 Integrations by Average Lifetime (Days)",
            color_discrete_map={
                'Awesome-Only': '#FF6B6B',
                'Available-to-All': '#4ECDC4',
                'Unknown': '#95A5A6'
            }
        )
        fig_lifetime.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
        fig_lifetime.add_vline(x=lifetime_data['Lifetime'].mean(), line_dash="dash", 
                              annotation_text=f"Average: {lifetime_data['Lifetime'].mean():.0f} days")
        st.plotly_chart(fig_lifetime, width='stretch')
    
    # Detailed data table
    st.subheader("📋 Detailed Integration Data")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tier_filter = st.selectbox(
            "Filter by Tier",
            options=['All'] + list(df['Tier'].unique()),
            index=0
        )
    
    with col2:
        min_shops = st.number_input(
            "Minimum Shop Count",
            min_value=0,
            max_value=int(df['Total Shops'].max()),
            value=20
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            options=['Total Shops', 'Awesome Conv %', 'LTV', 'Churn %', 'Lifetime'],
            index=0
        )
    
    # Apply filters
    filtered_df = df[df['Total Shops'] >= min_shops].copy()
    if tier_filter != 'All':
        filtered_df = filtered_df[filtered_df['Tier'] == tier_filter]
    
    # Sort data
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(sort_by, ascending=False)
    
    # Display table with formatting
    display_df = filtered_df[[
        'Integration', 'Tier', 'Total Shops', 'Awesome', 'Free',
        'Downgrade %', 'Churn %', 'LTV', 'Lifetime', 'Free Churn %', 'Awesome Conv %'
    ]].copy()
    
    # Format the display
    for col in ['Downgrade %', 'Churn %', 'Free Churn %', 'Awesome Conv %']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    
    if 'LTV' in display_df.columns:
        display_df['LTV'] = display_df['LTV'].apply(lambda x: f"${x:.0f}" if pd.notna(x) else "N/A")
    
    if 'Lifetime' in display_df.columns:
        display_df['Lifetime'] = display_df['Lifetime'].apply(lambda x: f"{x} days" if pd.notna(x) else "N/A")
    
    st.dataframe(
        display_df,
        width='stretch',
        height=400
    )
    
    # Summary insights
    st.subheader("🔍 Key Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top Performers:**")
        
        # Highest conversion rate
        top_conv = df.loc[df['Awesome Conv %'].idxmax()] if df['Awesome Conv %'].notna().any() else None
        if top_conv is not None:
            st.write(f"• **Highest Conversion**: {top_conv['Integration']} ({top_conv['Awesome Conv %']:.1f}%)")
        
        # Highest LTV
        top_ltv = df.loc[df['LTV'].idxmax()] if df['LTV'].notna().any() else None
        if top_ltv is not None:
            st.write(f"• **Highest LTV**: {top_ltv['Integration']} (${top_ltv['LTV']:.0f})")
        
        # Lowest churn
        low_churn = df.loc[df['Churn %'].idxmin()] if df['Churn %'].notna().any() else None
        if low_churn is not None:
            st.write(f"• **Lowest Churn**: {low_churn['Integration']} ({low_churn['Churn %']:.1f}%)")
    
    with col2:
        st.write("**Tier Comparison:**")
        
        awesome_only = df[df['Tier'] == 'Awesome-Only']
        available_all = df[df['Tier'] == 'Available-to-All']
        
        if not awesome_only.empty and not available_all.empty:
            ao_conv = awesome_only['Awesome Conv %'].mean()
            aa_conv = available_all['Awesome Conv %'].mean()
            
            if pd.notna(ao_conv):
                st.write(f"• **Awesome-Only Avg Conversion**: {ao_conv:.1f}%")
            if pd.notna(aa_conv):
                st.write(f"• **Available-to-All Avg Conversion**: {aa_conv:.1f}%")
            
            ao_ltv = awesome_only['LTV'].mean()
            aa_ltv = available_all['LTV'].mean()
            
            if pd.notna(ao_ltv):
                st.write(f"• **Awesome-Only Avg LTV**: ${ao_ltv:.0f}")
            if pd.notna(aa_ltv):
                st.write(f"• **Available-to-All Avg LTV**: ${aa_ltv:.0f}")

    return