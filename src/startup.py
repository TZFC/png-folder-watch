"""
Windows Startup Manager.
Creates or removes shortcuts in the Windows Startup folder so PNG Folder Watch
can automatically launch in background when the user logs in.
"""

import os
import subprocess
import sys

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAT_PATH = os.path.join(APP_DIR, "PNGWatch.bat")
STARTUP_FOLDER = os.path.join(
    os.getenv("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup",
)
SHORTCUT_PATH = os.path.join(STARTUP_FOLDER, "PNGFolderWatch.lnk")


def is_startup_enabled() -> bool:
    """Check if startup shortcut exists."""
    return os.path.exists(SHORTCUT_PATH)


def enable_startup() -> bool:
    """Create a minimized shortcut to PNGWatch.bat in the Windows Startup folder."""
    try:
        os.makedirs(STARTUP_FOLDER, exist_ok=True)
        target = os.path.abspath(BAT_PATH)
        working_dir = os.path.abspath(APP_DIR)

        # Use PowerShell to create .lnk shortcut with Minimized window style (7)
        ps_cmd = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{SHORTCUT_PATH}')
$s.TargetPath = '{target}'
$s.WorkingDirectory = '{working_dir}'
$s.Description = 'PNG Folder Watch background service'
$s.WindowStyle = 7
$s.Save()
"""
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0 and os.path.exists(SHORTCUT_PATH)
    except Exception as e:
        print(f"[Startup] Failed to enable startup: {e}")
        return False


def disable_startup() -> bool:
    """Remove shortcut from the Windows Startup folder."""
    try:
        if os.path.exists(SHORTCUT_PATH):
            os.remove(SHORTCUT_PATH)
        return True
    except Exception as e:
        print(f"[Startup] Failed to disable startup: {e}")
        return False


def set_startup(enable: bool) -> bool:
    """Enable or disable startup based on boolean flag."""
    if enable:
        return enable_startup()
    else:
        return disable_startup()
