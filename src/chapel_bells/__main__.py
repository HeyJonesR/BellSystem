"""
ChapelBells - Church Bell Automation System
Entry point: python -m chapel_bells [options]
"""

import argparse
import logging
import logging.handlers
import signal
import sys
import threading
import time
from pathlib import Path

from chapel_bells.scheduler import BellScheduler
from chapel_bells.audio import AudioPlayer


def setup_logging(log_file: str = None) -> None:
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3
        ))
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


def main() -> None:
    parser = argparse.ArgumentParser(description="ChapelBells – Church Bell Automation")
    parser.add_argument(
        "--config", default="config/schedule.json",
        help="Path to JSON or YAML schedule config (default: config/schedule.json)"
    )
    parser.add_argument(
        "--log-file", default=None,
        help="Optional log file path (logs to stdout by default)"
    )
    parser.add_argument(
        "--web", action="store_true",
        help="Also start the web dashboard"
    )
    parser.add_argument(
        "--port", type=int, default=5000,
        help="Web dashboard port (default: 5000)"
    )
    args = parser.parse_args()

    setup_logging(args.log_file)
    logger = logging.getLogger(__name__)

    # --- Scheduler (reads config; exposes audio_dir + volume) --------
    # Construct scheduler first so we read config only once.
    # Use a stub callback until the player is ready.
    scheduler = BellScheduler(config_path=args.config, play_callback=lambda _s: False)
    player = AudioPlayer(audio_dir=scheduler.audio_dir, volume=scheduler.volume)
    scheduler.play_callback = player.play
    scheduler.schedule_all()

    logger.info(
        "ChapelBells started. %d bell(s) scheduled. Config: %s",
        len(scheduler.bells), args.config
    )

    # --- Optional web UI ----------------------------------------------
    if args.web:
        from chapel_bells.web.app import create_web_app
        from threading import Thread
        flask_app = create_web_app(scheduler, player)
        t = Thread(
            target=lambda: flask_app.run(
                host="127.0.0.1", port=args.port, debug=False, use_reloader=False
            ),
            daemon=True,
            name="web-ui",
        )
        t.start()
        logger.info("Web dashboard: http://127.0.0.1:%d", args.port)

    # --- Signal handling (flag-based for clean shutdown) --------------
    _stop = threading.Event()

    def _shutdown(sig, frame):
        logger.info("Received signal %s – shutting down.", sig)
        _stop.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # --- Main loop ----------------------------------------------------
    while not _stop.is_set():
        scheduler.run_pending()
        _stop.wait(1)

    # --- Cleanup ------------------------------------------------------
    player.stop()
    player.close()
    logger.info("ChapelBells stopped.")


if __name__ == "__main__":
    main()
