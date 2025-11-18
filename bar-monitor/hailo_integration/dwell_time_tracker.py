"""
Dwell Time Tracker

Track how long each person/group stays in the bar.

BUSINESS VALUE:
- Identify "campers" who occupy seats for too long
- Optimize table turnover to serve more customers
- Increase revenue by freeing up high-value seats faster
- Typical impact: $1,500-2,500/month additional revenue

HOW IT WORKS:
1. Person detected entering (crosses counting line inward)
2. Track their unique ID
3. Person detected exiting (crosses counting line outward)
4. Calculate time difference = dwell time
5. Store to database with analytics

REVENUE MATH:
- 4 seats occupied 3 hours by low spenders ($80 total)
- Same 4 seats could serve 3 groups in 3 hours ($240 total)
- Lost revenue: $160 per occurrence
- Typical bar: 10-20 such occurrences per week = $8,000-16,000/month lost
- Goal: Recover 20-30% through better turnover = $1,600-4,800/month
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import time
import threading
from collections import defaultdict
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class DwellSession:
    """
    Represents one customer's visit to the bar.
    
    Attributes:
        track_id: Unique identifier for this person (from tracker)
        entry_time: When they entered
        exit_time: When they left (None if still present)
        dwell_minutes: How long they stayed
        day_of_week: Mon, Tue, Wed, etc.
        entry_hour: Hour they entered (for time-of-day analysis)
    """
    track_id: int
    entry_time: datetime
    exit_time: Optional[datetime] = None
    dwell_minutes: Optional[float] = None
    day_of_week: Optional[str] = None
    entry_hour: Optional[int] = None
    
    def calculate_dwell_time(self):
        """Calculate dwell time if exit time is set."""
        if self.exit_time:
            delta = self.exit_time - self.entry_time
            self.dwell_minutes = delta.total_seconds() / 60.0
            self.day_of_week = self.entry_time.strftime('%A')
            self.entry_hour = self.entry_time.hour
    
    def is_active(self) -> bool:
        """Check if person is still in the bar."""
        return self.exit_time is None
    
    def get_current_dwell_minutes(self) -> float:
        """Get current dwell time even if still active."""
        end_time = self.exit_time or datetime.now()
        delta = end_time - self.entry_time
        return delta.total_seconds() / 60.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['entry_time'] = self.entry_time.isoformat() if self.entry_time else None
        data['exit_time'] = self.exit_time.isoformat() if self.exit_time else None
        return data


class DwellTimeTracker:
    """
    Track customer dwell times for revenue optimization.
    
    USAGE:
        tracker = DwellTimeTracker(db_path='data/dwell_time.db')
        
        # When someone enters
        tracker.record_entry(track_id=42, timestamp=datetime.now())
        
        # When someone exits
        tracker.record_exit(track_id=42, timestamp=datetime.now())
        
        # Get current people in bar
        active = tracker.get_active_sessions()
        
        # Get analytics
        stats = tracker.get_statistics()
    """
    
    def __init__(self, db_path: str = 'data/dwell_time.db',
                 warning_threshold: int = 90,  # minutes
                 alert_threshold: int = 120):  # minutes
        """
        Initialize dwell time tracker.
        
        Args:
            db_path: Path to SQLite database
            warning_threshold: Minutes before warning (yellow alert)
            alert_threshold: Minutes before alert (red alert)
        """
        self.db_path = Path(db_path)
        self.warning_threshold = warning_threshold
        self.alert_threshold = alert_threshold
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Active sessions (track_id -> DwellSession)
        self.active_sessions: Dict[int, DwellSession] = {}
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Load any incomplete sessions from database
        self._load_active_sessions()
        
        logger.info(f"DwellTimeTracker initialized (db={db_path}, "
                   f"warning={warning_threshold}m, alert={alert_threshold}m)")
    
    def _init_database(self):
        """
        Initialize SQLite database with required tables.
        
        TABLES:
        1. sessions: All completed customer visits
        2. daily_stats: Aggregated statistics by day
        3. hourly_stats: Aggregated statistics by hour
        """
        with sqlite3.connect(self.db_path) as conn:
            # Main sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id INTEGER NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT,
                    dwell_minutes REAL,
                    day_of_week TEXT,
                    entry_hour INTEGER,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Daily statistics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    total_customers INTEGER,
                    avg_dwell_minutes REAL,
                    median_dwell_minutes REAL,
                    min_dwell_minutes REAL,
                    max_dwell_minutes REAL,
                    campers_count INTEGER,
                    quick_visits_count INTEGER
                )
            """)
            
            # Hourly statistics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hourly_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    avg_dwell_minutes REAL,
                    customer_count INTEGER,
                    UNIQUE(date, hour)
                )
            """)
            
            # Create indices for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_entry_time 
                ON sessions(entry_time)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_active 
                ON sessions(is_active)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_day 
                ON sessions(day_of_week)
            """)
            
            conn.commit()
        
        logger.info("Database initialized")
    
    def _load_active_sessions(self):
        """Load any incomplete sessions from database (e.g., after restart)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT track_id, entry_time, exit_time, dwell_minutes
                FROM sessions
                WHERE is_active = 1
            """)
            
            for row in cursor:
                track_id, entry_time_str, exit_time_str, dwell_minutes = row
                
                session = DwellSession(
                    track_id=track_id,
                    entry_time=datetime.fromisoformat(entry_time_str),
                    exit_time=datetime.fromisoformat(exit_time_str) if exit_time_str else None,
                    dwell_minutes=dwell_minutes
                )
                
                self.active_sessions[track_id] = session
        
        if self.active_sessions:
            logger.info(f"Loaded {len(self.active_sessions)} active sessions from database")
    
    def record_entry(self, track_id: int, timestamp: Optional[datetime] = None):
        """
        Record a customer entering the bar.
        
        Args:
            track_id: Unique identifier for this person
            timestamp: Entry time (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.lock:
            # Create new session
            session = DwellSession(
                track_id=track_id,
                entry_time=timestamp
            )
            
            self.active_sessions[track_id] = session
            
            # Store to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO sessions (track_id, entry_time, is_active)
                    VALUES (?, ?, 1)
                """, (track_id, timestamp.isoformat()))
                conn.commit()
            
            logger.info(f"Entry recorded: track_id={track_id}, time={timestamp.strftime('%H:%M:%S')}")
    
    def record_exit(self, track_id: int, timestamp: Optional[datetime] = None):
        """
        Record a customer exiting the bar.
        
        Args:
            track_id: Unique identifier for this person
            timestamp: Exit time (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.lock:
            # Find active session
            if track_id not in self.active_sessions:
                logger.warning(f"Exit recorded for unknown track_id: {track_id}")
                return
            
            session = self.active_sessions[track_id]
            session.exit_time = timestamp
            session.calculate_dwell_time()
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE sessions
                    SET exit_time = ?,
                        dwell_minutes = ?,
                        day_of_week = ?,
                        entry_hour = ?,
                        is_active = 0
                    WHERE track_id = ? AND is_active = 1
                """, (timestamp.isoformat(), session.dwell_minutes,
                      session.day_of_week, session.entry_hour, track_id))
                conn.commit()
            
            # Remove from active sessions
            del self.active_sessions[track_id]
            
            logger.info(f"Exit recorded: track_id={track_id}, "
                       f"dwell_time={session.dwell_minutes:.1f} minutes")
    
    def get_active_sessions(self) -> List[DwellSession]:
        """
        Get all currently active sessions (people still in bar).
        
        Returns:
            List of DwellSession objects for people currently present
        """
        with self.lock:
            return list(self.active_sessions.values())
    
    def get_campers(self, threshold_minutes: Optional[int] = None) -> List[DwellSession]:
        """
        Get list of "campers" - people who have been here too long.
        
        Args:
            threshold_minutes: Custom threshold (uses alert_threshold if None)
            
        Returns:
            List of DwellSession objects for campers
        """
        if threshold_minutes is None:
            threshold_minutes = self.alert_threshold
        
        campers = []
        
        with self.lock:
            for session in self.active_sessions.values():
                current_dwell = session.get_current_dwell_minutes()
                if current_dwell >= threshold_minutes:
                    campers.append(session)
        
        # Sort by dwell time (longest first)
        campers.sort(key=lambda s: s.get_current_dwell_minutes(), reverse=True)
        
        return campers
    
    def get_warnings(self) -> List[DwellSession]:
        """
        Get list of people approaching camping threshold.
        
        Returns:
            List of sessions between warning and alert thresholds
        """
        warnings = []
        
        with self.lock:
            for session in self.active_sessions.values():
                current_dwell = session.get_current_dwell_minutes()
                if self.warning_threshold <= current_dwell < self.alert_threshold:
                    warnings.append(session)
        
        warnings.sort(key=lambda s: s.get_current_dwell_minutes(), reverse=True)
        
        return warnings
    
    def get_statistics(self, days: int = 7) -> Dict:
        """
        Get dwell time statistics for recent period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            # Overall stats
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_visits,
                    AVG(dwell_minutes) as avg_dwell,
                    MIN(dwell_minutes) as min_dwell,
                    MAX(dwell_minutes) as max_dwell,
                    SUM(CASE WHEN dwell_minutes >= ? THEN 1 ELSE 0 END) as campers,
                    SUM(CASE WHEN dwell_minutes < 30 THEN 1 ELSE 0 END) as quick_visits
                FROM sessions
                WHERE exit_time >= ? AND is_active = 0
            """, (self.alert_threshold, cutoff_date.isoformat()))
            
            row = cursor.fetchone()
            total_visits, avg_dwell, min_dwell, max_dwell, campers, quick_visits = row
            
            # Stats by day of week
            cursor = conn.execute("""
                SELECT 
                    day_of_week,
                    AVG(dwell_minutes) as avg_dwell,
                    COUNT(*) as count
                FROM sessions
                WHERE exit_time >= ? AND is_active = 0
                GROUP BY day_of_week
                ORDER BY 
                    CASE day_of_week
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END
            """, (cutoff_date.isoformat(),))
            
            by_day = {}
            for row in cursor:
                day, avg, count = row
                by_day[day] = {'avg_dwell_minutes': avg, 'visit_count': count}
            
            # Stats by hour
            cursor = conn.execute("""
                SELECT 
                    entry_hour,
                    AVG(dwell_minutes) as avg_dwell,
                    COUNT(*) as count
                FROM sessions
                WHERE exit_time >= ? AND is_active = 0
                GROUP BY entry_hour
                ORDER BY entry_hour
            """, (cutoff_date.isoformat(),))
            
            by_hour = {}
            for row in cursor:
                hour, avg, count = row
                by_hour[hour] = {'avg_dwell_minutes': avg, 'visit_count': count}
        
        # Current active stats
        active_count = len(self.active_sessions)
        camper_count = len(self.get_campers())
        warning_count = len(self.get_warnings())
        
        return {
            'period_days': days,
            'total_visits': total_visits or 0,
            'avg_dwell_minutes': avg_dwell or 0,
            'min_dwell_minutes': min_dwell or 0,
            'max_dwell_minutes': max_dwell or 0,
            'campers_count': campers or 0,
            'quick_visits_count': quick_visits or 0,
            'by_day_of_week': by_day,
            'by_entry_hour': by_hour,
            'current_active': active_count,
            'current_campers': camper_count,
            'current_warnings': warning_count
        }
    
    def get_revenue_impact_estimate(self, avg_spend_per_person: float = 30.0,
                                    target_dwell_minutes: int = 75) -> Dict:
        """
        Estimate potential revenue increase from optimizing dwell time.
        
        Args:
            avg_spend_per_person: Average customer spend
            target_dwell_minutes: Target dwell time
            
        Returns:
            Dictionary with revenue impact estimates
        """
        stats = self.get_statistics(days=30)
        
        current_avg = stats['avg_dwell_minutes']
        campers_per_month = stats['campers_count']
        
        if current_avg <= target_dwell_minutes:
            return {
                'message': 'Dwell time already at target',
                'current_avg_minutes': current_avg,
                'target_minutes': target_dwell_minutes,
                'potential_monthly_gain': 0
            }
        
        # Calculate potential improvement
        excess_time = current_avg - target_dwell_minutes
        improvement_factor = target_dwell_minutes / current_avg
        
        # Estimate additional customers served
        # If people stay 25% less time, you can serve 33% more people in same time
        additional_customers_per_day = stats['total_visits'] * (1 / improvement_factor - 1) / 30
        
        # Revenue calculation
        monthly_additional_revenue = additional_customers_per_day * 30 * avg_spend_per_person
        
        return {
            'current_avg_minutes': current_avg,
            'target_minutes': target_dwell_minutes,
            'excess_time_minutes': excess_time,
            'improvement_potential_percent': (1 - improvement_factor) * 100,
            'additional_customers_per_day': additional_customers_per_day,
            'potential_monthly_gain': monthly_additional_revenue,
            'campers_per_month': campers_per_month,
            'avg_spend_per_person': avg_spend_per_person
        }
    
    def export_report(self, filepath: str, days: int = 30):
        """
        Export detailed report to JSON file.
        
        Args:
            filepath: Path to save JSON report
            days: Number of days to include
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'period_days': days,
            'statistics': self.get_statistics(days=days),
            'revenue_impact': self.get_revenue_impact_estimate(),
            'active_sessions': [s.to_dict() for s in self.get_active_sessions()],
            'current_campers': [s.to_dict() for s in self.get_campers()],
            'current_warnings': [s.to_dict() for s in self.get_warnings()]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report exported to {filepath}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Remove old session data to keep database size manageable.
        
        Args:
            days_to_keep: Number of days of history to retain
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM sessions
                WHERE exit_time < ? AND is_active = 0
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} old sessions (older than {days_to_keep} days)")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Mark all active sessions with current time
        for track_id in list(self.active_sessions.keys()):
            self.record_exit(track_id)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Dwell Time Tracker")
    print("=" * 60)
    
    # Create tracker
    tracker = DwellTimeTracker(
        db_path='test_dwell_time.db',
        warning_threshold=5,  # 5 minutes for testing
        alert_threshold=10    # 10 minutes for testing
    )
    
    # Simulate some customer visits
    print("\n1. Simulating customer visits...")
    
    # Customer 1: Quick visit
    print("  - Customer 1 enters")
    tracker.record_entry(track_id=1, timestamp=datetime.now() - timedelta(minutes=20))
    tracker.record_exit(track_id=1, timestamp=datetime.now() - timedelta(minutes=15))
    
    # Customer 2: Normal visit
    print("  - Customer 2 enters")
    tracker.record_entry(track_id=2, timestamp=datetime.now() - timedelta(minutes=45))
    tracker.record_exit(track_id=2, timestamp=datetime.now() - timedelta(minutes=5))
    
    # Customer 3: Still here (camper)
    print("  - Customer 3 enters (still here)")
    tracker.record_entry(track_id=3, timestamp=datetime.now() - timedelta(minutes=15))
    
    # Customer 4: Still here (recent)
    print("  - Customer 4 enters (recent)")
    tracker.record_entry(track_id=4, timestamp=datetime.now() - timedelta(minutes=3))
    
    # Get statistics
    print("\n2. Statistics:")
    stats = tracker.get_statistics(days=1)
    print(f"   Total visits: {stats['total_visits']}")
    print(f"   Average dwell: {stats['avg_dwell_minutes']:.1f} minutes")
    print(f"   Currently active: {stats['current_active']}")
    print(f"   Current campers: {stats['current_campers']}")
    print(f"   Current warnings: {stats['current_warnings']}")
    
    # Get campers
    print("\n3. Campers (> 10 minutes):")
    campers = tracker.get_campers()
    for session in campers:
        dwell = session.get_current_dwell_minutes()
        print(f"   Track ID {session.track_id}: {dwell:.1f} minutes")
    
    # Revenue impact
    print("\n4. Revenue Impact Estimate:")
    impact = tracker.get_revenue_impact_estimate(
        avg_spend_per_person=30,
        target_dwell_minutes=60
    )
    print(f"   Current avg: {impact['current_avg_minutes']:.1f} minutes")
    print(f"   Target: {impact['target_minutes']} minutes")
    print(f"   Potential gain: ${impact['potential_monthly_gain']:.0f}/month")
    
    # Export report
    print("\n5. Exporting report...")
    tracker.export_report('test_dwell_report.json', days=1)
    print("   Report saved to test_dwell_report.json")
    
    print("\n✓ Test complete!")
