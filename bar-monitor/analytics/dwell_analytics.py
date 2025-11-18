"""
Dwell Time Analytics & Reporting

Generate actionable reports and insights from dwell time data.

REPORTS GENERATED:
1. Daily Summary - Average dwell, campers, revenue impact
2. Weekly Trends - Day-by-day patterns
3. Hourly Breakdown - Peak camping times
4. Camper Alerts - Real-time notification of long stays
5. Revenue Optimization - Specific recommendations
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DwellAnalytics:
    """
    Analytics engine for dwell time data.
    
    USAGE:
        analytics = DwellAnalytics(db_path='data/dwell_time.db')
        
        # Generate daily report
        report = analytics.generate_daily_report()
        
        # Get recommendations
        recommendations = analytics.get_recommendations()
    """
    
    def __init__(self, db_path: str = 'data/dwell_time.db'):
        self.db_path = Path(db_path)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        logger.info(f"DwellAnalytics initialized (db={db_path})")
    
    def generate_daily_report(self, date: datetime = None) -> Dict:
        """
        Generate comprehensive daily report.
        
        Args:
            date: Date to report on (defaults to today)
            
        Returns:
            Dictionary with full day's statistics and insights
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            # Basic stats for the day
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_visits,
                    AVG(dwell_minutes) as avg_dwell,
                    MIN(dwell_minutes) as min_dwell,
                    MAX(dwell_minutes) as max_dwell,
                    SUM(CASE WHEN dwell_minutes >= 120 THEN 1 ELSE 0 END) as campers_120,
                    SUM(CASE WHEN dwell_minutes >= 90 THEN 1 ELSE 0 END) as campers_90,
                    SUM(CASE WHEN dwell_minutes < 30 THEN 1 ELSE 0 END) as quick_visits
                FROM sessions
                WHERE DATE(entry_time) = ? AND is_active = 0
            """, (date_str,))
            
            row = cursor.fetchone()
            total, avg, min_d, max_d, camp120, camp90, quick = row
            
            # Hourly breakdown
            cursor = conn.execute("""
                SELECT 
                    entry_hour,
                    COUNT(*) as visits,
                    AVG(dwell_minutes) as avg_dwell
                FROM sessions
                WHERE DATE(entry_time) = ? AND is_active = 0
                GROUP BY entry_hour
                ORDER BY entry_hour
            """, (date_str,))
            
            hourly = {}
            for row in cursor:
                hour, visits, avg_dwell = row
                hourly[hour] = {
                    'visits': visits,
                    'avg_dwell_minutes': round(avg_dwell, 1) if avg_dwell else 0
                }
        
        # Calculate revenue impact
        target_dwell = 75  # Target: 75 minutes
        if avg and avg > target_dwell:
            excess_time = avg - target_dwell
            potential_additional_customers = total * (avg / target_dwell - 1)
            potential_revenue = potential_additional_customers * 30  # $30 avg spend
        else:
            excess_time = 0
            potential_additional_customers = 0
            potential_revenue = 0
        
        return {
            'date': date_str,
            'total_visits': total or 0,
            'avg_dwell_minutes': round(avg, 1) if avg else 0,
            'min_dwell_minutes': round(min_d, 1) if min_d else 0,
            'max_dwell_minutes': round(max_d, 1) if max_d else 0,
            'campers_90min': camp90 or 0,
            'campers_120min': camp120 or 0,
            'quick_visits_under_30min': quick or 0,
            'hourly_breakdown': hourly,
            'revenue_optimization': {
                'target_dwell_minutes': target_dwell,
                'excess_time_minutes': round(excess_time, 1),
                'potential_additional_customers': round(potential_additional_customers, 1),
                'potential_daily_revenue_gain': round(potential_revenue, 2)
            }
        }
    
    def generate_weekly_report(self, end_date: datetime = None) -> Dict:
        """
        Generate 7-day trend report.
        
        Args:
            end_date: End of week (defaults to today)
            
        Returns:
            Dictionary with weekly trends
        """
        if end_date is None:
            end_date = datetime.now()
        
        start_date = end_date - timedelta(days=6)
        
        daily_reports = []
        current_date = start_date
        
        while current_date <= end_date:
            report = self.generate_daily_report(current_date)
            daily_reports.append(report)
            current_date += timedelta(days=1)
        
        # Calculate weekly aggregates
        total_visits = sum(r['total_visits'] for r in daily_reports)
        avg_dwell = sum(r['avg_dwell_minutes'] * r['total_visits'] for r in daily_reports) / total_visits if total_visits > 0 else 0
        total_campers = sum(r['campers_90min'] for r in daily_reports)
        
        # Potential weekly revenue gain
        total_potential = sum(r['revenue_optimization']['potential_daily_revenue_gain'] for r in daily_reports)
        
        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'weekly_summary': {
                'total_visits': total_visits,
                'avg_dwell_minutes': round(avg_dwell, 1),
                'total_campers': total_campers,
                'camping_rate_percent': round(total_campers / total_visits * 100, 1) if total_visits > 0 else 0
            },
            'daily_breakdown': daily_reports,
            'weekly_revenue_opportunity': round(total_potential, 2)
        }
    
    def get_recommendations(self) -> List[Dict]:
        """
        Generate actionable recommendations based on data.
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Get last 7 days stats
        weekly = self.generate_weekly_report()
        summary = weekly['weekly_summary']
        
        # Recommendation 1: Overall dwell time
        if summary['avg_dwell_minutes'] > 90:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Turnover',
                'issue': f"Average dwell time is {summary['avg_dwell_minutes']:.0f} minutes (target: 75 minutes)",
                'impact': f"Potential revenue gain: ${weekly['weekly_revenue_opportunity']:.0f}/week",
                'actions': [
                    "Offer check proactively after 75 minutes",
                    "Add subtle 'last call' reminder for long-staying groups",
                    "Train staff to encourage turnover politely",
                    "Consider time limits for high-demand periods"
                ]
            })
        
        # Recommendation 2: Camping rate
        if summary['camping_rate_percent'] > 15:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Campers',
                'issue': f"{summary['camping_rate_percent']:.1f}% of customers stay >90 minutes",
                'impact': f"{summary['total_campers']} campers this week blocking seats",
                'actions': [
                    "Implement 90-minute soft time limit during busy periods",
                    "Offer 'one more for the road' at 75-minute mark",
                    "Create standing-room area for overflow",
                    "Monitor repeat campers and set expectations"
                ]
            })
        
        # Recommendation 3: Peak times
        busiest_hours = self._find_busiest_camping_hours()
        if busiest_hours:
            hours_str = ', '.join(f"{h}:00" for h in busiest_hours[:3])
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Peak Times',
                'issue': f"Longest dwell times occur at {hours_str}",
                'impact': "Blocking seats during potentially busy periods",
                'actions': [
                    f"Focus turnover efforts during {hours_str}",
                    "Add extra staff during these hours",
                    "Implement 'rush hour' table policies",
                    "Offer happy hour before peak to draw customers earlier"
                ]
            })
        
        # Add positive feedback if doing well
        if summary['avg_dwell_minutes'] <= 75:
            recommendations.append({
                'priority': 'INFO',
                'category': 'Performance',
                'issue': "Dwell times are well-optimized",
                'impact': "Maintaining good turnover rate",
                'actions': [
                    "Continue current practices",
                    "Monitor for seasonal changes",
                    "Consider if you can serve even more customers"
                ]
            })
        
        return recommendations
    
    def _find_busiest_camping_hours(self) -> List[int]:
        """Find hours with longest average dwell times."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    entry_hour,
                    AVG(dwell_minutes) as avg_dwell
                FROM sessions
                WHERE entry_time >= ? AND is_active = 0
                GROUP BY entry_hour
                HAVING COUNT(*) >= 3
                ORDER BY avg_dwell DESC
                LIMIT 5
            """, (start_date.isoformat(),))
            
            return [row[0] for row in cursor]
    
    def generate_text_report(self, days: int = 7) -> str:
        """
        Generate human-readable text report.
        
        Args:
            days: Number of days to report on
            
        Returns:
            Formatted text report
        """
        weekly = self.generate_weekly_report()
        recommendations = self.get_recommendations()
        
        report = []
        report.append("╔═══════════════════════════════════════════════════════════╗")
        report.append("║           DWELL TIME ANALYSIS REPORT                      ║")
        report.append("╚═══════════════════════════════════════════════════════════╝")
        report.append("")
        report.append(f"Period: {weekly['start_date']} to {weekly['end_date']}")
        report.append("")
        
        report.append("SUMMARY:")
        report.append("─" * 60)
        summary = weekly['weekly_summary']
        report.append(f"  Total Visits: {summary['total_visits']}")
        report.append(f"  Average Dwell Time: {summary['avg_dwell_minutes']:.1f} minutes")
        report.append(f"  Campers (>90 min): {summary['total_campers']} ({summary['camping_rate_percent']:.1f}%)")
        report.append("")
        
        report.append("REVENUE OPPORTUNITY:")
        report.append("─" * 60)
        revenue = weekly['weekly_revenue_opportunity']
        report.append(f"  Potential Weekly Gain: ${revenue:.2f}")
        report.append(f"  Potential Monthly Gain: ${revenue * 4.3:.2f}")
        report.append(f"  Potential Annual Gain: ${revenue * 52:.2f}")
        report.append("")
        
        report.append("RECOMMENDATIONS:")
        report.append("─" * 60)
        for i, rec in enumerate(recommendations, 1):
            report.append(f"\n{i}. [{rec['priority']}] {rec['category']}")
            report.append(f"   Issue: {rec['issue']}")
            report.append(f"   Impact: {rec['impact']}")
            report.append("   Actions:")
            for action in rec['actions']:
                report.append(f"     • {action}")
        
        report.append("")
        report.append("─" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return '\n'.join(report)
    
    def export_csv(self, filepath: str, days: int = 30):
        """
        Export session data to CSV file.
        
        Args:
            filepath: Path to save CSV
            days: Number of days to export
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    entry_time,
                    exit_time,
                    dwell_minutes,
                    day_of_week,
                    entry_hour
                FROM sessions
                WHERE entry_time >= ? AND is_active = 0
                ORDER BY entry_time DESC
            """, (cutoff_date.isoformat(),))
            
            rows = cursor.fetchall()
        
        # Write CSV
        with open(filepath, 'w') as f:
            # Header
            f.write("Entry Time,Exit Time,Dwell Minutes,Day of Week,Entry Hour\n")
            
            # Data
            for row in rows:
                f.write(','.join(str(x) for x in row) + '\n')
        
        logger.info(f"Exported {len(rows)} sessions to {filepath}")


# Command-line usage
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python dwell_analytics.py [daily|weekly|recommendations|export]")
        sys.exit(1)
    
    analytics = DwellAnalytics()
    command = sys.argv[1]
    
    if command == 'daily':
        report = analytics.generate_daily_report()
        print(json.dumps(report, indent=2))
    
    elif command == 'weekly':
        report = analytics.generate_weekly_report()
        print(json.dumps(report, indent=2))
    
    elif command == 'recommendations':
        recommendations = analytics.get_recommendations()
        for rec in recommendations:
            print(f"\n[{rec['priority']}] {rec['category']}")
            print(f"Issue: {rec['issue']}")
            print(f"Impact: {rec['impact']}")
            print("Actions:")
            for action in rec['actions']:
                print(f"  • {action}")
    
    elif command == 'report':
        print(analytics.generate_text_report())
    
    elif command == 'export':
        filepath = sys.argv[2] if len(sys.argv) > 2 else 'dwell_export.csv'
        analytics.export_csv(filepath)
        print(f"Exported to {filepath}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
