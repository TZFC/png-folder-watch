"""
Watchdog folder monitoring manager for PNG Folder Watch.
Monitors configured folders recursively for new PNG images,
handles debouncing, and triggers conversion.
"""

import os
import threading
import time
from typing import Dict, Any, Callable, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .converter import convert_png_to_jpg, compute_target_path


class PNGEventHandler(FileSystemEventHandler):
    """Event handler for detecting new PNG files."""

    def __init__(
        self,
        rule: Dict[str, Any],
        on_converted: Optional[Callable[[Dict[str, Any], str, str, bool], None]] = None,
    ):
        super().__init__()
        self.rule = rule
        self.on_converted = on_converted
        self._processed: Dict[str, float] = {}  # filepath -> timestamp
        self._lock = threading.Lock()

    def _should_process(self, path: str) -> bool:
        if not path or not path.lower().endswith(".png"):
            return False

        # Ignore temporary files
        filename = os.path.basename(path)
        if filename.startswith("~$") or filename.startswith("."):
            return False

        now = time.time()
        with self._lock:
            # Clean up old records (>30s)
            self._processed = {
                k: v for k, v in self._processed.items() if now - v < 30.0
            }

            norm_path = os.path.normcase(os.path.abspath(path))
            last_time = self._processed.get(norm_path, 0)
            if now - last_time < 3.0:
                return False  # Debounce

            self._processed[norm_path] = now
            return True

    def _handle_event(self, path: str):
        if not self._should_process(path):
            return

        def task():
            # Small delay to ensure file write stream is open/committing
            time.sleep(0.4)
            success, msg, target_path, deleted = convert_png_to_jpg(path, self.rule)
            print(f"[Watcher:{self.rule.get('name')}] {msg}")
            if success and self.on_converted:
                self.on_converted(self.rule, path, target_path, deleted)

        # Run in separate thread so watchdog observer isn't blocked
        t = threading.Thread(target=task, daemon=True)
        t.start()

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_event(event.src_path)

    def on_moved(self, event: FileSystemEvent):
        if not event.is_directory and hasattr(event, "dest_path"):
            self._handle_event(event.dest_path)


class WatcherManager:
    """Manages active Watchdog Observers for all rules."""

    def __init__(self, on_converted: Optional[Callable[[Dict[str, Any], str, str, bool], None]] = None):
        self.on_converted = on_converted
        self._observers: Dict[str, Observer] = {}  # rule_id -> Observer
        self._lock = threading.Lock()
        self._paused = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def process_existing_files(self, rule: Dict[str, Any]):
        """Scan folder and convert unconverted existing PNG files."""
        watch_folder = rule.get("watch_folder", "")
        if not watch_folder or not os.path.exists(watch_folder):
            return

        output_mode = rule.get("output_mode", "same_folder")

        def scan_task():
            count = 0
            for root, _, files in os.walk(watch_folder):
                for f in files:
                    if f.lower().endswith(".png"):
                        png_path = os.path.join(root, f)
                        target_path = compute_target_path(png_path, watch_folder, output_mode)

                        # Check if target already exists and is newer
                        if os.path.exists(target_path):
                            try:
                                if os.path.getmtime(target_path) >= os.path.getmtime(png_path):
                                    continue
                            except OSError:
                                pass

                        success, msg, tgt, deleted = convert_png_to_jpg(png_path, rule)
                        if success:
                            count += 1
                            if self.on_converted:
                                self.on_converted(rule, png_path, tgt, deleted)
            if count > 0:
                print(f"[Watcher:{rule.get('name')}] Converted {count} existing PNG(s)")

        t = threading.Thread(target=scan_task, daemon=True)
        t.start()

    def start_rule(self, rule: Dict[str, Any]) -> bool:
        """Start watching folder for a single rule."""
        rule_id = rule.get("id")
        if not rule_id:
            return False

        watch_folder = rule.get("watch_folder")
        if not watch_folder or not os.path.exists(watch_folder):
            print(f"[WatcherManager] Watch folder does not exist: {watch_folder}")
            return False

        with self._lock:
            # Stop if already running
            if rule_id in self._observers:
                self._stop_observer_unlocked(rule_id)

            # Convert existing files if requested
            if rule.get("process_existing", True):
                self.process_existing_files(rule)

            handler = PNGEventHandler(
                rule=rule,
                on_converted=lambda r, p, t, d: self._safe_on_converted(r, p, t, d),
            )
            observer = Observer()
            try:
                observer.schedule(handler, path=watch_folder, recursive=True)
                observer.start()
                self._observers[rule_id] = observer
                print(f"[WatcherManager] Started watching '{rule.get('name')}' -> {watch_folder}")
                return True
            except Exception as e:
                print(f"[WatcherManager] Error starting observer for {watch_folder}: {e}")
                return False

    def _safe_on_converted(self, rule: Dict[str, Any], png_path: str, target_path: str, deleted: bool):
        if not self._paused and self.on_converted:
            try:
                self.on_converted(rule, png_path, target_path, deleted)
            except Exception as e:
                print(f"[WatcherManager] on_converted callback error: {e}")

    def stop_rule(self, rule_id: str):
        """Stop watching for a specific rule ID."""
        with self._lock:
            self._stop_observer_unlocked(rule_id)

    def _stop_observer_unlocked(self, rule_id: str):
        if rule_id in self._observers:
            obs = self._observers.pop(rule_id)
            try:
                obs.stop()
                obs.join(timeout=2.0)
            except Exception as e:
                print(f"[WatcherManager] Error stopping observer: {e}")

    def is_rule_active(self, rule_id: str) -> bool:
        with self._lock:
            obs = self._observers.get(rule_id)
            return obs is not None and obs.is_alive()

    def get_active_count(self) -> int:
        with self._lock:
            return sum(1 for obs in self._observers.values() if obs.is_alive())

    def stop_all(self):
        """Stop all active watchers."""
        with self._lock:
            for rule_id, obs in list(self._observers.items()):
                try:
                    obs.stop()
                    obs.join(timeout=1.5)
                except Exception:
                    pass
            self._observers.clear()
            print("[WatcherManager] Stopped all watchers.")
