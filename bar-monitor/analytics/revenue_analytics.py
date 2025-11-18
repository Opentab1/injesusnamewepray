"""
Revenue Analytics - Link Dwell Time to Actual POS Data

Combines dwell time tracking with Toast POS data to calculate:
- Revenue per customer
- Revenue per minute of occupancy
- High-value vs low-value customers
- Optimal dwell time for maximum revenue
- Revenue optimization opportunities

BUSINESS INSIGHTS:
- Which customers are worth keeping longer (high spenders)
- Which customers to encourage turnover (low spenders)
- What's the sweet spot between occupancy and revenue
- Time-of-day revenue patterns
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class RevenueAnalytics:
    """
    Link dwell time data with POS revenue data to calculate profitability.
    
    USAGE:
        analytics = RevenueAnalytics(
            dwell_db_path='data/dwell_time.db',
            toast_connector=toast_connector
        )
        
        # Get revenue per customer for last hour
        stats = analytics.get_revenue_per_customer(hours=1)
        
        # Find high-value customers currently in bar
        high_value = analytics.get_high_value_customers()
        
        # Calculate optimal dwell time
        optimal = analytics.calculate_optimal_dwell_time()
    """
    
    def __init__(self, dwell_db_path: str, toast_connector=None):
        """
        Initialize revenue analytics.
        
        Args:
            dwell_db_path: Path to dwell time database
            toast_connector: ToastPOSConnector instance (optional)
        """
        self.dwell_db_path = dwell_db_path
        self.toast_connector = toast_connector
        
        # Create revenue tracking table
        self._init_revenue_db()
        
        logger.info("RevenueAnalytics initialized")
    
    def _init_revenue_db(self):
        """Create tables for linking dwell time to revenue."""
        conn = sqlite3.connect(self.dwell_db_path)
        c = conn.cursor()
        
        # Table to link customers to revenue
        c.execute('''
            CREATE TABLE IF NOT EXISTS customer_revenue (
                track_id INTEGER,
                entry_time TEXT,
                exit_time TEXT,
                dwell_minutes REAL,
                estimated_revenue REAL,
                actual_revenue REAL,
                order_guid TEXT,
                revenue_per_minute REAL,
                customer_type TEXT,
                PRIMARY KEY (track_id, entry_time)
            )
        ''')
        
        # Hourly revenue stats
        c.execute('''
            CREATE TABLE IF NOT EXISTS hourly_revenue (
                hour_start TEXT PRIMARY KEY,
                total_revenue REAL,
                total_customers INTEGER,
                avg_dwell_minutes REAL,
                revenue_per_customer REAL,
                revenue_per_minute REAL,
                occupancy_avg REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def link_customer_to_revenue(self, track_id: int, entry_time: datetime,
                                exit_time: datetime, estimated_revenue: float = None):
        """
        Link a customer's dwell session to their revenue.
        
        Args:
            track_id: Customer tracking ID
            entry_time: When customer entered
            exit_time: When customer exited
            estimated_revenue: Estimated spend if no POS data
        """
        dwell_minutes = (exit_time - entry_time).total_seconds() / 60.0
        
        actual_revenue = None
        order_guid = None
        
        # Try to get actual revenue from Toast POS
        if self.toast_connector:
            # Get orders in window around customer's visit
            orders = self.toast_connector.get_orders(
                start_time=entry_time - timedelta(minutes=5),
                end_time=exit_time + timedelta(minutes=5)
            )
            
            # Simple matching: orders during their visit
            # More sophisticated: use table assignments, check numbers, etc.
            customer_orders = [
                o for o in orders
                if entry_time <= datetime.fromisoformat(o.get('openedDate', '')) <= exit_time
            ]
            
            if customer_orders:
                # Sum up all orders for this customer
                actual_revenue = sum(o.get('totalAmount', 0) / 100.0 for o in customer_orders)
                order_guid = ','.join(o.get('guid', '') for o in customer_orders)
        
        # Calculate metrics
        revenue = actual_revenue or estimated_revenue or 0
        revenue_per_minute = revenue / dwell_minutes if dwell_minutes > 0 else 0
        
        # Classify customer type
        if revenue_per_minute > 1.0:
            customer_type = 'high_value'
        elif revenue_per_minute > 0.5:
            customer_type = 'medium_value'
        elif revenue_per_minute > 0:
            customer_type = 'low_value'
        else:
            customer_type = 'unknown'
        
        # Store in database
        conn = sqlite3.connect(self.dwell_db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO customer_revenue
            (track_id, entry_time, exit_time, dwell_minutes, estimated_revenue,
             actual_revenue, order_guid, revenue_per_minute, customer_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            track_id,
            entry_time.isoformat(),
            exit_time.isoformat(),
            round(dwell_minutes, 2),
            estimated_revenue,
            actual_revenue,
            order_guid,
            round(revenue_per_minute, 2),
            customer_type
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Linked customer {track_id} to ${revenue:.2f} revenue "
                   f"(${revenue_per_minute:.2f}/min, {customer_type})")
    
    def get_revenue_per_customer(self, hours: int = 24) -> Dict:
        """
        Calculate revenue per customer statistics.
        
        Args:
            hours: Hours to look back
            
        Returns:
            Dictionary with revenue statistics
        """
        since = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(self.dwell_db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT 
                COUNT(*) as total_customers,
                AVG(COALESCE(actual_revenue, estimated_revenue)) as avg_revenue,
                SUM(COALESCE(actual_revenue, estimated_revenue)) as total_revenue,
                AVG(dwell_minutes) as avg_dwell,
                AVG(revenue_per_minute) as avg_rpm,
                COUNT(CASE WHEN customer_type = 'high_value' THEN 1 END) as high_value,
                COUNT(CASE WHEN customer_type = 'medium_value' THEN 1 END) as medium_value,
                COUNT(CASE WHEN customer_type = 'low_value' THEN 1 END) as low_value
            FROM customer_revenue
            WHERE exit_time >= ?
        ''', (since.isoformat(),))
        
        row = c.fetchone()
        conn.close()
        
        if row and row[0]:
            return {
                'total_customers': row[0],
                'average_revenue_per_customer': round(row[1] or 0, 2),
                'total_revenue': round(row[2] or 0, 2),
                'average_dwell_minutes': round(row[3] or 0, 1),
                'average_revenue_per_minute': round(row[4] or 0, 2),
                'high_value_customers': row[5],
                'medium_value_customers': row[6],
                'low_value_customers': row[7],
                'period_hours': hours
            }
        
        return {
            'total_customers': 0,
            'average_revenue_per_customer': 0,
            'total_revenue': 0,
            'average_dwell_minutes': 0,
            'average_revenue_per_minute': 0,
            'high_value_customers': 0,
            'medium_value_customers': 0,
            'low_value_customers': 0,
            'period_hours': hours
        }
    
    def get_high_value_customers(self, min_rpm: float = 1.0) -> List[Dict]:
        """
        Get currently active high-value customers.
        
        Args:
            min_rpm: Minimum revenue per minute to be considered high-value
            
        Returns:
            List of high-value customer sessions
        """
        conn = sqlite3.connect(self.dwell_db_path)
        c = conn.cursor()
        
        # Get customers still in bar (no exit time in dwell_sessions)
        c.execute('''
            SELECT 
                ds.track_id,
                ds.entry_time,
                COALESCE(cr.revenue_per_minute, 0) as rpm,
                COALESCE(cr.actual_revenue, cr.estimated_revenue, 0) as revenue
            FROM dwell_sessions ds
            LEFT JOIN customer_revenue cr 
                ON ds.track_id = cr.track_id 
                AND ds.entry_time = cr.entry_time
            WHERE ds.exit_time IS NULL
                AND COALESCE(cr.revenue_per_minute, 0) >= ?
            ORDER BY rpm DESC
        ''', (min_rpm,))
        
        customers = []
        for row in c.fetchall():
            entry = datetime.fromisoformat(row[1])
            current_dwell = (datetime.now() - entry).total_seconds() / 60.0
            
            customers.append({
                'track_id': row[0],
                'entry_time': row[1],
                'current_dwell_minutes': round(current_dwell, 1),
                'revenue_per_minute': round(row[2], 2),
                'current_revenue': round(row[3], 2),
                'projected_revenue': round(row[2] * current_dwell, 2)
            })
        
        conn.close()
        return customers
    
    def calculate_optimal_dwell_time(self, days: int = 7) -> Dict:
        """
        Calculate optimal dwell time that maximizes revenue.
        
        Analyzes historical data to find the sweet spot between:
        - Keeping customers long enough to maximize their spend
        - Turning tables fast enough to serve more customers
        
        Args:
            days: Days of historical data to analyze
            
        Returns:
            Dictionary with optimal dwell time recommendations
        """
        since = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.dwell_db_path)
        c = conn.cursor()
        
        # Get revenue by dwell time buckets
        c.execute('''
            SELECT 
                CAST(dwell_minutes / 15 AS INTEGER) * 15 as dwell_bucket,
                COUNT(*) as customers,
                AVG(COALESCE(actual_revenue, estimated_revenue)) as avg_revenue,
                AVG(revenue_per_minute) as avg_rpm
            FROM customer_revenue
            WHERE exit_time >= ?
                AND dwell_minutes > 0
            GROUP BY dwell_bucket
            HAVING customers >= 5
            ORDER BY dwell_bucket
        ''', (since.isoformat(),))
        
        buckets = c.fetchall()
        conn.close()
        
        if not buckets:
            return {
                'optimal_dwell_minutes': 60,
                'reason': 'Insufficient data',
                'confidence': 'low'
            }
        
        # Find bucket with highest revenue per minute
        optimal_bucket = max(buckets, key=lambda x: x[3])
        
        # Find bucket with highest total revenue per customer
        highest_revenue_bucket = max(buckets, key=lambda x: x[2])
        
        return {
            'optimal_dwell_minutes': optimal_bucket[0],
            'optimal_rpm': round(optimal_bucket[3], 2),
            'highest_revenue_dwell': highest_revenue_bucket[0],
            'highest_avg_revenue': round(highest_revenue_bucket[2], 2),
            'recommendation': (
                f"Target dwell time: {optimal_bucket[0]} minutes for best revenue/minute. "
                f"Customers staying {highest_revenue_bucket[0]} minutes spend most per visit."
            ),
            'buckets': [
                {
                    'dwell_minutes': b[0],
                    'customers': b[1],
                    'avg_revenue': round(b[2], 2),
                    'rpm': round(b[3], 2)
                }
                for b in buckets
            ],
            'confidence': 'high' if len(buckets) >= 10 else 'medium',
            'sample_size': sum(b[1] for b in buckets),
            'analysis_days': days
        }
    
    def get_revenue_opportunities(self) -> Dict:
        """
        Identify current revenue optimization opportunities.
        
        Returns:
            Dictionary with actionable recommendations
        """
        # Get current occupancy and customer values
        conn = sqlite3.connect(self.dwell_db_path)
        c = conn.cursor()
        
        # Get currently active customers
        c.execute('''
            SELECT 
                ds.track_id,
                ds.entry_time,
                (julianday('now') - julianday(ds.entry_time)) * 24 * 60 as current_dwell,
                COALESCE(cr.revenue_per_minute, 0.5) as rpm,
                cr.customer_type
            FROM dwell_sessions ds
            LEFT JOIN customer_revenue cr 
                ON ds.track_id = cr.track_id 
                AND ds.entry_time = cr.entry_time
            WHERE ds.exit_time IS NULL
        ''')
        
        active_customers = c.fetchall()
        conn.close()
        
        opportunities = {
            'low_value_campers': [],
            'high_value_customers': [],
            'quick_turnover_targets': [],
            'total_opportunity': 0
        }
        
        for customer in active_customers:
            track_id, entry, dwell, rpm, customer_type = customer
            
            # Low-value campers (staying >90 min, spending <$0.40/min)
            if dwell > 90 and rpm < 0.4:
                opportunity = 30 * 0.6  # Assume new customer would spend $0.60/min for 30 min
                opportunities['low_value_campers'].append({
                    'track_id': track_id,
                    'dwell_minutes': round(dwell, 1),
                    'rpm': round(rpm, 2),
                    'opportunity': round(opportunity, 2)
                })
                opportunities['total_opportunity'] += opportunity
            
            # High-value customers to retain
            elif rpm > 0.8:
                opportunities['high_value_customers'].append({
                    'track_id': track_id,
                    'dwell_minutes': round(dwell, 1),
                    'rpm': round(rpm, 2),
                    'value': round(rpm * dwell, 2)
                })
            
            # Quick turnover targets (45-60 min, decent spend)
            elif 45 <= dwell <= 60 and rpm >= 0.5:
                opportunities['quick_turnover_targets'].append({
                    'track_id': track_id,
                    'dwell_minutes': round(dwell, 1),
                    'rpm': round(rpm, 2)
                })
        
        opportunities['recommendation'] = self._generate_recommendation(opportunities)
        
        return opportunities
    
    def _generate_recommendation(self, opportunities: Dict) -> str:
        """Generate actionable recommendation based on opportunities."""
        if opportunities['low_value_campers']:
            count = len(opportunities['low_value_campers'])
            value = opportunities['total_opportunity']
            return (
                f"⚠️ ACTION NEEDED: {count} low-value campers detected. "
                f"Encouraging turnover could generate ${value:.0f} additional revenue."
            )
        elif opportunities['high_value_customers']:
            count = len(opportunities['high_value_customers'])
            return (
                f"✓ Good: {count} high-value customers active. "
                f"Prioritize their service to retain them."
            )
        else:
            return "✓ Optimal: Good mix of customers and turnover rate."
    
    def generate_revenue_report(self, days: int = 7) -> str:
        """
        Generate comprehensive revenue analysis report.
        
        Args:
            days: Days to analyze
            
        Returns:
            Formatted report string
        """
        stats = self.get_revenue_per_customer(hours=days*24)
        optimal = self.calculate_optimal_dwell_time(days=days)
        opportunities = self.get_revenue_opportunities()
        
        report = f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              📊 REVENUE ANALYTICS REPORT                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

PERIOD: Last {days} days

💰 REVENUE PERFORMANCE:
════════════════════════════════════════════════════════════
Total Revenue:              ${stats['total_revenue']:,.2f}
Total Customers:            {stats['total_customers']}
Avg Revenue/Customer:       ${stats['average_revenue_per_customer']:.2f}
Avg Revenue/Minute:         ${stats['average_revenue_per_minute']:.2f}
Avg Dwell Time:             {stats['average_dwell_minutes']:.0f} minutes

🎯 CUSTOMER BREAKDOWN:
════════════════════════════════════════════════════════════
High-Value (>$1.00/min):    {stats['high_value_customers']} customers
Medium-Value ($0.50-1.00):  {stats['medium_value_customers']} customers
Low-Value (<$0.50/min):     {stats['low_value_customers']} customers

⏱️ OPTIMAL DWELL TIME:
════════════════════════════════════════════════════════════
Target Dwell Time:          {optimal['optimal_dwell_minutes']} minutes
Best Revenue/Minute:        ${optimal['optimal_rpm']:.2f}/min
Confidence:                 {optimal['confidence']}
Sample Size:                {optimal['sample_size']} customers

{optimal['recommendation']}

💡 CURRENT OPPORTUNITIES:
════════════════════════════════════════════════════════════
{opportunities['recommendation']}

Low-Value Campers:          {len(opportunities['low_value_campers'])}
High-Value Active:          {len(opportunities['high_value_customers'])}
Potential Revenue Gain:     ${opportunities['total_opportunity']:.2f}

════════════════════════════════════════════════════════════
"""
        return report


if __name__ == "__main__":
    # Test revenue analytics
    logging.basicConfig(level=logging.INFO)
    
    analytics = RevenueAnalytics(dwell_db_path='data/dwell_time.db')
    
    print("\n" + analytics.generate_revenue_report(days=7))
