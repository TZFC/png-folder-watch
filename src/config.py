"""
Configuration manager for PNG Folder Watch.
Handles loading, saving, validating rules and global app settings.
"""

import json
import os
import sys
import uuid
from typing import Dict, List, Any, Optional

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(APP_DIR, "config.json")
APPDATA_CONFIG_PATH = os.path.join(
    os.getenv("APPDATA", os.path.expanduser("~")), "PNGFolderWatch", "config.json"
)

# Output mode choices
OUTPUT_MODE_SAME = "same_folder"
OUTPUT_MODE_JPG_SUB = "jpg_subfolder"
OUTPUT_MODE_MIRROR = "mirror_structure"

OUTPUT_MODES = [
    (OUTPUT_MODE_SAME, "Same Folder", "Save .jpg directly alongside the original .png"),
    (OUTPUT_MODE_JPG_SUB, "Subfolder (./jpg/)", "Save .jpg inside a 'jpg' subfolder in each directory"),
    (OUTPUT_MODE_MIRROR, "Mirror Structure (../jpg-root/)", "Mirror original folder tree under a sibling 'jpg-root' folder"),
]

# Keep original choices
KEEP_ORIGINAL_ALWAYS = "always"
KEEP_ORIGINAL_NEVER = "never"
KEEP_ORIGINAL_DELETE_NO_ALPHA = "delete_if_no_alpha"

KEEP_ORIGINAL_MODES = [
    (KEEP_ORIGINAL_ALWAYS, "Keep Original PNG", "Always keep both original .png and converted .jpg"),
    (KEEP_ORIGINAL_NEVER, "Delete Original PNG", "Always delete original .png after successful conversion"),
    (KEEP_ORIGINAL_DELETE_NO_ALPHA, "Delete Only If No Transparency", "Keep .png if it has transparent pixels; delete if fully opaque"),
]

# Per-Rule Watch Modes
WATCH_MODE_ALWAYS = "always"
WATCH_MODE_ON_APP = "on_app"

WATCH_MODES = [
    (WATCH_MODE_ALWAYS, "Watch Continuously", "Always active whenever PNG Folder Watch is running"),
    (WATCH_MODE_ON_APP, "Watch When Game / App Runs", "Active only while a selected game or application (.exe) is running"),
]


def get_config_path() -> str:
    """Return writable config file path."""
    try:
        test_file = os.path.join(APP_DIR, ".write_test")
        with open(test_file, "w") as f:
            f.write("1")
        if os.path.exists(test_file):
            os.remove(test_file)
        return DEFAULT_CONFIG_PATH
    except Exception:
        os.makedirs(os.path.dirname(APPDATA_CONFIG_PATH), exist_ok=True)
        return APPDATA_CONFIG_PATH


def create_default_rule(folder_path: str = "") -> Dict[str, Any]:
    """Create a new rule dict with sensible defaults."""
    name = "New Rule"
    if folder_path:
        base = os.path.basename(os.path.normpath(folder_path))
        name = base if base else folder_path

    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "watch_folder": folder_path,
        "output_mode": OUTPUT_MODE_SAME,
        "keep_original": KEEP_ORIGINAL_ALWAYS,
        "jpg_quality": 90,
        "process_existing": True,
        "apply_delete_to_existing": False,
        "watch_mode": WATCH_MODE_ALWAYS,
        "target_app_path": "",
        "target_app_name": "",
        "enabled": True,
    }


from .i18n import detect_system_language, set_language, get_language, LANG_ZH_CN, LANG_EN_US


def get_default_config() -> Dict[str, Any]:
    """Return default global configuration."""
    return {
        "version": 3,
        "language": detect_system_language(),
        "start_with_windows": True,
        "notify_on_convert": True,
        "rules": [],
    }


import threading

class ConfigManager:
    """Manages application settings and rules."""

    def __init__(self, config_path: Optional[str] = None):
        self._lock = threading.RLock()
        self.config_path = config_path or get_config_path()
        with self._lock:
            self.data = self._load_unlocked()
        # Synchronize active i18n language
        set_language(self.language)

    def load(self) -> Dict[str, Any]:
        """Load configuration from disk or return default."""
        with self._lock:
            self.data = self._load_unlocked()
            return self.data.copy()

    def _load_unlocked(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    merged = get_default_config()
                    merged.update(data)
                    return merged
            except Exception as e:
                print(f"[ConfigManager] Error reading config: {e}")
        return get_default_config()

    def save(self) -> bool:
        """Save configuration to disk."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                print(f"[ConfigManager] Error saving config: {e}")
                return False

    @property
    def language(self) -> str:
        with self._lock:
            return self.data.get("language", detect_system_language())

    @language.setter
    def language(self, value: str):
        with self._lock:
            self.data["language"] = value
        set_language(value)

    @property
    def rules(self) -> List[Dict[str, Any]]:
        with self._lock:
            # Return a list of rule dict copies to avoid concurrent mutation issues during iteration
            return [r.copy() for r in self.data.setdefault("rules", [])]

    @property
    def start_with_windows(self) -> bool:
        with self._lock:
            return self.data.get("start_with_windows", True)

    @start_with_windows.setter
    def start_with_windows(self, value: bool):
        with self._lock:
            self.data["start_with_windows"] = bool(value)

    @property
    def notify_on_convert(self) -> bool:
        with self._lock:
            return self.data.get("notify_on_convert", True)

    @notify_on_convert.setter
    def notify_on_convert(self, value: bool):
        with self._lock:
            self.data["notify_on_convert"] = bool(value)

    def add_rule(self, rule: Dict[str, Any]) -> str:
        """Add a rule and return its ID."""
        with self._lock:
            rule_copy = rule.copy()
            if "id" not in rule_copy or not rule_copy["id"]:
                rule_copy["id"] = str(uuid.uuid4())
            self.data.setdefault("rules", []).append(rule_copy)
            self.save()
            return rule_copy["id"]

    def update_rule(self, rule_id: str, updated_rule: Dict[str, Any]) -> bool:
        """Update an existing rule by ID."""
        with self._lock:
            rules_list = self.data.setdefault("rules", [])
            for i, r in enumerate(rules_list):
                if r.get("id") == rule_id:
                    new_rule = updated_rule.copy()
                    new_rule["id"] = rule_id
                    rules_list[i] = new_rule
                    self.save()
                    return True
            return False

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        with self._lock:
            initial_len = len(self.data.setdefault("rules", []))
            self.data["rules"] = [r for r in self.data["rules"] if r.get("id") != rule_id]
            if len(self.data["rules"]) != initial_len:
                self.save()
                return True
            return False

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get rule by ID."""
        with self._lock:
            for r in self.data.setdefault("rules", []):
                if r.get("id") == rule_id:
                    return r.copy()
            return None
