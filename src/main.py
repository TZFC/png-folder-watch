"""
Main entry point for PNG Folder Watch.
Handles single-instance verification, configuration mode, and background tray execution.
"""

import os
import sys
import argparse
import ctypes
from typing import Optional

from .config import ConfigManager
from .gui import show_config_gui
from .tray import TrayApp
from .startup import is_startup_enabled, set_startup


def is_already_running(mutex_name: str = "PNGFolderWatch_SingleInstance_Mutex") -> bool:
    """Check if another instance of PNG Folder Watch is currently active."""
    try:
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        last_error = ctypes.windll.kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183
        return last_error == ERROR_ALREADY_EXISTS
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="PNG Folder Watch")
    parser.add_argument(
        "--configure",
        action="store_true",
        help="Open configuration GUI directly",
    )
    args = parser.parse_args()

    config_manager = ConfigManager()

    # Ensure Windows startup shortcut is registered so app runs in background
    if not is_startup_enabled():
        set_startup(True)

    already_running = is_already_running()

    # Case 1: First install or explicit configure request or no rules yet
    if args.configure or not config_manager.rules:
        # Show configuration GUI
        def on_start():
            # If not already running tray, launch tray
            if not already_running:
                tray = TrayApp(config_manager)
                tray.start()

        show_config_gui(config_manager, on_start_callback=on_start)
        return

    # Case 2: Already running in tray and launched again without flags
    if already_running:
        print("[Main] PNG Folder Watch is already running in system tray. Opening Settings GUI.")
        show_config_gui(config_manager)
        return

    # Case 3: Normal background startup with configured rules
    tray = TrayApp(config_manager)
    tray.start()


if __name__ == "__main__":
    main()
