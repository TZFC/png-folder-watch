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

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.config_file = os.path.join(cls.temp_dir, "test_gui_config.json")
        cls.cm = ConfigManager(cls.config_file)
        cls.app = ConfigApp(cls.cm)
        cls.app.update()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.destroy()
        except Exception:
            pass
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_gui_init_and_cards(self):
        rule = create_default_rule("C:\\TestFolder")
        self.cm.add_rule(rule)
        self.app.refresh_rules_list()
        self.app.update()
        self.assertGreaterEqual(len(self.app.cards_frame.winfo_children()), 1)

    def test_rule_editor_dialog_init_and_cancel(self):
        editor = RuleEditorDialog(self.app, rule=None)
        editor.update()
        editor.destroy()

    def test_toggle_options_applied_immediately(self):
        # Toggle startup
        self.app.var_startup.set(False)
        self.app._on_toggle_startup()
        self.assertFalse(self.cm.start_with_windows)

        # Reload from file to ensure disk persistence
        cm_reloaded = ConfigManager(self.config_file)
        self.assertFalse(cm_reloaded.start_with_windows)

        # Toggle notify
        self.app.var_notify.set(False)
        self.app._on_toggle_notify()
        self.assertFalse(self.cm.notify_on_convert)

        cm_reloaded2 = ConfigManager(self.config_file)
        self.assertFalse(cm_reloaded2.notify_on_convert)

    def test_gui_language_toggle(self):
        rule = create_default_rule("C:\\TestFolder")
        self.cm.add_rule(rule)

        # Start with zh-CN
        self.cm.language = "zh-CN"
        self.cm.save()
        self.app.refresh_rules_list()
        self.app.update()

        self.assertIn("PNG 图片监控转换器", self.app.lbl_hero_title.cget("text"))
        self.assertEqual(self.app.btn_lang.cget("text"), "🌐 English")

        # Toggle to English
        self.app._toggle_language()
        self.app.update()

        self.assertEqual(self.cm.language, "en-US")
        self.assertIn("PNG Folder Watch", self.app.lbl_hero_title.cget("text"))
        self.assertEqual(self.app.btn_lang.cget("text"), "🌐 简体中文")

        # Toggle back to zh-CN
        self.app._toggle_language()
        self.app.update()

        self.assertEqual(self.cm.language, "zh-CN")
        self.assertIn("PNG 图片监控转换器", self.app.lbl_hero_title.cget("text"))
        self.assertEqual(self.app.btn_lang.cget("text"), "🌐 English")

    def test_gui_window_dimensions(self):
        min_w, min_h = self.app.minsize()
        self.assertGreaterEqual(min_w, 860)
        self.assertGreaterEqual(min_h, 580)

    def test_gui_start_and_close_lifecycle(self):
        self.assertFalse(self.app.start_requested)
        self.app.start_requested = True
        self.assertTrue(self.app.start_requested)
        self.app.start_requested = False

    def test_rule_editor_dialog_mousewheel_cleanup(self):
        dlg = RuleEditorDialog(parent=self.app)
        dlg.update()
        dlg.destroy()
        # Scrolling in main app canvas should not raise error
        self.app.canvas.event_generate("<MouseWheel>", delta=120)

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

