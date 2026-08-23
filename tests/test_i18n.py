"""
Unit tests for i18n localization module.
"""

import unittest
from src.i18n import (
    t,
    set_language,
    get_language,
    toggle_language,
    get_localized_output_modes,
    get_localized_keep_original_modes,
    get_localized_watch_modes,
    TRANSLATIONS,
    LANG_ZH_CN,
    LANG_EN_US,
    SUPPORTED_LANGUAGES,
)


class TestI18n(unittest.TestCase):

    def setUp(self):
        # Reset to zh-CN before each test
        set_language(LANG_ZH_CN)

    def test_key_parity(self):
        """Ensure all keys in zh-CN exist in en-US and vice versa."""
        zh_keys = set(TRANSLATIONS[LANG_ZH_CN].keys())
        en_keys = set(TRANSLATIONS[LANG_EN_US].keys())

        missing_in_en = zh_keys - en_keys
        missing_in_zh = en_keys - zh_keys

        self.assertEqual(missing_in_en, set(), f"Keys missing in en-US: {missing_in_en}")
        self.assertEqual(missing_in_zh, set(), f"Keys missing in zh-CN: {missing_in_zh}")

    def test_set_and_get_language(self):
        set_language(LANG_EN_US)
        self.assertEqual(get_language(), LANG_EN_US)
        self.assertEqual(t("app_name"), "PNG Folder Watch")

        set_language(LANG_ZH_CN)
        self.assertEqual(get_language(), LANG_ZH_CN)
        self.assertEqual(t("app_name"), "PNG 图片监控转换器")

    def test_toggle_language(self):
        set_language(LANG_ZH_CN)
        new_lang = toggle_language()
        self.assertEqual(new_lang, LANG_EN_US)
        self.assertEqual(get_language(), LANG_EN_US)

        new_lang2 = toggle_language()
        self.assertEqual(new_lang2, LANG_ZH_CN)
        self.assertEqual(get_language(), LANG_ZH_CN)

    def test_translation_formatting(self):
        set_language(LANG_EN_US)
        formatted_en = t("status_active", active=2, total=5)
        self.assertIn("2 of 5 Rules Active", formatted_en)

        set_language(LANG_ZH_CN)
        formatted_zh = t("status_active", active=2, total=5)
        self.assertIn("2 / 5 条规则", formatted_zh)

    def test_fallback_for_unknown_key(self):
        set_language(LANG_ZH_CN)
        self.assertEqual(t("non_existent_key_xyz"), "non_existent_key_xyz")

    def test_localized_option_lists(self):
        set_language(LANG_EN_US)
        modes_en = get_localized_output_modes()
        self.assertEqual(len(modes_en), 3)
        self.assertEqual(modes_en[0][1], "Same Folder")

        set_language(LANG_ZH_CN)
        modes_zh = get_localized_output_modes()
        self.assertEqual(len(modes_zh), 3)
        self.assertEqual(modes_zh[0][1], "原文件夹")

        keeps_zh = get_localized_keep_original_modes()
        self.assertEqual(len(keeps_zh), 3)
        self.assertEqual(keeps_zh[0][1], "保留原始 PNG")

        watches_zh = get_localized_watch_modes()
        self.assertEqual(len(watches_zh), 2)
        self.assertEqual(watches_zh[0][1], "全时持续监控")


if __name__ == "__main__":
    unittest.main()
