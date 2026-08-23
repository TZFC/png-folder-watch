"""
System Tray Manager for PNG Folder Watch.
Runs in the Windows notification area with pystray, providing background operation,
status menus, pause/resume, quick folder access, and notification toasts.
"""

import os
import threading
import time
from typing import Optional
from PIL import Image
import pystray
from pystray import MenuItem as item, Menu

from .config import ConfigManager, WATCH_MODE_ALWAYS, WATCH_MODE_ON_APP
from .i18n import t, get_language, set_language
from .watcher import WatcherManager
from .process_monitor import ProcessMonitor
from .icon_generator import create_app_icon, ensure_icon_files, ICON_PNG_PATH
from .gui import show_config_gui


class TrayApp:
    """Manages background watchers, per-rule process monitors, and the Windows system tray icon."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        set_language(self.config_manager.language)
        self.watcher_manager = WatcherManager(on_converted=self._on_file_converted)
        self.process_monitor = ProcessMonitor(
            self.watcher_manager,
            get_rules_callback=lambda: self.config_manager.rules,
            on_rule_state_change=self._on_rule_app_state_change,
        )
        self.icon: Optional[pystray.Icon] = None
        self._gui_thread: Optional[threading.Thread] = None

    def start(self):
        """Start watchers, process monitor, and launch system tray."""
        self._apply_rules()
        self.process_monitor.start()

        # Prepare tray icon image
        ensure_icon_files()
        if os.path.exists(ICON_PNG_PATH):
            try:
                icon_img = Image.open(ICON_PNG_PATH)
            except Exception:
                icon_img = create_app_icon(64)
        else:
            icon_img = create_app_icon(64)

        # Build tray menu with dynamic localized labels
        menu = Menu(
            item(lambda i: t("tray_title"), None, enabled=False),
            item(self._get_status_text, None, enabled=False),
            Menu.SEPARATOR,
            item(lambda i: t("tray_settings"), self._on_open_settings, default=True),
            item(self._get_pause_label, self._on_toggle_pause),
            item(lambda i: t("tray_open_folder"), Menu(self._build_folder_menu_items)),
            Menu.SEPARATOR,
            item(lambda i: t("tray_exit"), self._on_exit),
        )

        self.icon = pystray.Icon(
            "PNGFolderWatch",
            icon_img,
            t("tray_tooltip_active"),
            menu=menu,
        )

        print("[TrayApp] PNG Folder Watch is running in the system tray.")
        self.icon.run()

    def _apply_rules(self):
        """Apply all continuous rules and update process monitor."""
        self.watcher_manager.stop_all()

        rules = self.config_manager.rules
        continuous_rules = [
            r for r in rules
            if r.get("enabled", True) and r.get("watch_mode", WATCH_MODE_ALWAYS) == WATCH_MODE_ALWAYS
        ]

        for rule in continuous_rules:
            self.watcher_manager.start_rule(rule)

        print(f"[TrayApp] Started {len(continuous_rules)} continuous rules.")

    def _on_rule_app_state_change(self, rule: dict, is_running: bool):
        """Notify user when an app-triggered rule turns active or inactive."""
        if self.icon and self.config_manager.notify_on_convert:
            try:
                app_name = rule.get("target_app_name") or os.path.basename(rule.get("target_app_path", "Game"))
                rule_name = rule.get("name", "Folder")
                if is_running:
                    self.icon.notify(
                        t("notify_app_active_msg", app_name=app_name, rule_name=rule_name),
                        title=t("notify_app_active_title"),
                    )
                else:
                    self.icon.notify(
                        t("notify_app_idle_msg", app_name=app_name, rule_name=rule_name),
                        title=t("notify_app_idle_title"),
                    )
            except Exception:
                pass

    def _get_status_text(self, item=None) -> str:
        if self.watcher_manager.is_paused:
            return t("tray_status_paused")

        active_count = self.watcher_manager.get_active_count()
        total_count = len([r for r in self.config_manager.rules if r.get("enabled", True)])
        app_active = self.process_monitor.get_active_app_rules_count()

        if app_active > 0:
            return t("tray_status_active_app", active=active_count, total=total_count, app_active=app_active)
        return t("tray_status_active", active=active_count, total=total_count)

    def _get_pause_label(self, item=None) -> str:
        return t("tray_resume") if self.watcher_manager.is_paused else t("tray_pause")

    def _on_toggle_pause(self, icon=None, item=None):
        if self.watcher_manager.is_paused:
            self.watcher_manager.resume()
            if self.icon:
                self.icon.title = t("tray_tooltip_active")
        else:
            self.watcher_manager.pause()
            if self.icon:
                self.icon.title = t("tray_tooltip_paused")

    def _build_folder_menu_items(self):
        """Dynamically generate menu items for opening each watched folder in Windows Explorer."""
        items = []
        for rule in self.config_manager.rules:
            folder = rule.get("watch_folder", "")
            name = rule.get("name", folder)
            if folder and os.path.isdir(folder):
                items.append(item(name, lambda i, f=folder: self._open_explorer(f)))
        if not items:
            items.append(item(t("tray_no_folders"), None, enabled=False))
        return items

    def _open_explorer(self, folder_path: str):
        try:
            if os.path.exists(folder_path):
                os.startfile(folder_path)
        except Exception as e:
            print(f"[TrayApp] Failed to open folder {folder_path}: {e}")

    def _on_file_converted(self, rule: dict, png_path: str, jpg_path: str, deleted_original: bool):
        """Notification callback on conversion."""
        if self.config_manager.notify_on_convert and self.icon:
            try:
                title = t("notify_converted_title", rule_name=rule.get("name", "Watch"))
                msg = t("notify_saved_msg", filename=os.path.basename(jpg_path))
                if deleted_original:
                    msg += "\n" + t("notify_deleted_msg")
                self.icon.notify(msg, title=title)
            except Exception:
                pass

    def _on_open_settings(self, icon=None, item=None):
        """Open settings GUI in a thread so tray remains responsive."""
        if self._gui_thread and self._gui_thread.is_alive():
            return

        def run_gui():
            show_config_gui(self.config_manager, on_start_callback=self._on_settings_saved)

        self._gui_thread = threading.Thread(target=run_gui, daemon=True)
        self._gui_thread.start()

    def _on_settings_saved(self):
        """Reload configuration and restart active watchers."""
        self.config_manager.load()
        set_language(self.config_manager.language)
        self._apply_rules()
        print("[TrayApp] Re-applied updated settings and rules.")

    def _on_exit(self, icon=None, item=None):
        """Clean shutdown."""
        print("[TrayApp] Shutting down...")
        self.watcher_manager.stop_all()
        self.process_monitor.stop()
        if self.icon:
            self.icon.stop()
