"""
GUI smoke tests to ensure Tkinter components initialize and destroy without error.
"""

import unittest
import tempfile
import os
import shutil
from src.config import ConfigManager, create_default_rule
from src.gui import ConfigApp, RuleEditorDialog


class TestGUISmoke(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_gui_config.json")
        self.cm = ConfigManager(self.config_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_gui_init_and_close(self):
        rule = create_default_rule("C:\\TestFolder")
        self.cm.add_rule(rule)

        app = ConfigApp(self.cm)
        app.update()
        self.assertEqual(len(app.cards_frame.winfo_children()), 1)
        app.destroy()

    def test_rule_editor_dialog_init_and_cancel(self):
        app = ConfigApp(self.cm)
        app.update()

        editor = RuleEditorDialog(app, rule=None)
        editor.update()
        editor.destroy()
        app.destroy()

    def test_toggle_options_applied_immediately(self):
        app = ConfigApp(self.cm)
        app.update()

        # Toggle startup
        app.var_startup.set(False)
        app._on_toggle_startup()
        self.assertFalse(self.cm.start_with_windows)

        # Reload from file to ensure disk persistence
        cm_reloaded = ConfigManager(self.config_file)
        self.assertFalse(cm_reloaded.start_with_windows)

        # Toggle notify
        app.var_notify.set(False)
        app._on_toggle_notify()
        self.assertFalse(self.cm.notify_on_convert)

        cm_reloaded2 = ConfigManager(self.config_file)
        self.assertFalse(cm_reloaded2.notify_on_convert)

        app.destroy()


    def test_gui_window_dimensions(self):
        app = ConfigApp(self.cm)
        app.update()
        min_w, min_h = app.minsize()
        self.assertGreaterEqual(min_w, 860)
        self.assertGreaterEqual(min_h, 580)
        app.destroy()

    def test_startup_lifecycle(self):
        from src.startup import enable_startup, disable_startup, is_startup_enabled, sync_startup_with_config
        # Enable startup
        self.cm.start_with_windows = True
        res = sync_startup_with_config(self.cm)
        self.assertTrue(res)
        self.assertTrue(is_startup_enabled())

        # Disable startup
        self.cm.start_with_windows = False
        res2 = sync_startup_with_config(self.cm)
        self.assertTrue(res2)
        self.assertFalse(is_startup_enabled())

        # Re-enable to restore user preference
        self.cm.start_with_windows = True
        sync_startup_with_config(self.cm)
        self.assertTrue(is_startup_enabled())


if __name__ == "__main__":
    unittest.main()

