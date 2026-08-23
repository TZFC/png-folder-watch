"""
Process Monitor for game/app-triggered folder rules.
Polls running Windows processes to dynamically activate or deactivate
watchers for each rule when its specific target game or application is running.
"""

import os
import time
import threading
from typing import Dict, Any, List, Set, Optional, Callable
import psutil

from .config import WATCH_MODE_ON_APP


class ProcessMonitor:
    """Monitors running processes and starts/stops individual rules based on their target apps."""

    def __init__(
        self,
        watcher_manager,
        poll_interval: float = 3.5,
        get_rules_callback: Optional[Callable[[], List[Dict[str, Any]]]] = None,
        on_rule_state_change: Optional[Callable[[Dict[str, Any], bool], None]] = None,
    ):
        self.watcher_manager = watcher_manager
        self.poll_interval = poll_interval
        self.get_rules_callback = get_rules_callback
        self.on_rule_state_change = on_rule_state_change
        self._active_rules: Set[str] = set()  # Set of rule IDs currently active due to running target app
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def set_rules_provider(self, get_rules_callback: Callable[[], List[Dict[str, Any]]]):
        with self._lock:
            self.get_rules_callback = get_rules_callback

    def is_rule_app_active(self, rule_id: str) -> bool:
        with self._lock:
            return rule_id in self._active_rules

    def get_active_app_rules_count(self) -> int:
        with self._lock:
            return len(self._active_rules)

    def start(self):
        """Start the background process monitoring loop."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            print("[ProcessMonitor] Started process monitoring loop for app-triggered rules.")

    def stop(self):
        """Stop monitoring."""
        with self._lock:
            self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        print("[ProcessMonitor] Stopped process monitoring.")

    def _get_running_process_names_and_paths(self) -> Set[str]:
        """Collect lowercased running executable names and paths."""
        names_and_paths = set()
        for p in psutil.process_iter(["name", "exe"]):
            try:
                name = p.info.get("name")
                if name:
                    names_and_paths.add(name.lower())
                exe = p.info.get("exe")
                if exe:
                    names_and_paths.add(os.path.normpath(exe).lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return names_and_paths

    def _is_target_running(self, rule: Dict[str, Any], running_set: Set[str]) -> bool:
        target_path = rule.get("target_app_path", "").strip()
        target_name = rule.get("target_app_name", "").strip()

        if not target_name and target_path:
            target_name = os.path.basename(target_path)

        if target_path and os.path.normpath(target_path).lower() in running_set:
            return True
        if target_name and target_name.lower() in running_set:
            return True

        return False

    def _monitor_loop(self):
        while self._running:
            try:
                with self._lock:
                    get_rules = self.get_rules_callback

                if get_rules:
                    all_rules = get_rules()
                    app_rules = [
                        r for r in all_rules
                        if r.get("enabled", True) and r.get("watch_mode") == WATCH_MODE_ON_APP
                    ]

                    if app_rules:
                        running_apps = self._get_running_process_names_and_paths()

                        for rule in app_rules:
                            rule_id = rule.get("id")
                            is_target_up = self._is_target_running(rule, running_apps)

                            with self._lock:
                                was_active = rule_id in self._active_rules

                            if is_target_up and not was_active:
                                print(f"[ProcessMonitor] Target app detected for rule '{rule.get('name')}'. Activating watcher.")
                                success = self.watcher_manager.start_rule(rule)
                                if success:
                                    with self._lock:
                                        self._active_rules.add(rule_id)
                                    if self.on_rule_state_change:
                                        self.on_rule_state_change(rule, True)

                            elif not is_target_up and was_active:
                                print(f"[ProcessMonitor] Target app exited for rule '{rule.get('name')}'. Stopping watcher.")
                                # Brief pause to catch screenshots saved right upon game shutdown
                                time.sleep(0.8)
                                if rule.get("process_existing", True):
                                    self.watcher_manager.process_existing_files(rule)
                                self.watcher_manager.stop_rule(rule_id)
                                with self._lock:
                                    self._active_rules.discard(rule_id)
                                if self.on_rule_state_change:
                                    self.on_rule_state_change(rule, False)
                    else:
                        with self._lock:
                            self._active_rules.clear()

            except Exception as e:
                print(f"[ProcessMonitor] Error in monitoring loop: {e}")

            time.sleep(self.poll_interval)
