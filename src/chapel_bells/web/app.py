"""
Flask web administration interface for ChapelBells.
Provides dashboard, schedule editor, and system settings.
"""

import json
import os
import re
import secrets
from pathlib import Path
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, session
from markupsafe import escape
import logging

logger = logging.getLogger(__name__)

# Max items returned from history endpoint
MAX_HISTORY_LIMIT = 500


class ChapelBellsWeb:
    """Flask application for ChapelBells admin interface."""
    
    def __init__(self, app_instance):
        """
        Initialize web interface.
        
        Args:
            app_instance: ChapelBells application instance
        """
        # Initialize Flask with correct template folder
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.app = Flask(__name__, template_folder=template_dir)
        self.app.secret_key = os.environ.get("CHAPEL_BELLS_SECRET") or secrets.token_hex(32)
        self.bell_app = app_instance
        
        # Load API tokens from environment (comma-separated)
        tokens_env = os.environ.get("CHAPEL_BELLS_API_TOKENS", "")
        self._api_tokens = {t.strip() for t in tokens_env.split(",") if t.strip()}
        if not self._api_tokens:
            # Generate a one-time token and log it so the admin can capture it
            generated = secrets.token_urlsafe(32)
            self._api_tokens = {generated}
            logger.warning(
                "No CHAPEL_BELLS_API_TOKENS set. Generated token: %s  "
                "Set CHAPEL_BELLS_API_TOKENS env var for persistence.",
                generated,
            )
        
        # Register security headers
        self._register_security_headers()
        
        # Register routes
        self._register_routes()
    
    def _register_security_headers(self):
        """Add security headers to all responses."""
        @self.app.after_request
        def add_security_headers(response):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            )
            response.headers["Cache-Control"] = "no-store"
            return response
    
    def _require_auth(self, f):
        """Decorator to require Bearer-token authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Unauthorized"}), 401
            
            token = auth[7:]
            if token not in self._api_tokens:
                logger.warning("Rejected invalid API token from %s", request.remote_addr)
                return jsonify({"error": "Unauthorized"}), 401
            
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
        @self._require_auth
        def api_events_create():
            """Create new event."""
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON body required"}), 400
            
            # Validate required fields
            name = data.get("name", "")
            rule = data.get("rule", "")
            if not name or not isinstance(name, str) or len(name) > 100:
                return jsonify({"error": "name is required (max 100 chars)"}), 400
            if not re.match(r'^[\w\s\-:*/]+$', name):
                return jsonify({"error": "name contains invalid characters"}), 400
            if not rule or not isinstance(rule, str) or len(rule) > 200:
                return jsonify({"error": "rule is required (max 200 chars)"}), 400
            
            try:
                from chapel_bells.scheduler import BellEvent
                event = BellEvent(
                    name=name.strip(),
                    rule=rule.strip(),
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
        @self._require_auth
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
        @self._require_auth
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

        @self.app.route("/api/audio/tones/<profile>")
        def api_audio_tones(profile):
            """Get available tones for a given audio profile."""
            tones = list(self.bell_app.audio_engine.profiles.get(profile, {}).keys())
            if not tones:
                # Profile exists as an enum but has no loaded files; return empty list
                return jsonify([])
            return jsonify(tones)

        @self.app.route("/api/events/<event_name>", methods=["PUT"])
        @self._require_auth
        def api_events_update(event_name):
            """Update an existing event by deleting and recreating it."""
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON body required"}), 400

            # Validate required fields
            name = data.get("name", event_name)
            rule = data.get("rule", "")
            if not name or not isinstance(name, str) or len(name) > 100:
                return jsonify({"error": "name is required (max 100 chars)"}), 400
            if not re.match(r'^[\w\s\-:*/]+$', name):
                return jsonify({"error": "name contains invalid characters"}), 400
            if not rule or not isinstance(rule, str) or len(rule) > 200:
                return jsonify({"error": "rule is required (max 200 chars)"}), 400

            try:
                from chapel_bells.scheduler import BellEvent
                # Delete the existing event first
                self.bell_app.scheduler.delete_event(event_name)
                # Recreate with updated data
                event = BellEvent(
                    name=name.strip(),
                    rule=rule.strip(),
                    profile=data.get("profile", "westminster"),
                    tone=data.get("tone", "bell"),
                    active_after=data.get("active_after"),
                    active_before=data.get("active_before"),
                    description=data.get("description", "")
                )
                self.bell_app.scheduler.add_event(event)
                return jsonify({"status": "success", "event": event.to_dict()})
            except Exception as e:
                logger.error(f"Error updating event: {e}")
                return jsonify({"error": str(e)}), 400

        @self.app.route("/api/audio/play", methods=["POST"])
        @self._require_auth
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
            limit = min(request.args.get("limit", 100, type=int), MAX_HISTORY_LIMIT)
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
        @self._require_auth
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
        @self._require_auth
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
    
    def run(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """Start the web server (dev only; use gunicorn in production)."""
        logger.info(f"Starting web server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_app():
    """WSGI application factory for gunicorn / production use."""
    from chapel_bells import ChapelBells
    bell_app = ChapelBells()
    bell_app.start()
    web = ChapelBellsWeb(bell_app)
    return web.app


if __name__ == "__main__":
    from chapel_bells import ChapelBells
    
    bell_app = ChapelBells()
    web_app = ChapelBellsWeb(bell_app)
    web_app.run(host="127.0.0.1", port=5000, debug=False)
