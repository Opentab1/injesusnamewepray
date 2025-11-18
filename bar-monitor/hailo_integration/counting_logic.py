"""
Entry/Exit Counting Logic

This module implements the logic to count people entering and exiting the bar
by tracking their movement across a virtual line in the camera view.

HOW IT WORKS:
1. Define a "counting line" in the camera frame (e.g., doorway)
2. Track each detected person using their position
3. When someone crosses the line:
   - Moving UP/IN = Entry (+1)
   - Moving DOWN/OUT = Exit (-1)
4. Maintain running count of occupancy

TRACKING METHOD:
We use "centroid tracking" - follow the center point of each person's
bounding box frame-by-frame to determine their direction.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import deque, OrderedDict
import logging
import time
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class TrackedPerson:
    """
    Represents a person being tracked across frames.
    
    Attributes:
        track_id: Unique ID for this person
        centroids: History of center positions (x, y)
        last_seen: Timestamp of last detection
        crossed_line: Whether they've crossed the counting line
        direction: 'entry' or 'exit' or None
    """
    track_id: int
    centroids: deque  # Recent position history
    last_seen: float
    crossed_line: bool = False
    direction: Optional[str] = None
    
    def update_position(self, centroid: Tuple[int, int]):
        """Add new position to tracking history."""
        self.centroids.append(centroid)
        self.last_seen = time.time()
        
        # Keep only recent history (last 30 frames = 1 second at 30fps)
        if len(self.centroids) > 30:
            self.centroids.popleft()


class CentroidTracker:
    """
    Track people across frames using centroid (center point) tracking.
    
    EXPLANATION:
    - Each person gets a unique ID
    - We match detections frame-to-frame by finding closest centroids
    - If someone disappears for too long, remove their ID
    - This is simpler than deep learning tracking but works well for doorways
    
    ADVANTAGE: Very low CPU usage - just distance calculations
    """
    
    def __init__(self, max_disappeared: int = 30, max_distance: float = 50):
        """
        Initialize tracker.
        
        Args:
            max_disappeared: Frames before removing a lost track (30 frames = 1 sec at 30fps)
            max_distance: Max pixel distance to match detection to existing track
        """
        self.next_id = 0
        self.tracks: Dict[int, TrackedPerson] = OrderedDict()
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        
        logger.info(f"CentroidTracker initialized (max_disappeared={max_disappeared}, max_distance={max_distance})")
    
    def register(self, centroid: Tuple[int, int]) -> int:
        """
        Register a new person.
        
        Args:
            centroid: Initial center position
            
        Returns:
            track_id: Unique ID assigned to this person
        """
        track_id = self.next_id
        self.tracks[track_id] = TrackedPerson(
            track_id=track_id,
            centroids=deque([centroid], maxlen=30),
            last_seen=time.time()
        )
        self.next_id += 1
        
        logger.debug(f"Registered new track ID: {track_id}")
        return track_id
    
    def deregister(self, track_id: int):
        """Remove a lost track."""
        if track_id in self.tracks:
            del self.tracks[track_id]
            logger.debug(f"Deregistered track ID: {track_id}")
    
    def update(self, detections: List[Tuple[int, int]]) -> Dict[int, TrackedPerson]:
        """
        Update tracks with new detections.
        
        Args:
            detections: List of (x, y) centroid positions from current frame
            
        Returns:
            Dictionary of track_id -> TrackedPerson
            
        ALGORITHM:
        1. If no detections, mark all existing tracks as "disappeared"
        2. If no existing tracks, register all detections as new
        3. Otherwise, match detections to tracks using distance
        4. Register unmatched detections as new tracks
        5. Remove tracks that disappeared too long ago
        """
        # No detections - increment disappeared counter
        if len(detections) == 0:
            current_time = time.time()
            disappeared_ids = []
            
            for track_id, track in self.tracks.items():
                if (current_time - track.last_seen) > (self.max_disappeared / 30.0):
                    disappeared_ids.append(track_id)
            
            for track_id in disappeared_ids:
                self.deregister(track_id)
            
            return self.tracks
        
        # No existing tracks - register all detections
        if len(self.tracks) == 0:
            for centroid in detections:
                self.register(centroid)
            return self.tracks
        
        # Match detections to existing tracks
        track_ids = list(self.tracks.keys())
        track_centroids = [self.tracks[tid].centroids[-1] for tid in track_ids]
        
        # Compute distance matrix
        distances = self._compute_distances(track_centroids, detections)
        
        # Match using Hungarian algorithm (simplified: greedy matching)
        matched_pairs = self._greedy_match(distances, self.max_distance)
        
        # Update matched tracks
        matched_track_ids = set()
        matched_detection_ids = set()
        
        for track_idx, det_idx in matched_pairs:
            track_id = track_ids[track_idx]
            centroid = detections[det_idx]
            self.tracks[track_id].update_position(centroid)
            matched_track_ids.add(track_id)
            matched_detection_ids.add(det_idx)
        
        # Register unmatched detections as new tracks
        for det_idx, centroid in enumerate(detections):
            if det_idx not in matched_detection_ids:
                self.register(centroid)
        
        # Remove disappeared tracks
        current_time = time.time()
        disappeared_ids = []
        for track_id in track_ids:
            if track_id not in matched_track_ids:
                if (current_time - self.tracks[track_id].last_seen) > (self.max_disappeared / 30.0):
                    disappeared_ids.append(track_id)
        
        for track_id in disappeared_ids:
            self.deregister(track_id)
        
        return self.tracks
    
    def _compute_distances(self, centroids1: List[Tuple[int, int]], 
                          centroids2: List[Tuple[int, int]]) -> np.ndarray:
        """Compute Euclidean distance matrix between two sets of centroids."""
        distances = np.zeros((len(centroids1), len(centroids2)))
        
        for i, c1 in enumerate(centroids1):
            for j, c2 in enumerate(centroids2):
                distances[i, j] = math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
        
        return distances
    
    def _greedy_match(self, distances: np.ndarray, max_distance: float) -> List[Tuple[int, int]]:
        """
        Greedy matching algorithm.
        
        Repeatedly match the closest pair until no matches below threshold remain.
        """
        matches = []
        distances = distances.copy()
        
        while True:
            # Find minimum distance
            min_val = distances.min()
            
            if min_val > max_distance:
                break
            
            # Get indices of minimum
            i, j = np.unravel_index(distances.argmin(), distances.shape)
            matches.append((i, j))
            
            # Mark row and column as used
            distances[i, :] = float('inf')
            distances[:, j] = float('inf')
        
        return matches


class EntryExitCounter:
    """
    Count people entering and exiting based on line crossing.
    
    SETUP:
    You define a horizontal line in your camera view (e.g., doorway threshold).
    People crossing upward = entering
    People crossing downward = exiting
    
    USAGE:
        counter = EntryExitCounter(
            counting_line_y=300,  # Y-coordinate of doorway in pixels
            frame_height=480
        )
        
        for each frame:
            detections = detector.get_detections()
            centroids = [(d.center) for d in detections]
            entries, exits = counter.update(centroids)
            total_inside = counter.get_occupancy()
    """
    
    def __init__(self, counting_line_y: int, frame_height: int = 480,
                 entry_direction: str = 'down', dwell_tracker=None):
        """
        Initialize counter.
        
        Args:
            counting_line_y: Y-coordinate of counting line (0 = top of frame)
            frame_height: Height of video frame in pixels
            entry_direction: 'down' if entering means moving down in frame,
                           'up' if entering means moving up
            dwell_tracker: Optional DwellTimeTracker instance for tracking visit duration
        """
        self.counting_line_y = counting_line_y
        self.frame_height = frame_height
        self.entry_direction = entry_direction
        self.dwell_tracker = dwell_tracker
        
        self.tracker = CentroidTracker(max_disappeared=30, max_distance=50)
        
        # Counters
        self.total_entries = 0
        self.total_exits = 0
        self.current_occupancy = 0
        
        # Tracking for line crossing
        self.track_states = {}  # track_id -> 'above' or 'below' line
        
        logger.info(f"EntryExitCounter initialized: line_y={counting_line_y}, "
                   f"entry_direction={entry_direction}, "
                   f"dwell_tracking={'enabled' if dwell_tracker else 'disabled'}")
    
    def update(self, detections: List[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Update counter with new detections.
        
        Args:
            detections: List of (x, y) centroid positions
            
        Returns:
            (new_entries, new_exits) in this frame
        """
        # Update tracker
        tracks = self.tracker.update(detections)
        
        new_entries = 0
        new_exits = 0
        
        # Check each track for line crossing
        for track_id, track in tracks.items():
            if len(track.centroids) < 2:
                continue  # Need at least 2 positions to determine direction
            
            current_y = track.centroids[-1][1]
            previous_y = track.centroids[-2][1]
            
            # Determine current position relative to line
            current_side = 'above' if current_y < self.counting_line_y else 'below'
            
            # Check if track has previous state
            if track_id not in self.track_states:
                self.track_states[track_id] = current_side
                continue
            
            previous_side = self.track_states[track_id]
            
            # Detect line crossing
            if previous_side != current_side and not track.crossed_line:
                # Determine direction
                if previous_side == 'above' and current_side == 'below':
                    # Moved from above to below line
                    if self.entry_direction == 'down':
                        direction = 'entry'
                        new_entries += 1
                        self.total_entries += 1
                        self.current_occupancy += 1
                    else:
                        direction = 'exit'
                        new_exits += 1
                        self.total_exits += 1
                        self.current_occupancy -= 1
                
                elif previous_side == 'below' and current_side == 'above':
                    # Moved from below to above line
                    if self.entry_direction == 'down':
                        direction = 'exit'
                        new_exits += 1
                        self.total_exits += 1
                        self.current_occupancy -= 1
                    else:
                        direction = 'entry'
                        new_entries += 1
                        self.total_entries += 1
                        self.current_occupancy += 1
                
                # Mark as crossed
                track.crossed_line = True
                track.direction = direction
                
                # Notify dwell tracker if enabled
                if self.dwell_tracker:
                    from datetime import datetime
                    if direction == 'entry':
                        self.dwell_tracker.record_entry(track_id, datetime.now())
                    elif direction == 'exit':
                        self.dwell_tracker.record_exit(track_id, datetime.now())
                
                logger.info(f"Track {track_id}: {direction} detected "
                          f"(Occupancy: {self.current_occupancy})")
            
            # Update state
            self.track_states[track_id] = current_side
        
        # Clean up states for deregistered tracks
        active_ids = set(tracks.keys())
        inactive_ids = set(self.track_states.keys()) - active_ids
        for track_id in inactive_ids:
            del self.track_states[track_id]
        
        return new_entries, new_exits
    
    def get_occupancy(self) -> int:
        """Get current occupancy count."""
        return max(0, self.current_occupancy)  # Don't go negative
    
    def get_stats(self) -> Dict:
        """Get all counting statistics."""
        return {
            'total_entries': self.total_entries,
            'total_exits': self.total_exits,
            'current_occupancy': self.get_occupancy(),
            'active_tracks': len(self.tracker.tracks)
        }
    
    def reset(self):
        """Reset all counters."""
        self.total_entries = 0
        self.total_exits = 0
        self.current_occupancy = 0
        self.tracker = CentroidTracker()
        self.track_states = {}
        logger.info("Counter reset")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Entry/Exit Counter")
    print("=" * 60)
    
    # Simulate doorway at y=300 in a 640x480 frame
    counter = EntryExitCounter(counting_line_y=300, frame_height=480)
    
    # Simulate person walking through doorway
    # Starting above line (y=250), moving down to below line (y=350)
    path = [
        [(320, 250)],  # Frame 1: above line
        [(320, 270)],  # Frame 2: still above
        [(320, 290)],  # Frame 3: approaching line
        [(320, 310)],  # Frame 4: crossed! (entry)
        [(320, 330)],  # Frame 5: below line
        [(320, 350)],  # Frame 6: fully below
    ]
    
    for frame_num, detections in enumerate(path, 1):
        entries, exits = counter.update(detections)
        stats = counter.get_stats()
        
        print(f"Frame {frame_num}: Entries={entries}, Exits={exits}, "
              f"Occupancy={stats['current_occupancy']}")
    
    print("\nFinal Statistics:")
    print(counter.get_stats())
