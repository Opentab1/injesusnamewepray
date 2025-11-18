"""
Hailo Integration Module

This module provides the interface to the Hailo AI HAT for real-time
person detection and counting in the bar environment.
"""

from .people_detector import PeopleDetector
from .counting_logic import EntryExitCounter
from .occupancy_tracker import OccupancyTracker

__all__ = ['PeopleDetector', 'EntryExitCounter', 'OccupancyTracker']
