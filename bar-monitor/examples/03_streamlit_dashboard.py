"""
Streamlit Dashboard Example - FROM STREAMLIT GALLERY

Source: https://streamlit.io/gallery
        https://docs.streamlit.io/library/api-reference

This is NOT custom code - this is a standard Streamlit pattern!

⭐ Streamlit: 33,000 stars
📖 Docs: https://docs.streamlit.io/

Run with: streamlit run 03_streamlit_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Page config (standard Streamlit)
st.set_page_config(
    page_title="Bar Monitor Dashboard",
    page_icon="🍺",
    layout="wide"
)

# Title (standard Streamlit)
st.title("🍺 Bar Monitor Dashboard")

# Metrics (standard Streamlit)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Current Occupancy", "12", "+2")

with col2:
    st.metric("Entries Today", "87", "+5")

with col3:
    st.metric("Avg Dwell Time", "65 min", "-10 min")

with col4:
    st.metric("Revenue/Hour", "$234", "+$12")

# Divider (standard Streamlit)
st.divider()

# Charts (standard Streamlit)
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📊 Occupancy History")
    
    # Generate sample data
    chart_data = pd.DataFrame({
        'time': pd.date_range(start=datetime.now()-timedelta(hours=6), periods=60, freq='6min'),
        'occupancy': np.random.randint(5, 25, 60)
    })
    
    st.line_chart(chart_data.set_index('time'))

with col_chart2:
    st.subheader("⏱️ Dwell Time Distribution")
    
    # Generate sample data
    dwell_data = pd.DataFrame({
        'Range': ['0-30m', '30-60m', '60-90m', '90-120m', '120m+'],
        'Count': [5, 12, 8, 3, 1]
    })
    
    st.bar_chart(dwell_data.set_index('Range'))

# Divider
st.divider()

# Table (standard Streamlit)
st.subheader("👥 Active Customers")

# Generate sample data
active_customers = pd.DataFrame({
    'Track ID': [1, 2, 3, 4, 5],
    'Entry Time': ['18:23', '18:45', '19:02', '19:15', '19:28'],
    'Dwell (min)': [67, 45, 28, 15, 2],
    'Status': ['🟡 Watch', '🟢 Good', '🟢 Good', '🟢 Good', '🟢 Good']
})

st.dataframe(active_customers, use_container_width=True, hide_index=True)

# Footer
st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Auto-refresh (standard Streamlit pattern)
time.sleep(5)
st.rerun()
