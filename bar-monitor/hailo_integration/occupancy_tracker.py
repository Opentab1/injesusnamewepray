"""
Occupancy Tracker

This module manages overall occupancy tracking, data persistence, and statistics.

WHAT IT DOES:
1. Combines people detection + counting logic
2. Stores historical data (entries/exits/occupancy over time)
3. Provides current and historical statistics
4. Handles database storage
5. Generates reports

This is the HIGH-LEVEL interface you'll use in your main application.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class OccupancySnapshot:
    """
    A snapshot of occupancy at a specific time.
    
    Attributes:
        timestamp: When this snapshot was taken
        current_occupancy: Number of people currently inside
        total_entries: Total entries since start/reset
        total_exits: Total exits since start/reset
        active_tracks: Number of people currently being tracked
    """
    timestamp: datetime
    current_occupancy: int
    total_entries: int
    total_exits: int
    active_tracks: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class OccupancyEvent:
    """
    A single entry or exit event.
    
    Attributes:
        timestamp: When event occurred
        event_type: 'entry' or 'exit'
        occupancy_after: Occupancy count after this event
    """
    timestamp: datetime
    event_type: str  # 'entry' or 'exit'
    occupancy_after: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class OccupancyTracker:
    """
    Main occupancy tracking system.
    
    USAGE:
        # Initialize
        tracker = OccupancyTracker(db_path='data/occupancy.db')
        
        # Update with new detections
        tracker.update(detections)
        
        # Get current stats
        occupancy = tracker.get_current_occupancy()
        stats = tracker.get_statistics()
        
        # Get historical data
        history = tracker.get_history(hours=1)
    """
    
    def __init__(self, db_path: str = 'data/occupancy.db', 
                 snapshot_interval: int = 60):
        """
        Initialize occupancy tracker.
        
        Args:
            db_path: Path to SQLite database file
            snapshot_interval: Seconds between automatic snapshots
        """
        self.db_path = Path(db_path)
        self.snapshot_interval = snapshot_interval
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Current state
        self.current_occupancy = 0
        self.total_entries = 0
        self.total_exits = 0
        self.active_tracks = 0
        self.last_snapshot_time = time.time()
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Start background snapshot thread
        self.running = True
        self.snapshot_thread = threading.Thread(target=self._snapshot_loop, daemon=True)
        self.snapshot_thread.start()
        
        logger.info(f"OccupancyTracker initialized (db={db_path}, "
                   f"snapshot_interval={snapshot_interval}s)")
    
    def _init_database(self):
        """
        Initialize SQLite database with required tables.
        
        TABLES:
        1. snapshots: Periodic snapshots of occupancy state
        2. events: Individual entry/exit events
        3. sessions: Tracking sessions (app start/stop)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    current_occupancy INTEGER NOT NULL,
                    total_entries INTEGER NOT NULL,
                    total_exits INTEGER NOT NULL,
                    active_tracks INTEGER NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    occupancy_after INTEGER NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_entries INTEGER,
                    total_exits INTEGER,
                    peak_occupancy INTEGER
                )
            """)
            
            # Create indices for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp 
                ON snapshots(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON events(timestamp)
            """)
            
            conn.commit()
        
        logger.info("Database initialized")
    
    def update(self, stats: Dict):
        """
        Update tracker with new statistics from counter.
        
        Args:
            stats: Dictionary with keys: current_occupancy, total_entries,
                   total_exits, active_tracks
        """
        with self.lock:
            # Detect new events
            new_entries = stats['total_entries'] - self.total_entries
            new_exits = stats['total_exits'] - self.total_exits
            
            # Update state
            self.current_occupancy = stats['current_occupancy']
            self.total_entries = stats['total_entries']
            self.total_exits = stats['total_exits']
            self.active_tracks = stats.get('active_tracks', 0)
            
            # Record events
            if new_entries > 0:
                for _ in range(new_entries):
                    self._record_event('entry')
            
            if new_exits > 0:
                for _ in range(new_exits):
                    self._record_event('exit')
            
            # Check if it's time for a snapshot
            if time.time() - self.last_snapshot_time >= self.snapshot_interval:
                self._take_snapshot()
                self.last_snapshot_time = time.time()
    
    def _record_event(self, event_type: str):
        """Record an entry or exit event."""
        event = OccupancyEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            occupancy_after=self.current_occupancy
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO events (timestamp, event_type, occupancy_after)
                VALUES (?, ?, ?)
            """, (event.timestamp.isoformat(), event.event_type, event.occupancy_after))
            conn.commit()
        
        logger.debug(f"Recorded {event_type} event (occupancy: {self.current_occupancy})")
    
    def _take_snapshot(self):
        """Take a snapshot of current occupancy state."""
        snapshot = OccupancySnapshot(
            timestamp=datetime.now(),
            current_occupancy=self.current_occupancy,
            total_entries=self.total_entries,
            total_exits=self.total_exits,
            active_tracks=self.active_tracks
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO snapshots (timestamp, current_occupancy, total_entries, 
                                      total_exits, active_tracks)
                VALUES (?, ?, ?, ?, ?)
            """, (snapshot.timestamp.isoformat(), snapshot.current_occupancy,
                  snapshot.total_entries, snapshot.total_exits, snapshot.active_tracks))
            conn.commit()
        
        logger.debug(f"Snapshot taken: occupancy={self.current_occupancy}")
    
    def _snapshot_loop(self):
        """Background thread for periodic snapshots."""
        while self.running:
            time.sleep(self.snapshot_interval)
            
            with self.lock:
                self._take_snapshot()
    
    def get_current_occupancy(self) -> int:
        """Get current occupancy count."""
        with self.lock:
            return self.current_occupancy
    
    def get_statistics(self) -> Dict:
        """
        Get current statistics.
        
        Returns:
            Dictionary with current state and counts
        """
        with self.lock:
            return {
                'current_occupancy': self.current_occupancy,
                'total_entries': self.total_entries,
                'total_exits': self.total_exits,
                'active_tracks': self.active_tracks,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_history(self, hours: int = 1) -> List[Dict]:
        """
        Get historical snapshots.
        
        Args:
            hours: Number of hours of history to retrieve
            
        Returns:
            List of snapshot dictionaries
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, current_occupancy, total_entries, total_exits, active_tracks
                FROM snapshots
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (cutoff_time.isoformat(),))
            
            snapshots = []
            for row in cursor:
                snapshots.append({
                    'timestamp': row[0],
                    'current_occupancy': row[1],
                    'total_entries': row[2],
                    'total_exits': row[3],
                    'active_tracks': row[4]
                })
            
            return snapshots
    
    def get_events(self, hours: int = 1) -> List[Dict]:
        """
        Get historical events.
        
        Args:
            hours: Number of hours of events to retrieve
            
        Returns:
            List of event dictionaries
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, event_type, occupancy_after
                FROM events
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (cutoff_time.isoformat(),))
            
            events = []
            for row in cursor:
                events.append({
                    'timestamp': row[0],
                    'event_type': row[1],
                    'occupancy_after': row[2]
                })
            
            return events
    
    def get_peak_occupancy(self, hours: int = 24) -> Tuple[int, str]:
        """
        Get peak occupancy within time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            (peak_count, timestamp) tuple
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT MAX(current_occupancy), timestamp
                FROM snapshots
                WHERE timestamp >= ?
            """, (cutoff_time.isoformat(),))
            
            row = cursor.fetchone()
            if row and row[0] is not None:
                return row[0], row[1]
            else:
                return 0, datetime.now().isoformat()
    
    def reset_counters(self):
        """Reset all counters (useful for daily/hourly resets)."""
        with self.lock:
            self.total_entries = 0
            self.total_exits = 0
            # Don't reset current_occupancy - it's the actual count
            logger.info("Counters reset")
    
    def stop(self):
        """Stop the tracker and cleanup."""
        self.running = False
        if hasattr(self, 'snapshot_thread'):
            self.snapshot_thread.join(timeout=5.0)
        
        # Take final snapshot
        with self.lock:
            self._take_snapshot()
        
        logger.info("OccupancyTracker stopped")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Occupancy Tracker")
    print("=" * 60)
    
    # Create tracker
    tracker = OccupancyTracker(db_path='test_occupancy.db', snapshot_interval=5)
    
    try:
        # Simulate some events
        for i in range(10):
            # Simulate stats from counter
            stats = {
                'current_occupancy': min(i, 5),
                'total_entries': i,
                'total_exits': max(0, i - 5),
                'active_tracks': min(i, 5)
            }
            
            tracker.update(stats)
            
            print(f"Update {i+1}: Occupancy={stats['current_occupancy']}")
            time.sleep(0.5)
        
        # Get statistics
        print("\nCurrent Statistics:")
        print(json.dumps(tracker.get_statistics(), indent=2))
        
        print("\nPeak Occupancy:")
        peak, peak_time = tracker.get_peak_occupancy(hours=1)
        print(f"Peak: {peak} at {peak_time}")
        
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        tracker.stop()
        print("Tracker stopped")
