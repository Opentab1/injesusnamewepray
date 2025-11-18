#!/usr/bin/env python3
"""
Bar Monitor Dashboard - Streamlit Version

STOLEN FROM: streamlit (33k stars)
REPLACED: Custom Flask dashboard (300 lines) → Streamlit (50 lines!)

Run with: streamlit run dashboard_streamlit.py
"""

import streamlit as st
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Bar Monitor Dashboard",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-green { color: #00ff00; }
    .metric-yellow { color: #ffff00; }
    .metric-orange { color: #ffa500; }
    .metric-red { color: #ff0000; }
    .big-font { font-size: 24px !important; }
</style>
""", unsafe_allow_html=True)


def get_occupancy_data(db_path='data/occupancy_v2.db'):
    """Get current occupancy from database."""
    try:
        conn = sqlite3.connect(db_path)
        query = """
            SELECT occupancy_count, timestamp
            FROM occupancy_snapshots
            ORDER BY timestamp DESC
            LIMIT 1
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            return df.iloc[0]['occupancy_count'], df.iloc[0]['timestamp']
        return 0, None
    except Exception as e:
        return 0, None


def get_occupancy_history(db_path='data/occupancy_v2.db', hours=6):
    """Get occupancy history for chart."""
    try:
        conn = sqlite3.connect(db_path)
        since = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT timestamp, occupancy_count
            FROM occupancy_snapshots
            WHERE timestamp >= ?
            ORDER BY timestamp
        """
        df = pd.read_sql_query(query, conn, params=(since.isoformat(),))
        conn.close()
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        return pd.DataFrame()


def get_active_customers(db_path='data/dwell_time.db'):
    """Get currently active customers."""
    try:
        conn = sqlite3.connect(db_path)
        query = """
            SELECT track_id, entry_time,
                   (julianday('now') - julianday(entry_time)) * 24 * 60 as dwell_minutes
            FROM dwell_sessions
            WHERE exit_time IS NULL
            ORDER BY entry_time
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()


def main():
    """Main dashboard."""
    
    # Header
    st.title("🍺 Bar Monitor Dashboard V2")
    st.markdown("**Powered by:** Supervision (18k ⭐) + Streamlit (33k ⭐)")
    
    # Sidebar
    st.sidebar.header("Settings")
    auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=True)
    history_hours = st.sidebar.slider("History (hours)", 1, 24, 6)
    
    # Main columns
    col1, col2, col3, col4 = st.columns(4)
    
    # Get current data
    current_occupancy, last_update = get_occupancy_data()
    active_customers = get_active_customers()
    
    # Metrics
    with col1:
        st.metric(
            label="Current Occupancy",
            value=current_occupancy,
            delta=None
        )
    
    with col2:
        st.metric(
            label="Active Customers",
            value=len(active_customers) if not active_customers.empty else 0
        )
    
    with col3:
        if not active_customers.empty:
            avg_dwell = active_customers['dwell_minutes'].mean()
            st.metric(label="Avg Dwell Time", value=f"{avg_dwell:.1f} min")
        else:
            st.metric(label="Avg Dwell Time", value="N/A")
    
    with col4:
        if last_update:
            st.metric(label="Last Update", value=datetime.fromisoformat(last_update).strftime("%H:%M:%S"))
        else:
            st.metric(label="Last Update", value="N/A")
    
    # Divider
    st.markdown("---")
    
    # Charts row
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📊 Occupancy History")
        history = get_occupancy_history(hours=history_hours)
        
        if not history.empty:
            st.line_chart(
                history.set_index('timestamp')['occupancy_count'],
                use_container_width=True
            )
        else:
            st.info("No occupancy data yet")
    
    with col_chart2:
        st.subheader("⏱️ Dwell Time Distribution")
        
        if not active_customers.empty:
            # Create bins
            bins = [0, 30, 60, 90, 120, 999]
            labels = ['0-30m', '30-60m', '60-90m', '90-120m', '120m+']
            active_customers['bin'] = pd.cut(
                active_customers['dwell_minutes'],
                bins=bins,
                labels=labels
            )
            
            # Count by bin
            dwell_dist = active_customers['bin'].value_counts().sort_index()
            st.bar_chart(dwell_dist)
        else:
            st.info("No active customers")
    
    # Divider
    st.markdown("---")
    
    # Active customers table
    st.subheader("👥 Active Customers")
    
    if not active_customers.empty:
        # Add status column
        def get_status(minutes):
            if minutes < 60:
                return "🟢 Good"
            elif minutes < 90:
                return "🟡 Watch"
            elif minutes < 120:
                return "🟠 Warning"
            else:
                return "🔴 Camper"
        
        active_customers['Status'] = active_customers['dwell_minutes'].apply(get_status)
        active_customers['Entry Time'] = pd.to_datetime(active_customers['entry_time']).dt.strftime('%H:%M:%S')
        active_customers['Dwell (min)'] = active_customers['dwell_minutes'].round(1)
        
        # Display table
        display_df = active_customers[['track_id', 'Entry Time', 'Dwell (min)', 'Status']]
        display_df.columns = ['Track ID', 'Entry Time', 'Dwell (min)', 'Status']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Camper alerts
        campers = active_customers[active_customers['dwell_minutes'] > 120]
        if not campers.empty:
            st.error(f"⚠️ {len(campers)} customer(s) have been here over 2 hours!")
    else:
        st.info("No active customers currently")
    
    # Footer
    st.markdown("---")
    st.caption(f"Dashboard updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()


if __name__ == "__main__":
    main()
