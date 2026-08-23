"""
Comprehensive unit & integration tests for PNG Folder Watch.
"""

import os
import shutil
import tempfile
import unittest
from PIL import Image

from src.config import (
    ConfigManager,
    create_default_rule,
    OUTPUT_MODE_SAME,
    OUTPUT_MODE_JPG_SUB,
    OUTPUT_MODE_MIRROR,
    KEEP_ORIGINAL_ALWAYS,
    KEEP_ORIGINAL_NEVER,
    KEEP_ORIGINAL_DELETE_NO_ALPHA,
    WATCH_MODE_ALWAYS,
    WATCH_MODE_ON_APP,
)
from src.converter import (
    has_alpha_channel,
    compute_target_path,
    convert_png_to_jpg,
)
from src.watcher import WatcherManager


class TestConverter(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="pngwatch_test_")
        self.watch_root = os.path.join(self.test_dir, "WatchedFolder")
        os.makedirs(self.watch_root, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_test_png(self, filepath: str, mode: str = "RGB", with_transparency: bool = False):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        size = (100, 100)
        if mode == "RGBA":
            if with_transparency:
                img = Image.new("RGBA", size, (255, 0, 0, 128))  # 50% transparent red
            else:
                img = Image.new("RGBA", size, (255, 0, 0, 255))  # Fully opaque red
        elif mode == "P":
            img = Image.new("P", size)
            if with_transparency:
                img.info["transparency"] = 0
        else:
            img = Image.new("RGB", size, (0, 128, 255))
        img.save(filepath, "PNG")
        return filepath

    def test_has_alpha_channel(self):
        # 1. RGB has no alpha
        rgb_path = os.path.join(self.watch_root, "opaque_rgb.png")
        self._create_test_png(rgb_path, "RGB")
        with Image.open(rgb_path) as img:
            self.assertFalse(has_alpha_channel(img))

        # 2. RGBA with all 255 alpha has no transparency
        rgba_opaque_path = os.path.join(self.watch_root, "opaque_rgba.png")
        self._create_test_png(rgba_opaque_path, "RGBA", with_transparency=False)
        with Image.open(rgba_opaque_path) as img:
            self.assertFalse(has_alpha_channel(img))

        # 3. RGBA with actual alpha < 255 has transparency
        rgba_trans_path = os.path.join(self.watch_root, "trans_rgba.png")
        self._create_test_png(rgba_trans_path, "RGBA", with_transparency=True)
        with Image.open(rgba_trans_path) as img:
            self.assertTrue(has_alpha_channel(img))

    def test_compute_target_path(self):
        sub_dir = os.path.join(self.watch_root, "level1", "level2")
        png_path = os.path.join(sub_dir, "shot.png")

        # Mode 1: same_folder
        target_same = compute_target_path(png_path, self.watch_root, OUTPUT_MODE_SAME)
        expected_same = os.path.join(sub_dir, "shot.jpg")
        self.assertEqual(os.path.normpath(target_same), os.path.normpath(expected_same))

        # Mode 2: jpg_subfolder
        target_sub = compute_target_path(png_path, self.watch_root, OUTPUT_MODE_JPG_SUB)
        expected_sub = os.path.join(sub_dir, "jpg", "shot.jpg")
        self.assertEqual(os.path.normpath(target_sub), os.path.normpath(expected_sub))

        # Mode 3: mirror_structure
        target_mirror = compute_target_path(png_path, self.watch_root, OUTPUT_MODE_MIRROR)
        expected_mirror = os.path.join(
            os.path.dirname(self.watch_root),
            f"jpg-{os.path.basename(self.watch_root)}",
            "level1",
            "level2",
            "shot.jpg",
        )
        self.assertEqual(os.path.normpath(target_mirror), os.path.normpath(expected_mirror))

    def test_conversion_output_mode_same_and_keep_always(self):
        png_path = os.path.join(self.watch_root, "screen1.png")
        self._create_test_png(png_path, "RGB")

        rule = create_default_rule(self.watch_root)
        rule["output_mode"] = OUTPUT_MODE_SAME
        rule["keep_original"] = KEEP_ORIGINAL_ALWAYS
        rule["jpg_quality"] = 85

        success, msg, target_path, deleted = convert_png_to_jpg(png_path, rule)
        self.assertTrue(success)
        self.assertFalse(deleted)
        self.assertTrue(os.path.exists(png_path), "Original PNG should be preserved")
        self.assertTrue(os.path.exists(target_path), "JPG should exist")

        # Verify valid JPG
        with Image.open(target_path) as img:
            self.assertEqual(img.format, "JPEG")

    def test_conversion_keep_never(self):
        png_path = os.path.join(self.watch_root, "screen2.png")
        self._create_test_png(png_path, "RGB")

        rule = create_default_rule(self.watch_root)
        rule["keep_original"] = KEEP_ORIGINAL_NEVER

        success, msg, target_path, deleted = convert_png_to_jpg(png_path, rule)
        self.assertTrue(success)
        self.assertTrue(deleted)
        self.assertFalse(os.path.exists(png_path), "Original PNG should be deleted")
        self.assertTrue(os.path.exists(target_path), "JPG should exist")

    def test_conversion_delete_if_no_alpha(self):
        # Case A: Opaque image -> should delete
        opaque_path = os.path.join(self.watch_root, "opaque.png")
        self._create_test_png(opaque_path, "RGBA", with_transparency=False)

        rule = create_default_rule(self.watch_root)
        rule["keep_original"] = KEEP_ORIGINAL_DELETE_NO_ALPHA

        success, msg, target_path, deleted = convert_png_to_jpg(opaque_path, rule)
        self.assertTrue(success)
        self.assertTrue(deleted, "Opaque image should have original deleted")
        self.assertFalse(os.path.exists(opaque_path))
        self.assertTrue(os.path.exists(target_path))

        # Case B: Transparent image -> should KEEP
        trans_path = os.path.join(self.watch_root, "transparent.png")
        self._create_test_png(trans_path, "RGBA", with_transparency=True)

        success, msg, target_path, deleted = convert_png_to_jpg(trans_path, rule)
        self.assertTrue(success)
        self.assertFalse(deleted, "Transparent image should NOT have original deleted")
        self.assertTrue(os.path.exists(trans_path), "Original transparent PNG must be preserved")
        self.assertTrue(os.path.exists(target_path))

    def test_conversion_mirror_structure(self):
        nested_dir = os.path.join(self.watch_root, "game_sub", "sub2")
        png_path = os.path.join(nested_dir, "nested_shot.png")
        self._create_test_png(png_path, "RGB")

        rule = create_default_rule(self.watch_root)
        rule["output_mode"] = OUTPUT_MODE_MIRROR

        success, msg, target_path, deleted = convert_png_to_jpg(png_path, rule)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(target_path))
        self.assertIn("jpg-WatchedFolder", target_path)
        self.assertIn(os.path.join("game_sub", "sub2"), target_path)

    def test_process_existing_preserves_already_converted_by_default(self):
        png_path = os.path.join(self.watch_root, "existing1.png")
        self._create_test_png(png_path, "RGB")
        jpg_path = os.path.join(self.watch_root, "existing1.jpg")
        self._create_test_png(jpg_path, "RGB")  # pre-existing jpg

        rule = create_default_rule(self.watch_root)
        rule["keep_original"] = KEEP_ORIGINAL_NEVER
        rule["apply_delete_to_existing"] = False

        wm = WatcherManager()
        wm.process_existing_files(rule)
        import time
        time.sleep(0.5)

        self.assertTrue(os.path.exists(png_path), "Previously converted PNG should NOT be deleted by default")
        self.assertTrue(os.path.exists(jpg_path), "JPG should remain")

    def test_process_existing_apply_delete_to_existing(self):
        # 1. Opaque PNG with pre-existing JPG -> should be deleted when apply_delete_to_existing=True
        png_path = os.path.join(self.watch_root, "del_existing.png")
        self._create_test_png(png_path, "RGBA", with_transparency=False)
        jpg_path = os.path.join(self.watch_root, "del_existing.jpg")
        self._create_test_png(jpg_path, "RGB")

        # 2. Transparent PNG with pre-existing JPG -> should be KEPT when delete_if_no_alpha
        trans_png_path = os.path.join(self.watch_root, "trans_existing.png")
        self._create_test_png(trans_png_path, "RGBA", with_transparency=True)
        trans_jpg_path = os.path.join(self.watch_root, "trans_existing.jpg")
        self._create_test_png(trans_jpg_path, "RGB")

        rule = create_default_rule(self.watch_root)
        rule["keep_original"] = KEEP_ORIGINAL_DELETE_NO_ALPHA
        rule["apply_delete_to_existing"] = True

        wm = WatcherManager()
        wm.process_existing_files(rule)
        import time
        time.sleep(0.5)

        self.assertFalse(os.path.exists(png_path), "Opaque processed PNG should be deleted when apply_delete_to_existing is True")
        self.assertTrue(os.path.exists(jpg_path), "JPG should remain")
        self.assertTrue(os.path.exists(trans_png_path), "Transparent PNG must be kept even if apply_delete_to_existing is True")
        self.assertTrue(os.path.exists(trans_jpg_path), "Transparent JPG should remain")


    def test_chinese_paths_and_filenames_conversion(self):
        """Ensure full support for Chinese folder paths and image filenames."""
        cn_folder = os.path.join(self.watch_root, "游戏截图_2026", "原神_相册")
        os.makedirs(cn_folder, exist_ok=True)
        cn_png = os.path.join(cn_folder, "旅行者_透明测试.png")
        self._create_test_png(cn_png, "RGBA", with_transparency=True)

        cn_opaque_png = os.path.join(cn_folder, "不透明风景_璃月港.png")
        self._create_test_png(cn_opaque_png, "RGBA", with_transparency=False)

        rule = create_default_rule(cn_folder)
        rule["keep_original"] = KEEP_ORIGINAL_DELETE_NO_ALPHA
        rule["output_mode"] = OUTPUT_MODE_JPG_SUB

        # 1. Convert transparent PNG
        success1, msg1, tgt1, del1 = convert_png_to_jpg(cn_png, rule)
        self.assertTrue(success1)
        self.assertFalse(del1)
        self.assertTrue(os.path.exists(cn_png))
        self.assertTrue(os.path.exists(tgt1))
        self.assertIn("原神_相册", tgt1)
        self.assertIn("jpg", tgt1)

        # 2. Convert opaque PNG
        success2, msg2, tgt2, del2 = convert_png_to_jpg(cn_opaque_png, rule)
        self.assertTrue(success2)
        self.assertTrue(del2)
        self.assertFalse(os.path.exists(cn_opaque_png))
        self.assertTrue(os.path.exists(tgt2))


class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.cm = ConfigManager(self.config_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_and_update_rule(self):
        rule = create_default_rule("C:\\Screenshots")
        rule_id = self.cm.add_rule(rule)
        self.assertEqual(len(self.cm.rules), 1)
        self.assertEqual(self.cm.rules[0]["name"], "Screenshots")

        # Update
        rule["jpg_quality"] = 95
        self.cm.update_rule(rule_id, rule)

        # Reload from disk
        cm2 = ConfigManager(self.config_file)
        self.assertEqual(cm2.get_rule(rule_id)["jpg_quality"], 95)

        # Test per-rule watch_mode and global startup
        rule["watch_mode"] = "on_app"
        rule["target_app_path"] = "C:\\Games\\Cyberpunk2077.exe"
        rule["target_app_name"] = "Cyberpunk2077.exe"
        self.cm.update_rule(rule_id, rule)

        self.cm.start_with_windows = True
        self.cm.language = "zh-CN"
        self.cm.save()

        cm3 = ConfigManager(self.config_file)
        saved_rule = cm3.get_rule(rule_id)
        self.assertEqual(saved_rule["watch_mode"], "on_app")
        self.assertEqual(saved_rule["target_app_name"], "Cyberpunk2077.exe")
        self.assertTrue(cm3.start_with_windows)
        self.assertEqual(cm3.language, "zh-CN")

        # Toggle to en-US
        self.cm.language = "en-US"
        self.cm.save()
        cm4 = ConfigManager(self.config_file)
        self.assertEqual(cm4.language, "en-US")


if __name__ == "__main__":
    unittest.main()
