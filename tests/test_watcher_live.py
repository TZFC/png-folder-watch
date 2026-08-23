"""
Live watcher integration tests.
Tests folder observer detecting new files in real time and debouncing.
"""

import os
import time
import shutil
import tempfile
import unittest
from PIL import Image

from src.config import create_default_rule, OUTPUT_MODE_SAME, KEEP_ORIGINAL_ALWAYS
from src.watcher import WatcherManager


class TestWatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.watch_dir = tempfile.mkdtemp(prefix="pngwatch_live_")
        self.converted_files = []

        def callback(rule, png_path, jpg_path, deleted):
            self.converted_files.append((png_path, jpg_path, deleted))

        self.watcher = WatcherManager(on_converted=callback)

    def tearDown(self):
        self.watcher.stop_all()
        shutil.rmtree(self.watch_dir, ignore_errors=True)

    def test_live_file_creation_detected(self):
        rule = create_default_rule(self.watch_dir)
        rule["output_mode"] = OUTPUT_MODE_SAME
        rule["keep_original"] = KEEP_ORIGINAL_ALWAYS
        rule["process_existing"] = False

        started = self.watcher.start_rule(rule)
        self.assertTrue(started)

        # Give watchdog observer thread a moment to start
        time.sleep(0.5)

        # Create a new PNG file
        test_png = os.path.join(self.watch_dir, "live_shot.png")
        img = Image.new("RGB", (50, 50), (255, 100, 50))
        img.save(test_png, "PNG")

        # Wait for watcher event and conversion
        max_wait = 6.0
        start_t = time.time()
        expected_jpg = os.path.join(self.watch_dir, "live_shot.jpg")

        while time.time() - start_t < max_wait:
            if os.path.exists(expected_jpg) and len(self.converted_files) > 0:
                break
            time.sleep(0.3)

        self.assertTrue(os.path.exists(expected_jpg), "JPG was not created by watcher event")
        self.assertTrue(os.path.exists(test_png), "Original PNG was kept")


if __name__ == "__main__":
    unittest.main()
