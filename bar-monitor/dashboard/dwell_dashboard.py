"""
Real-Time Dwell Time Dashboard for Staff

A simple web dashboard showing:
- Current customers and their dwell times
- Color-coded alerts (green/yellow/red)
- Camper warnings
- Daily statistics

USAGE:
    python dashboard/dwell_dashboard.py
    
    Then open browser to: http://localhost:5000
    Or from tablet: http://[pi-ip-address]:5000
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hailo_integration.dwell_time_tracker import DwellTimeTracker
from analytics.dwell_analytics import DwellAnalytics

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Initialize tracker and analytics
dwell_tracker = None
dwell_analytics = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_tracker(db_path='data/dwell_time.db'):
    """Initialize global tracker and analytics."""
    global dwell_tracker, dwell_analytics
    
    try:
        dwell_tracker = DwellTimeTracker(
            db_path=db_path,
            warning_threshold=90,
            alert_threshold=120
        )
        dwell_analytics = DwellAnalytics(db_path=db_path)
        logger.info("Dashboard initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize dashboard: {e}")


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dwell_dashboard.html')


@app.route('/api/current')
def api_current():
    """
    API endpoint for current dwell time status.
    
    Returns JSON with:
    - active_sessions: List of current customers
    - campers: List of people over alert threshold
    - warnings: List of people approaching threshold
    - statistics: Current day stats
    """
    if not dwell_tracker:
        return jsonify({'error': 'Tracker not initialized'}), 500
    
    # Get active sessions
    active = dwell_tracker.get_active_sessions()
    active_data = []
    
    for session in active:
        dwell_min = session.get_current_dwell_minutes()
        
        # Determine status
        if dwell_min >= dwell_tracker.alert_threshold:
            status = 'alert'
            color = 'red'
        elif dwell_min >= dwell_tracker.warning_threshold:
            status = 'warning'
            color = 'yellow'
        else:
            status = 'good'
            color = 'green'
        
        active_data.append({
            'track_id': session.track_id,
            'dwell_minutes': round(dwell_min, 1),
            'entry_time': session.entry_time.strftime('%H:%M'),
            'status': status,
            'color': color
        })
    
    # Sort by dwell time (longest first)
    active_data.sort(key=lambda x: x['dwell_minutes'], reverse=True)
    
    # Get campers and warnings
    campers = dwell_tracker.get_campers()
    warnings = dwell_tracker.get_warnings()
    
    # Get today's stats
    try:
        daily_report = dwell_analytics.generate_daily_report()
        stats = {
            'total_visits_today': daily_report['total_visits'],
            'avg_dwell_today': daily_report['avg_dwell_minutes'],
            'campers_today': daily_report['campers_90min'],
            'revenue_opportunity_today': daily_report['revenue_optimization']['potential_daily_revenue_gain']
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        stats = {
            'total_visits_today': 0,
            'avg_dwell_today': 0,
            'campers_today': 0,
            'revenue_opportunity_today': 0
        }
    
    return jsonify({
        'active_count': len(active_data),
        'camper_count': len(campers),
        'warning_count': len(warnings),
        'active_sessions': active_data,
        'statistics': stats,
        'thresholds': {
            'warning': dwell_tracker.warning_threshold,
            'alert': dwell_tracker.alert_threshold
        }
    })


@app.route('/api/recommendations')
def api_recommendations():
    """API endpoint for actionable recommendations."""
    if not dwell_analytics:
        return jsonify({'error': 'Analytics not initialized'}), 500
    
    try:
        recommendations = dwell_analytics.get_recommendations()
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/weekly')
def api_weekly():
    """API endpoint for weekly trends."""
    if not dwell_analytics:
        return jsonify({'error': 'Analytics not initialized'}), 500
    
    try:
        weekly = dwell_analytics.generate_weekly_report()
        return jsonify(weekly)
    except Exception as e:
        logger.error(f"Error getting weekly data: {e}")
        return jsonify({'error': str(e)}), 500


# Create templates directory if it doesn't exist
TEMPLATES_DIR = Path(__file__).parent / 'templates'
TEMPLATES_DIR.mkdir(exist_ok=True)


# Create the HTML template
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dwell Time Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #1a1a1a;
            color: #ffffff;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }
        
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            font-size: 16px;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        
        .stat-card .label {
            font-size: 12px;
            text-transform: uppercase;
            color: #999;
            margin-bottom: 5px;
        }
        
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
        }
        
        .stat-card.alert {
            border-left-color: #ff6b6b;
        }
        
        .stat-card.warning {
            border-left-color: #ffd93d;
        }
        
        .active-sessions {
            background: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .active-sessions h2 {
            margin-bottom: 20px;
            font-size: 24px;
        }
        
        .session-list {
            display: grid;
            gap: 10px;
        }
        
        .session-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: #1a1a1a;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .session-item.green {
            border-left-color: #51cf66;
        }
        
        .session-item.yellow {
            border-left-color: #ffd93d;
        }
        
        .session-item.red {
            border-left-color: #ff6b6b;
        }
        
        .session-info {
            flex: 1;
        }
        
        .session-id {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .session-time {
            font-size: 14px;
            color: #999;
        }
        
        .session-dwell {
            font-size: 24px;
            font-weight: bold;
            text-align: right;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .refresh-info {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 20px;
        }
        
        .alert-banner {
            background: #ff6b6b;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-weight: bold;
            display: none;
        }
        
        .alert-banner.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🍺 Dwell Time Monitor</h1>
        <p class="subtitle">Real-time customer visit tracking</p>
    </div>
    
    <div class="alert-banner" id="alertBanner">
        ⚠️ Multiple customers over 2 hours - consider encouraging turnover
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">Currently Inside</div>
            <div class="value" id="activeCount">-</div>
        </div>
        
        <div class="stat-card warning">
            <div class="label">Warnings (90+ min)</div>
            <div class="value" id="warningCount">-</div>
        </div>
        
        <div class="stat-card alert">
            <div class="label">Campers (120+ min)</div>
            <div class="value" id="camperCount">-</div>
        </div>
        
        <div class="stat-card">
            <div class="label">Avg Today</div>
            <div class="value" id="avgDwell">-</div>
        </div>
    </div>
    
    <div class="active-sessions">
        <h2>Active Customers</h2>
        <div class="session-list" id="sessionList">
            <div class="empty-state">
                Loading...
            </div>
        </div>
    </div>
    
    <div class="refresh-info">
        Auto-refreshing every 5 seconds
    </div>
    
    <script>
        function updateDashboard() {
            fetch('/api/current')
                .then(response => response.json())
                .then(data => {
                    // Update stats
                    document.getElementById('activeCount').textContent = data.active_count;
                    document.getElementById('warningCount').textContent = data.warning_count;
                    document.getElementById('camperCount').textContent = data.camper_count;
                    document.getElementById('avgDwell').textContent = 
                        Math.round(data.statistics.avg_dwell_today) + 'm';
                    
                    // Show alert banner if campers present
                    const banner = document.getElementById('alertBanner');
                    if (data.camper_count > 0) {
                        banner.classList.add('show');
                    } else {
                        banner.classList.remove('show');
                    }
                    
                    // Update session list
                    const listEl = document.getElementById('sessionList');
                    
                    if (data.active_sessions.length === 0) {
                        listEl.innerHTML = '<div class="empty-state">No customers currently tracked</div>';
                    } else {
                        listEl.innerHTML = data.active_sessions.map(session => `
                            <div class="session-item ${session.color}">
                                <div class="session-info">
                                    <div class="session-id">Customer #${session.track_id}</div>
                                    <div class="session-time">Entered at ${session.entry_time}</div>
                                </div>
                                <div class="session-dwell">${Math.round(session.dwell_minutes)}m</div>
                            </div>
                        `).join('');
                    }
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                });
        }
        
        // Initial load
        updateDashboard();
        
        // Auto-refresh every 5 seconds
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>'''

# Write the template file
with open(TEMPLATES_DIR / 'dwell_dashboard.html', 'w') as f:
    f.write(HTML_TEMPLATE)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Dwell Time Dashboard')
    parser.add_argument('--db', default='data/dwell_time.db', help='Path to dwell time database')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', default=5000, type=int, help='Port to bind to')
    
    args = parser.parse_args()
    
    # Initialize tracker
    init_tracker(args.db)
    
    print("=" * 60)
    print("  DWELL TIME DASHBOARD STARTING")
    print("=" * 60)
    print(f"\n  📊 Dashboard URL: http://localhost:{args.port}")
    print(f"  📱 From tablet: http://[your-pi-ip]:{args.port}")
    print(f"  📂 Database: {args.db}")
    print("\n  Press Ctrl+C to stop\n")
    print("=" * 60)
    
    # Run Flask app
    app.run(host=args.host, port=args.port, debug=False)
