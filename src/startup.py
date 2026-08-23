"""
Windows Startup Manager.
Manages automatic startup via both Windows Registry Run key (HKCU)
and the Windows Startup folder shortcut to ensure 100% reliable, silent background execution.
"""

import os
import subprocess
import sys
from typing import Optional

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_SCRIPT_PATH = os.path.join(APP_DIR, "src", "main.py")
BAT_PATH = os.path.join(APP_DIR, "PNGWatch.bat")
REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_VALUE_NAME = "PNGFolderWatch"
STARTUP_FOLDER = os.path.join(
    os.getenv("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup",
)
SHORTCUT_PATH = os.path.join(STARTUP_FOLDER, "PNGFolderWatch.lnk")


def get_pythonw_executable() -> str:
    """Return the path to pythonw.exe (or python.exe fallback)."""
    # 1. Check self-contained runtime directory
    runtime_pythonw = os.path.join(APP_DIR, "runtime", "pythonw.exe")
    if os.path.exists(runtime_pythonw):
        return runtime_pythonw
    runtime_python = os.path.join(APP_DIR, "runtime", "python.exe")
    if os.path.exists(runtime_python):
        return runtime_python

    # 2. Check current python environment
    exe_dir = os.path.dirname(sys.executable)
    env_pythonw = os.path.join(exe_dir, "pythonw.exe")
    if os.path.exists(env_pythonw):
        return env_pythonw

    return sys.executable


def get_startup_command() -> str:
    """Construct command string to run PNG Folder Watch silently in background."""
    py_exe = get_pythonw_executable()
    return f'"{py_exe}" "{MAIN_SCRIPT_PATH}"'


def is_startup_enabled() -> bool:
    """Check if startup is registered in Windows Registry or Startup folder."""
    # Check Registry
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_KEY_PATH,
            0,
            winreg.KEY_READ,
        )
        val, _ = winreg.QueryValueEx(key, REG_VALUE_NAME)
        winreg.CloseKey(key)
        if val:
            return True
    except Exception:
        pass

    # Check Startup shortcut
    return os.path.exists(SHORTCUT_PATH)


def enable_startup() -> bool:
    """Register PNG Folder Watch in Windows Registry Run key and create Startup shortcut."""
    success = False

    # 1. Register in Windows Registry (HKCU Run Key - standard & reliable)
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_KEY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(
            key,
            REG_VALUE_NAME,
            0,
            winreg.REG_SZ,
            get_startup_command(),
        )
        winreg.CloseKey(key)
        success = True
    except Exception as e:
        print(f"[Startup] Registry enable error: {e}")

    # 2. Also create/update .lnk shortcut in Windows Startup folder pointing directly to pythonw
    try:
        os.makedirs(STARTUP_FOLDER, exist_ok=True)
        py_exe = get_pythonw_executable()
        working_dir = os.path.abspath(APP_DIR)

        ps_cmd = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{SHORTCUT_PATH}')
$s.TargetPath = '{py_exe}'
$s.Arguments = '"{MAIN_SCRIPT_PATH}"'
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
        if result.returncode == 0 and os.path.exists(SHORTCUT_PATH):
            success = True
    except Exception as e:
        print(f"[Startup] Shortcut enable error: {e}")

    return success


def disable_startup() -> bool:
    """Remove PNG Folder Watch from Windows Registry and Startup folder."""
    # 1. Remove from Windows Registry
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_KEY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        )
        try:
            winreg.DeleteValue(key, REG_VALUE_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"[Startup] Registry disable error: {e}")

    # 2. Remove shortcut from Startup folder
    try:
        if os.path.exists(SHORTCUT_PATH):
            os.remove(SHORTCUT_PATH)
    except Exception as e:
        print(f"[Startup] Shortcut disable error: {e}")

    return True


def set_startup(enable: bool) -> bool:
    """Enable or disable startup based on boolean flag."""
    if enable:
        return enable_startup()
    else:
        return disable_startup()


def sync_startup_with_config(config_manager) -> bool:
    """Synchronize Windows startup state with the configuration setting."""
    should_enable = getattr(config_manager, "start_with_windows", True)
    return set_startup(should_enable)

