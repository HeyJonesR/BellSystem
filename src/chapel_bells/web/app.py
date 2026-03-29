"""
Flask web administration interface for ChapelBells.
Provides dashboard, schedule editor, and system settings.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, session
import logging

logger = logging.getLogger(__name__)


class ChapelBellsWeb:
    """Flask application for ChapelBells admin interface."""
    
    def __init__(self, app_instance):
        """
        Initialize web interface.
        
        Args:
            app_instance: ChapelBells application instance
        """
        self.app = Flask(__name__)
        self.app.secret_key = os.environ.get("CHAPEL_BELLS_SECRET", "change-me-in-production")
        self.bell_app = app_instance
        
        # Register routes
        self._register_routes()
    
    def _require_auth(self, f):
        """Decorator to require authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple check - in production use proper auth
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Unauthorized"}), 401
            
            token = auth[7:]  # Remove "Bearer "
            # TODO: validate token against configured tokens
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def _register_routes(self):
        """Register Flask routes."""
        
        @self.app.route("/")
        def dashboard():
            """Main dashboard."""
            status = self.bell_app.get_status()
            events = self.bell_app.scheduler.get_events()
            history = self.bell_app.scheduler.get_playback_history(20)
            
            return render_template(
                "dashboard.html",
                status=status,
                events=[e.to_dict() for e in events],
                history=history
            )
        
        @self.app.route("/api/status")
        def api_status():
            """Get system status (JSON)."""
            return jsonify(self.bell_app.get_status())
        
        @self.app.route("/api/events")
        def api_events():
            """Get all scheduled events."""
            events = self.bell_app.scheduler.get_events()
            return jsonify([e.to_dict() for e in events])
        
        @self.app.route("/api/events", methods=["POST"])
        def api_events_create():
            """Create new event."""
            data = request.get_json()
            
            try:
                from chapel_bells.scheduler import BellEvent
                event = BellEvent(
                    name=data["name"],
                    rule=data["rule"],
                    profile=data.get("profile", "westminster"),
                    tone=data.get("tone", "bell"),
                    active_after=data.get("active_after"),
                    active_before=data.get("active_before"),
                    description=data.get("description", "")
                )
                self.bell_app.scheduler.add_event(event)
                
                return jsonify({
                    "status": "success",
                    "event": event.to_dict()
                }), 201
            
            except Exception as e:
                logger.error(f"Error creating event: {e}")
                return jsonify({"error": str(e)}), 400
        
        @self.app.route("/api/events/<event_name>", methods=["DELETE"])
        def api_events_delete(event_name):
            """Delete event by name."""
            try:
                self.bell_app.scheduler.delete_event(event_name)
                return jsonify({"status": "success"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 400
        
        @self.app.route("/api/quiet-hours")
        def api_quiet_hours():
            """Get quiet hours configuration."""
            return jsonify(self.bell_app.scheduler.quiet_hours.to_dict())
        
        @self.app.route("/api/quiet-hours", methods=["PUT"])
        def api_quiet_hours_update():
            """Update quiet hours."""
            data = request.get_json()
            
            try:
                from chapel_bells.scheduler import QuietHours
                quiet_hours = QuietHours(
                    enabled=data.get("enabled", True),
                    start=data.get("start", "21:00"),
                    end=data.get("end", "07:00"),
                    override_dates=data.get("override_dates", [])
                )
                self.bell_app.scheduler.set_quiet_hours(quiet_hours)
                
                return jsonify({"status": "success", "data": quiet_hours.to_dict()})
            except Exception as e:
                return jsonify({"error": str(e)}), 400
        
        @self.app.route("/api/audio/profiles")
        def api_audio_profiles():
            """Get available audio profiles."""
            return jsonify(self.bell_app.audio_engine.get_available_profiles())
        
        @self.app.route("/api/audio/play", methods=["POST"])
        def api_audio_play():
            """Test audio playback."""
            data = request.get_json()
            profile = data.get("profile", "westminster")
            tone = data.get("tone", "bell")
            
            success = self.bell_app.audio_engine.play(profile, tone, wait=False)
            
            return jsonify({
                "status": "success" if success else "failed",
                "message": f"Playing {profile}/{tone}"
            })
        
        @self.app.route("/api/history")
        def api_history():
            """Get bell playback history."""
            limit = request.args.get("limit", 100, type=int)
            history = self.bell_app.scheduler.get_playback_history(limit)
            return jsonify(history)
        
        @self.app.route("/api/settings")
        def api_settings():
            """Get application settings."""
            return jsonify({
                "astro": {
                    "latitude": self.bell_app.astro.latitude,
                    "longitude": self.bell_app.astro.longitude
                },
                "audio": {
                    "volume": self.bell_app.audio_engine.config.volume,
                    "backend": self.bell_app.audio_engine.config.backend
                }
            })
        
        @self.app.route("/api/settings/astro", methods=["PUT"])
        def api_settings_astro():
            """Update astronomical settings."""
            data = request.get_json()
            
            try:
                from chapel_bells.astro import AstronomicalCalculator
                self.bell_app.astro = AstronomicalCalculator(
                    latitude=float(data["latitude"]),
                    longitude=float(data["longitude"]),
                    timezone_offset=int(data.get("timezone_offset", -5))
                )
                return jsonify({"status": "success"})
            except Exception as e:
                return jsonify({"error": str(e)}), 400
        
        @self.app.route("/api/settings/audio", methods=["PUT"])
        def api_settings_audio():
            """Update audio settings."""
            data = request.get_json()
            
            if "volume" in data:
                self.bell_app.audio_engine.set_volume(int(data["volume"]))
            
            return jsonify({"status": "success"})
        
        @self.app.route("/api/export")
        def api_export():
            """Export configuration as JSON."""
            config_json = self.bell_app.scheduler.to_json()
            return config_json, 200, {"Content-Type": "application/json"}
    
    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """Start the web server."""
        logger.info(f"Starting web server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


# Minimal HTML template (can be extended with full UI)
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ChapelBells Admin</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header h1 { color: #333; margin-bottom: 10px; }
        .status { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .status-item { background: #f9f9f9; padding: 15px; border-radius: 6px; }
        .status-item label { display: block; font-size: 12px; color: #666; margin-bottom: 5px; font-weight: 600; }
        .status-item .value { font-size: 14px; color: #333; }
        .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h2 { color: #333; margin-bottom: 15px; font-size: 18px; }
        .event-list { list-style: none; }
        .event-item { background: #f9f9f9; padding: 12px; border-left: 3px solid #007bff; margin-bottom: 10px; border-radius: 4px; }
        .event-item strong { display: block; margin-bottom: 4px; }
        .event-item small { color: #666; }
        button { background: #007bff; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; font-size: 14px; }
        button:hover { background: #0056b3; }
        input, select, textarea { width: 100%; padding: 10px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        .form-group { margin-bottom: 15px; }
        .alert { padding: 12px; background: #d4edda; color: #155724; border: 1px solid #c3e6cb; border-radius: 4px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 ChapelBells Administration</h1>
            <div class="status">
                <div class="status-item">
                    <label>Status</label>
                    <div class="value" id="status-running">Loading...</div>
                </div>
                <div class="status-item">
                    <label>Current Time</label>
                    <div class="value" id="status-time">Loading...</div>
                </div>
                <div class="status-item">
                    <label>Sunrise / Sunset</label>
                    <div class="value" id="status-sun">Loading...</div>
                </div>
                <div class="status-item">
                    <label>Quiet Hours</label>
                    <div class="value" id="status-quiet">Loading...</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Scheduled Events</h2>
            <ul class="event-list" id="events-list">
                <li>Loading events...</li>
            </ul>
        </div>
        
        <div class="card">
            <h2>Recent Playback</h2>
            <ul class="event-list" id="history-list">
                <li>Loading history...</li>
            </ul>
        </div>
    </div>
    
    <script>
        async function updateDashboard() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                document.getElementById('status-running').textContent = status.running ? '✓ Running' : '✗ Stopped';
                document.getElementById('status-time').textContent = new Date(status.current_time).toLocaleTimeString();
                document.getElementById('status-quiet').textContent = status.quiet_hours_enabled ? `${status.quiet_hours.start} - ${status.quiet_hours.end}` : 'Disabled';
                
                if (status.sunrise && status.sunset) {
                    const sunrise = new Date(status.sunrise).toLocaleTimeString();
                    const sunset = new Date(status.sunset).toLocaleTimeString();
                    document.getElementById('status-sun').textContent = `↑${sunrise} ↓${sunset}`;
                }
            } catch (e) {
                console.error('Error fetching status:', e);
            }
        }
        
        async function loadEvents() {
            try {
                const response = await fetch('/api/events');
                const events = await response.json();
                const list = document.getElementById('events-list');
                
                if (events.length === 0) {
                    list.innerHTML = '<li>No events scheduled</li>';
                    return;
                }
                
                list.innerHTML = events.map(e => `
                    <li class="event-item">
                        <strong>${e.name}</strong>
                        <small>${e.rule} | ${e.profile}/${e.tone}</small>
                    </li>
                `).join('');
            } catch (e) {
                console.error('Error loading events:', e);
            }
        }
        
        async function loadHistory() {
            try {
                const response = await fetch('/api/history?limit=10');
                const history = await response.json();
                const list = document.getElementById('history-list');
                
                if (history.length === 0) {
                    list.innerHTML = '<li>No bell playback yet</li>';
                    return;
                }
                
                list.innerHTML = history.map(h => `
                    <li class="event-item">
                        <strong>${h.event}</strong>
                        <small>${new Date(h.time).toLocaleString()} | ${h.profile}/${h.tone}</small>
                    </li>
                `).join('');
            } catch (e) {
                console.error('Error loading history:', e);
            }
        }
        
        // Update dashboard every 5 seconds
        updateDashboard();
        loadEvents();
        loadHistory();
        
        setInterval(updateDashboard, 5000);
        setInterval(loadHistory, 10000);
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    # Example standalone usage
    from chapel_bells import ChapelBells
    
    bell_app = ChapelBells()
    web_app = ChapelBellsWeb(bell_app)
    
    # In production, run bell_app in background thread
    # For now, just start web server
    web_app.run(host="0.0.0.0", port=5000, debug=True)
