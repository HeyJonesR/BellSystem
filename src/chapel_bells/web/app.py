"""
Flask web dashboard for ChapelBells.
Provides a simple UI to view the schedule, trigger bells manually,
and adjust volume.
"""

import logging
import os
import re

from flask import Flask, jsonify, render_template, request

logger = logging.getLogger(__name__)


def create_web_app(scheduler, player) -> Flask:
    """
    Create and return the Flask application.

    Args:
        scheduler: BellScheduler instance
        player:    AudioPlayer instance
    """
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    app = Flask(__name__, template_folder=template_dir)

    # ------------------------------------------------------------------
    # Security headers
    # ------------------------------------------------------------------
    @app.after_request
    def _security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------
    @app.route("/")
    def dashboard():
        return render_template(
            "dashboard.html",
            bells=scheduler.bells,
            history=scheduler.get_history(20),
            status=scheduler.get_status(),
            volume=player.volume,
        )

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    @app.route("/api/status")
    def api_status():
        return jsonify(scheduler.get_status())

    @app.route("/api/schedule")
    def api_schedule():
        return jsonify(scheduler.bells)

    @app.route("/api/history")
    def api_history():
        limit = min(request.args.get("limit", 50, type=int), 200)
        return jsonify(scheduler.get_history(limit))

    @app.route("/api/trigger", methods=["POST"])
    def api_trigger():
        """Manually play a bell sound."""
        data = request.get_json(silent=True) or {}
        sound = data.get("sound", "")
        if not sound or not isinstance(sound, str):
            return jsonify({"error": "sound filename required"}), 400
        # Prevent path traversal
        if ".." in sound or sound.startswith("/"):
            return jsonify({"error": "invalid sound filename"}), 400
        ok = scheduler.trigger_sound(sound)
        return jsonify({"status": "ok" if ok else "error"})

    @app.route("/api/volume", methods=["PUT"])
    def api_volume():
        """Set playback volume (0–100)."""
        data = request.get_json(silent=True) or {}
        try:
            vol = int(data.get("volume", player.volume))
        except (TypeError, ValueError):
            return jsonify({"error": "volume must be an integer 0–100"}), 400
        player.set_volume(vol)
        return jsonify({"volume": player.volume})

    @app.route("/api/stop", methods=["POST"])
    def api_stop():
        """Stop all currently playing sounds."""
        player.stop()
        return jsonify({"status": "ok"})

    # ------------------------------------------------------------------
    # Schedule CRUD
    # ------------------------------------------------------------------

    def _parse_bell(data):
        """Validate and return a clean bell dict, or raise ValueError."""
        time_ = data.get("time", "")
        sound = data.get("sound", "")
        if not time_ or not isinstance(time_, str):
            raise ValueError("time required (HH:MM)")
        if not re.match(r"^\d{2}:\d{2}$", time_):
            raise ValueError("time must be HH:MM format")
        if not sound or not isinstance(sound, str):
            raise ValueError("sound filename required")
        if ".." in sound or sound.startswith("/"):
            raise ValueError("invalid sound filename")
        bell = {"time": time_, "sound": sound}
        if "count" in data:
            try:
                bell["count"] = max(1, int(data["count"]))
            except (TypeError, ValueError):
                raise ValueError("count must be an integer >= 1")
        if "interval" in data:
            try:
                bell["interval"] = max(0.5, float(data["interval"]))
            except (TypeError, ValueError):
                raise ValueError("interval must be a number >= 0.5")
        return bell

    @app.route("/api/sounds")
    def api_sounds():
        """List available sound files under audio_samples/ with friendly labels."""
        from pathlib import Path
        import re as _re
        audio_dir = Path(player.audio_dir)

        def _label(rel_path: str) -> str:
            """Turn a file path into a readable label."""
            parts = Path(rel_path).parts
            stem = Path(rel_path).stem
            # Strip leading numeric IDs like '458297__author__actual-name'
            stem = _re.sub(r'^\d+__[^_]+__', '', stem)
            # Replace hyphens/underscores with spaces and title-case
            name = stem.replace('-', ' ').replace('_', ' ').title()
            # Prefix with folder name when name is too generic (e.g. just "Bell")
            if len(name) <= 6 and len(parts) > 1:
                folder = parts[-2].replace('-', ' ').replace('_', ' ').title()
                name = f"{folder} \u2013 {name}"
            return name

        sounds = sorted(
            [
                {
                    "path": str(f.relative_to(audio_dir)).replace("\\", "/"),
                    "label": _label(str(f.relative_to(audio_dir))),
                }
                for f in audio_dir.rglob("*")
                if f.suffix.lower() in (".wav", ".mp3") and f.is_file()
            ],
            key=lambda s: s["path"],
        )
        return jsonify(sounds)

    @app.route("/api/schedule", methods=["POST"])
    def api_schedule_add():
        """Add a new bell entry."""
        data = request.get_json(silent=True) or {}
        try:
            bell = _parse_bell(data)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        scheduler.add_bell(bell)
        return jsonify({"status": "ok", "bells": scheduler.bells}), 201

    @app.route("/api/schedule/<int:idx>", methods=["PUT"])
    def api_schedule_update(idx):
        """Update a bell entry by index."""
        data = request.get_json(silent=True) or {}
        try:
            bell = _parse_bell(data)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        try:
            scheduler.update_bell(idx, bell)
        except IndexError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"status": "ok", "bells": scheduler.bells})

    @app.route("/api/schedule/<int:idx>", methods=["DELETE"])
    def api_schedule_delete(idx):
        """Delete a bell entry by index."""
        try:
            scheduler.delete_bell(idx)
        except IndexError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"status": "ok", "bells": scheduler.bells})

    @app.route("/api/quiet_hours", methods=["PUT"])
    def api_quiet_hours():
        """Update quiet hours settings."""
        data = request.get_json(silent=True) or {}
        enabled = bool(data.get("enabled", False))
        # Accept HH:MM or HH:MM:SS (browser time inputs may include seconds)
        start = str(data.get("start", "22:00"))[:5]
        end = str(data.get("end", "07:00"))[:5]
        if not re.match(r"^\d{2}:\d{2}$", start) or not re.match(r"^\d{2}:\d{2}$", end):
            return jsonify({"error": "start and end must be HH:MM format"}), 400
        scheduler.update_quiet_hours(enabled, start, end)
        return jsonify(scheduler.get_status())

    return app
