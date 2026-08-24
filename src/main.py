"""
Main entry point for PNG Folder Watch.
Handles single-instance verification, configuration mode, and background tray execution.
"""

import os
import sys
import argparse
import ctypes
# Ensure project root directory is in sys.path and is the active working directory
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
try:
    os.chdir(APP_DIR)
except Exception:
    pass

if __package__ in (None, ""):
    from src.config import ConfigManager
    from src.gui import show_config_gui
    from src.tray import TrayApp
    from src.startup import sync_startup_with_config
else:
    from .config import ConfigManager
    from .gui import show_config_gui
    from .tray import TrayApp
    from .startup import sync_startup_with_config


def is_already_running(mutex_name: str = "PNGFolderWatch_SingleInstance_Mutex") -> bool:
    """Check if another instance of PNG Folder Watch is currently active."""
    try:
        # Set proper return types to prevent 64-bit handle truncation
        ctypes.windll.kernel32.CreateMutexW.restype = ctypes.c_void_p
        ctypes.windll.kernel32.CreateMutexW.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p
        ]
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

    # Synchronize Windows startup (Registry Run key + shortcut) with config setting
    sync_startup_with_config(config_manager)

    already_running = is_already_running()

    # Case 1: First install or explicit configure request or no rules yet
    if args.configure or not config_manager.rules:
        # Show configuration GUI
        start_requested = show_config_gui(config_manager)

        # If not already running tray and start was requested (or rules were configured), launch tray
        if not already_running and (start_requested or bool(config_manager.rules)):
            tray = TrayApp(config_manager)
            tray.start()
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

