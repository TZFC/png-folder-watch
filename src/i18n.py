"""
Internationalization (i18n) module for PNG Folder Watch.
Supports Simplified Chinese (zh-CN) and English (en-US).
Provides seamless language toggling, system locale auto-detection,
and localized strings for GUI, dialogs, cards, badges, tray, and notifications.
"""

import threading
from typing import Dict, List, Tuple

LANG_ZH_CN = "zh-CN"
LANG_EN_US = "en-US"

SUPPORTED_LANGUAGES = [LANG_ZH_CN, LANG_EN_US]

LANGUAGE_NAMES = {
    LANG_ZH_CN: "简体中文",
    LANG_EN_US: "English",
}

# Master translations dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    LANG_ZH_CN: {
        # App & Header
        "app_name": "PNG 图片监控转换器",
        "app_title_short": "PNG Folder Watch",
        "app_subtitle": "游戏截图与文件夹后台静默自动转 JPG 工具",
        "window_title_dashboard": "PNG 图片监控转换器 — 控制面板与规则管理",
        "btn_add_rule": "➕ 添加监控文件夹规则",
        "btn_start_watching": "🚀 启动监控并最小化到托盘",
        "chk_startup": "开机自启（随 Windows 启动并静默运行在系统托盘）",
        "chk_notify": "图片转换完成时弹出系统通知",
        "status_ready": "🟢 就绪 • 已配置 {count} 条规则",
        "status_active": "🟢 运行中 • 已启用 {active} / {total} 条规则",
        "empty_title": "暂未配置任何监控规则",
        "empty_desc": "点击上方「+ 添加监控文件夹规则」开始选择您的第一个截图文件夹。",
        
        # Rule Cards
        "btn_enable": "启用",
        "btn_disable": "停用",
        "btn_edit": "✏️ 编辑",
        "btn_delete": "🗑️ 删除",
        "badge_out_same": "保存: 原文件夹",
        "badge_out_sub": "保存: ./jpg/ 子文件夹",
        "badge_out_mirror": "保存: 镜像目录结构",
        "badge_keep_always": "保留 PNG: 始终保留",
        "badge_keep_never": "保留 PNG: 从不 (自动删除)",
        "badge_keep_delete_no_alpha": "保留 PNG: 仅透明时保留",
        "badge_danger_delete_existing": "⚠️ 自动删除已处理的 PNG",
        "badge_quality": "画质: {quality}%",
        "badge_watch_app": "🎮 仅在 {app} 运行时监控",
        "badge_watch_continuous": "⚡ 全时持续监控",

        # Rule Editor Dialog
        "dialog_title_add": "✨ 添加监控文件夹规则",
        "dialog_title_edit": "✏️ 编辑监控文件夹规则",
        "dialog_banner_title_add": "✨ 添加监控文件夹规则",
        "dialog_banner_title_edit": "✏️ 编辑监控文件夹规则",
        "dialog_banner_sub": "配置监控文件夹路径、自动转换策略及游戏联动触发条件。",
        "sec1_title": "📁 1. 选择要监控的文件夹",
        "sec1_desc": "选择保存 PNG 游戏截图或图片的文件夹。",
        "btn_browse_folder": "📂 浏览文件夹...",
        "no_folder_selected": "⚠️ 尚未选择文件夹 (请点击「浏览文件夹...」)",
        "sec2_title": "💾 2. JPG 图片保存位置",
        "out_same_title": "原文件夹",
        "out_same_desc": "将转换后的 .jpg 与原 .png 保存在同一目录下",
        "out_sub_title": "子文件夹 (./jpg/)",
        "out_sub_desc": "在每个目录下新建 'jpg' 子文件夹保存 .jpg 图片",
        "out_mirror_title": "镜像目录结构 (../jpg-root/)",
        "out_mirror_desc": "在同级目录下创建 'jpg-root' 文件夹并完整镜像原目录层级",
        "sec3_title": "🎨 3. 原 PNG 图片处理策略",
        "keep_always_title": "保留原始 PNG",
        "keep_always_desc": "始终同时保留原 .png 和转换后的 .jpg",
        "keep_never_title": "删除原始 PNG",
        "keep_never_desc": "转换成功后自动删除原 .png 图片以节省磁盘空间",
        "keep_delete_no_alpha_title": "仅在无透明通道时删除（智能保留透明图）",
        "keep_delete_no_alpha_desc": "若图片包含透明像素则保留 .png；若是纯不透明图则安全删除原图",
        "chk_apply_existing": "同步应用于已处理的原图 (危险选项)",
        "apply_existing_desc": "若该文件夹中已有同名 JPG，启动扫描时将自动清理对应的无透明原 PNG 图。",
        "sec4_title": "🎚️ 4. 转换画质与历史图片处理",
        "lbl_jpg_quality": "JPG 画质质量:",
        "qual_maximum": "{val}% (极高质量 / 无损感知)",
        "qual_high": "{val}% (高画质 - 推荐)",
        "qual_balanced": "{val}% (画质与体积均衡)",
        "qual_medium": "{val}% (中等画质 / 极限压缩)",
        "chk_process_existing": "启动时自动转换该文件夹中已存在的历史 PNG 图片",
        "sec5_title": "🎮 5. 监控触发条件",
        "watch_always_title": "全时持续监控",
        "watch_always_desc": "只要本程序在后台运行，就始终实时监控此文件夹",
        "watch_on_app_title": "仅在指定游戏/程序运行时监控",
        "watch_on_app_desc": "仅在检测到目标游戏或应用程序 (.exe) 正在运行时才开启监控",
        "lbl_target_app": "目标游戏或应用程序可执行文件 (.exe):",
        "btn_pick_exe": "🎮 选择游戏 / 程序 (.exe)...",
        "app_selected": "已选择: {name}",
        "no_app_selected": "⚠️ 尚未选择任何 .exe 程序",
        "btn_cancel": "取消",
        "btn_save_rule": "💾 保存规则",

        # Message Dialogs & Alerts
        "msg_folder_required_title": "必须选择文件夹",
        "msg_folder_required_body": "请点击「浏览文件夹...」并选择一个有效的监控文件夹路径。",
        "msg_app_required_title": "必须指定目标程序",
        "msg_app_required_body": "您选择了「仅在指定游戏/程序运行时监控」。\n请点击「选择游戏 / 程序 (.exe)...」指定目标游戏程序。",
        "msg_delete_rule_title": "删除规则",
        "msg_delete_rule_body": "确定要删除针对以下文件夹的监控规则吗？\n{path}",
        "msg_no_rules_title": "未配置任何规则",
        "msg_no_rules_body": "请在启动监控前至少添加一条文件夹监控规则。",
        "dialog_select_folder": "选择要监控 PNG 图片的文件夹",
        "dialog_select_app": "选择目标游戏或应用程序 (.exe)",

        # System Tray & Notifications
        "tray_title": "📸 PNG 图片监控转换器",
        "tray_tooltip_active": "PNG 图片监控转换器 — 正在运行",
        "tray_tooltip_paused": "PNG 图片监控转换器 — 已暂停",
        "tray_status_paused": "⏸️ 状态: 已暂停监控",
        "tray_status_active": "🟢 状态: {active}/{total} 个文件夹正在监控",
        "tray_status_active_app": "🟢 状态: {active}/{total} 个文件夹正在监控 ({app_active} 个游戏联动中)",
        "tray_settings": "⚙️ 设置与规则管理...",
        "tray_resume": "▶️ 恢复监控",
        "tray_pause": "⏸️ 暂停所有监控",
        "tray_open_folder": "📁 打开监控的文件夹",
        "tray_no_folders": "未配置监控文件夹",
        "tray_exit": "❌ 退出程序",
        "notify_app_active_title": "PNG 监控已联动激活",
        "notify_app_active_msg": "检测到 {app_name} 正在运行！\n已开始监控文件夹: {rule_name}",
        "notify_app_idle_title": "PNG 监控已进入休眠",
        "notify_app_idle_msg": "{app_name} 已关闭。\n已停止监控文件夹: {rule_name}",
        "notify_converted_title": "PNG 转换完成 ({rule_name})",
        "notify_saved_msg": "已保存: {filename}",
        "notify_deleted_msg": "原始 PNG 图片已删除",

        # Toggle Label
        "lang_switch_btn": "🌐 English",
    },

    LANG_EN_US: {
        # App & Header
        "app_name": "PNG Folder Watch",
        "app_title_short": "PNG Folder Watch",
        "app_subtitle": "Set-and-forget background converter for game screenshots & folders",
        "window_title_dashboard": "PNG Folder Watch — Dashboard & Rules",
        "btn_add_rule": "➕ Add Watch Folder Rule",
        "btn_start_watching": "🚀 Start Watching & Minimize to Tray",
        "chk_startup": "Start with Windows (Launch silently in system tray on boot)",
        "chk_notify": "Show notification toast on image conversion",
        "status_ready": "🟢 Ready • {count} Rules Configured",
        "status_active": "🟢 Ready • {active} of {total} Rules Active",
        "empty_title": "No Watch Rules Configured Yet",
        "empty_desc": "Click '+ Add Watch Folder Rule' above to select your first screenshot folder.",
        
        # Rule Cards
        "btn_enable": "Enable",
        "btn_disable": "Disable",
        "btn_edit": "✏️ Edit",
        "btn_delete": "🗑️ Delete",
        "badge_out_same": "Save: Same Folder",
        "badge_out_sub": "Save: ./jpg/ Subfolder",
        "badge_out_mirror": "Save: Mirror Structure",
        "badge_keep_always": "Keep PNG: Always",
        "badge_keep_never": "Keep PNG: Never (Delete)",
        "badge_keep_delete_no_alpha": "Keep PNG: Only if Transparent",
        "badge_danger_delete_existing": "⚠️ Deletes Processed PNGs",
        "badge_quality": "Quality: {quality}%",
        "badge_watch_app": "🎮 Active when {app} runs",
        "badge_watch_continuous": "⚡ Continuous Watch",

        # Rule Editor Dialog
        "dialog_title_add": "✨ Add Watch Folder Rule",
        "dialog_title_edit": "✏️ Edit Watch Folder Rule",
        "dialog_banner_title_add": "✨ Add Watch Folder Rule",
        "dialog_banner_title_edit": "✏️ Edit Watch Folder Rule",
        "dialog_banner_sub": "Configure folder location, auto-conversion behavior, and game triggers.",
        "sec1_title": "📁 1. Folder to Watch",
        "sec1_desc": "Choose the folder where your PNG screenshots or images are created.",
        "btn_browse_folder": "📂 Browse Folder...",
        "no_folder_selected": "⚠️ No folder selected yet (Click 'Browse Folder...')",
        "sec2_title": "💾 2. Where to Save JPG Images",
        "out_same_title": "Same Folder",
        "out_same_desc": "Save .jpg directly alongside the original .png",
        "out_sub_title": "Subfolder (./jpg/)",
        "out_sub_desc": "Save .jpg inside a 'jpg' subfolder in each directory",
        "out_mirror_title": "Mirror Structure (../jpg-root/)",
        "out_mirror_desc": "Mirror original folder tree under a sibling 'jpg-root' folder",
        "sec3_title": "🎨 3. Original PNG Handling",
        "keep_always_title": "Keep Original PNG",
        "keep_always_desc": "Always keep both original .png and converted .jpg",
        "keep_never_title": "Delete Original PNG",
        "keep_never_desc": "Always delete original .png after successful conversion",
        "keep_delete_no_alpha_title": "Delete Only If No Transparency",
        "keep_delete_no_alpha_desc": "Keep .png if it has transparent pixels; delete if fully opaque",
        "chk_apply_existing": "Apply to processed images (Danger)",
        "apply_existing_desc": "Delete existing original PNGs in this folder if a matching JPG already exists.",
        "sec4_title": "🎚️ 4. Quality & Existing Images",
        "lbl_jpg_quality": "JPG Quality:",
        "qual_maximum": "{val}% (Maximum Quality)",
        "qual_high": "{val}% (High Quality - Recommended)",
        "qual_balanced": "{val}% (Balanced Quality & Size)",
        "qual_medium": "{val}% (Medium Quality, Small File)",
        "chk_process_existing": "Convert existing PNG images in this folder upon startup",
        "sec5_title": "🎮 5. When to Watch This Folder",
        "watch_always_title": "Watch Continuously",
        "watch_always_desc": "Always active whenever PNG Folder Watch is running",
        "watch_on_app_title": "Watch When Game / App Runs",
        "watch_on_app_desc": "Active only while a selected game or application (.exe) is running",
        "lbl_target_app": "Target Game / Application Executable:",
        "btn_pick_exe": "🎮 Select Game / App (.exe)...",
        "app_selected": "Selected: {name}",
        "no_app_selected": "⚠️ No .exe selected yet",
        "btn_cancel": "Cancel",
        "btn_save_rule": "💾 Save Rule",

        # Message Dialogs & Alerts
        "msg_folder_required_title": "Folder Required",
        "msg_folder_required_body": "Please click 'Browse Folder...' and select a valid folder to watch.",
        "msg_app_required_title": "Game / App Required",
        "msg_app_required_body": "You selected 'Watch When Game / App Runs'.\nPlease click 'Select Game / App (.exe)...' to pick the target game executable.",
        "msg_delete_rule_title": "Delete Rule",
        "msg_delete_rule_body": "Are you sure you want to delete the rule for:\n{path}?",
        "msg_no_rules_title": "No Rules Configured",
        "msg_no_rules_body": "Please add at least one folder watch rule before starting.",
        "dialog_select_folder": "Select Folder to Watch for PNG Images",
        "dialog_select_app": "Select Game or Application Executable (.exe)",

        # System Tray & Notifications
        "tray_title": "📸 PNG Folder Watch",
        "tray_tooltip_active": "PNG Folder Watch — Active",
        "tray_tooltip_paused": "PNG Folder Watch — Paused",
        "tray_status_paused": "⏸️ Status: Paused",
        "tray_status_active": "🟢 Status: {active}/{total} Folders Active",
        "tray_status_active_app": "🟢 Status: {active}/{total} Folders Active ({app_active} Game Active)",
        "tray_settings": "⚙️ Settings & Rules...",
        "tray_resume": "▶️ Resume Watching",
        "tray_pause": "⏸️ Pause All",
        "tray_open_folder": "📁 Open Watched Folder",
        "tray_no_folders": "No folders configured",
        "tray_exit": "❌ Exit",
        "notify_app_active_title": "PNG Folder Watch Active",
        "notify_app_active_msg": "Detected {app_name}!\nWatching folder: {rule_name}",
        "notify_app_idle_title": "PNG Folder Watch Idle",
        "notify_app_idle_msg": "{app_name} closed.\nStopped watching: {rule_name}",
        "notify_converted_title": "PNG Converted ({rule_name})",
        "notify_saved_msg": "Saved: {filename}",
        "notify_deleted_msg": "Original PNG deleted",

        # Toggle Label
        "lang_switch_btn": "🌐 简体中文",
    },
}


def detect_system_language() -> str:
    """
    Detect the user's Windows operating system or user locale.
    Returns 'zh-CN' if Chinese locale is detected, otherwise 'en-US'.
    """
    try:
        import locale
        # locale.getdefaultlocale() is deprecated since Python 3.11 and removed in 3.15.
        # Use locale.getlocale() with a fallback.
        try:
            lang, _ = locale.getlocale()
        except Exception:
            lang = None
        if not lang:
            # Fallback: try getdefaultlocale if still available (Python < 3.15)
            try:
                lang, _ = locale.getdefaultlocale()  # type: ignore[attr-defined]
            except (AttributeError, Exception):
                lang = None
        if lang and (lang.lower().startswith("zh") or "chinese" in lang.lower() or "china" in lang.lower()):
            return LANG_ZH_CN
    except Exception:
        pass

    try:
        import ctypes
        windll = getattr(ctypes, "windll", None)
        if windll:
            # Primary language identifier (bottom 10 bits of LANGID)
            # 0x04 is LANG_CHINESE
            lang_id = windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
            if lang_id == 0x04:
                return LANG_ZH_CN
    except Exception:
        pass

    return LANG_EN_US


_CURRENT_LANGUAGE: str = LANG_ZH_CN
_LANG_LOCK = threading.Lock()


def get_language() -> str:
    """Get the currently active language code."""
    with _LANG_LOCK:
        return _CURRENT_LANGUAGE


def set_language(lang: str) -> str:
    """Set the active language code (must be in SUPPORTED_LANGUAGES)."""
    global _CURRENT_LANGUAGE
    with _LANG_LOCK:
        if lang in SUPPORTED_LANGUAGES:
            _CURRENT_LANGUAGE = lang
        else:
            _CURRENT_LANGUAGE = LANG_ZH_CN
        return _CURRENT_LANGUAGE


def toggle_language() -> str:
    """Toggle between zh-CN and en-US and return new language."""
    current = get_language()
    new_lang = LANG_EN_US if current == LANG_ZH_CN else LANG_ZH_CN
    set_language(new_lang)
    return new_lang


def t(key: str, **kwargs) -> str:
    """
    Translate a key into the currently active language with optional kwargs formatting.
    Falls back to en-US if key is not found in current language, then to key itself.
    """
    lang = get_language()
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS[LANG_ZH_CN])
    
    text = lang_dict.get(key)
    if text is None:
        # Fallback to English
        text = TRANSLATIONS[LANG_EN_US].get(key, key)

    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def get_localized_output_modes() -> List[Tuple[str, str, str]]:
    """Return localized (value, title, description) tuples for output mode option cards."""
    return [
        ("same_folder", t("out_same_title"), t("out_same_desc")),
        ("jpg_subfolder", t("out_sub_title"), t("out_sub_desc")),
        ("mirror_structure", t("out_mirror_title"), t("out_mirror_desc")),
    ]


def get_localized_keep_original_modes() -> List[Tuple[str, str, str]]:
    """Return localized (value, title, description) tuples for keep original option cards."""
    return [
        ("always", t("keep_always_title"), t("keep_always_desc")),
        ("never", t("keep_never_title"), t("keep_never_desc")),
        ("delete_if_no_alpha", t("keep_delete_no_alpha_title"), t("keep_delete_no_alpha_desc")),
    ]


def get_localized_watch_modes() -> List[Tuple[str, str, str]]:
    """Return localized (value, title, description) tuples for watch mode option cards."""
    return [
        ("always", t("watch_always_title"), t("watch_always_desc")),
        ("on_app", t("watch_on_app_title"), t("watch_on_app_desc")),
    ]
