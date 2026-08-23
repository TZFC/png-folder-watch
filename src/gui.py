"""
Modern Graphical User Interface for PNG Folder Watch.
Features a sleek desktop UI with zero-freeform-input rule editor,
custom option cards, real-time quality sliders, and native Windows pickers.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional, Callable, List
from PIL import Image, ImageTk

from .config import (
    ConfigManager,
    create_default_rule,
    OUTPUT_MODE_SAME,
    OUTPUT_MODE_JPG_SUB,
    OUTPUT_MODE_MIRROR,
    OUTPUT_MODES,
    KEEP_ORIGINAL_ALWAYS,
    KEEP_ORIGINAL_NEVER,
    KEEP_ORIGINAL_DELETE_NO_ALPHA,
    KEEP_ORIGINAL_MODES,
    WATCH_MODE_ALWAYS,
    WATCH_MODE_ON_APP,
    WATCH_MODES,
)
from .startup import is_startup_enabled, set_startup
from .icon_generator import ensure_icon_files, ICON_PNG_PATH, ICON_ICO_PATH

# Enable high DPI awareness on Windows
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class ModernOptionCard(tk.Frame):
    """A clickable card widget that acts as an enhanced radio button."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        description: str,
        value: str,
        variable: tk.StringVar,
        on_select: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#e2e8f0", padx=12, pady=10)
        self.value = value
        self.variable = variable
        self.on_select = on_select

        self.cursor = "hand2"
        self.config(cursor=self.cursor)

        # Left radio indicator
        self.radio_lbl = tk.Label(
            self,
            text="○",
            font=("Segoe UI", 12),
            bg="#ffffff",
            fg="#94a3b8",
            cursor="hand2",
        )
        self.radio_lbl.pack(side=tk.LEFT, padx=(0, 10))

        # Text box
        text_frame = tk.Frame(self, bg="#ffffff", cursor="hand2")
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.lbl_title = tk.Label(
            text_frame,
            text=title,
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#0f172a",
            anchor="w",
            cursor="hand2",
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_desc = tk.Label(
            text_frame,
            text=description,
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#64748b",
            anchor="w",
            wraplength=520,
            justify="left",
            cursor="hand2",
        )
        self.lbl_desc.pack(anchor="w", pady=(2, 0))

        # Bind click events
        for widget in (self, self.radio_lbl, text_frame, self.lbl_title, self.lbl_desc):
            widget.bind("<Button-1>", lambda e: self.select())
            widget.bind("<Enter>", lambda e: self._on_hover(True))
            widget.bind("<Leave>", lambda e: self._on_hover(False))

        self.update_state()

    def _on_hover(self, is_hover: bool):
        if self.variable.get() != self.value:
            bg = "#f8fafc" if is_hover else "#ffffff"
            border = "#cbd5e1" if is_hover else "#e2e8f0"
            self.config(bg=bg, highlightbackground=border)
            self.radio_lbl.config(bg=bg)
            self.lbl_title.config(bg=bg)
            self.lbl_desc.config(bg=bg)

    def select(self):
        self.variable.set(self.value)
        if self.on_select:
            self.on_select(self.value)
        # Notify siblings to refresh
        for child in self.master.winfo_children():
            if isinstance(child, ModernOptionCard):
                child.update_state()

    def update_state(self):
        is_selected = (self.variable.get() == self.value)
        if is_selected:
            self.config(bg="#eff6ff", highlightbackground="#3b82f6", highlightthickness=2)
            self.radio_lbl.config(text="●", fg="#2563eb", bg="#eff6ff")
            self.lbl_title.config(fg="#1d4ed8", bg="#eff6ff")
            self.lbl_desc.config(fg="#3b82f6", bg="#eff6ff")
        else:
            self.config(bg="#ffffff", highlightbackground="#e2e8f0", highlightthickness=1)
            self.radio_lbl.config(text="○", fg="#94a3b8", bg="#ffffff")
            self.lbl_title.config(fg="#0f172a", bg="#ffffff")
            self.lbl_desc.config(fg="#64748b", bg="#ffffff")


class RuleEditorDialog(tk.Toplevel):
    """
    Modern modal dialog for configuring a folder watch rule.
    Zero freeform text input: all choices use constrained pickers & option cards.
    """

    def __init__(
        self,
        parent: tk.Widget,
        rule: Optional[Dict[str, Any]] = None,
        on_save: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.on_save = on_save
        self.is_new = rule is None
        self.rule = rule.copy() if rule else create_default_rule()

        self.title("✨ Add Watch Folder Rule" if self.is_new else "✏️ Edit Watch Folder Rule")
        self.geometry("720x760")
        self.minsize(680, 640)
        self.config(bg="#f8fafc")

        ensure_icon_files()
        if os.path.exists(ICON_ICO_PATH):
            try:
                self.iconbitmap(ICON_ICO_PATH)
            except Exception:
                pass

        self._init_variables()
        self._build_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        pw = self.master.winfo_width()
        ph = self.master.winfo_height()
        px = self.master.winfo_x()
        py = self.master.winfo_y()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _init_variables(self):
        self.var_folder = tk.StringVar(value=self.rule.get("watch_folder", ""))
        self.var_output_mode = tk.StringVar(value=self.rule.get("output_mode", OUTPUT_MODE_SAME))
        self.var_keep_original = tk.StringVar(value=self.rule.get("keep_original", KEEP_ORIGINAL_ALWAYS))
        self.var_apply_delete_to_existing = tk.BooleanVar(value=self.rule.get("apply_delete_to_existing", False))
        self.var_jpg_quality = tk.IntVar(value=int(self.rule.get("jpg_quality", 90)))
        self.var_process_existing = tk.BooleanVar(value=self.rule.get("process_existing", True))
        self.var_watch_mode = tk.StringVar(value=self.rule.get("watch_mode", WATCH_MODE_ALWAYS))
        self.var_app_path = tk.StringVar(value=self.rule.get("target_app_path", ""))
        self.var_app_name = tk.StringVar(value=self.rule.get("target_app_name", ""))

    def _build_ui(self):
        # Dialog Header Banner
        header = tk.Frame(self, bg="#0f172a", padx=20, pady=16)
        header.pack(fill=tk.X)

        lbl_head_title = tk.Label(
            header,
            text="✨ Add Watch Folder Rule" if self.is_new else "✏️ Edit Watch Folder Rule",
            font=("Segoe UI", 13, "bold"),
            bg="#0f172a",
            fg="#ffffff",
        )
        lbl_head_title.pack(anchor="w")

        lbl_head_sub = tk.Label(
            header,
            text="Configure folder location, auto-conversion behavior, and game triggers.",
            font=("Segoe UI", 9),
            bg="#0f172a",
            fg="#94a3b8",
        )
        lbl_head_sub.pack(anchor="w", pady=(2, 0))

        # Scrollable Form Canvas
        content_frame = tk.Frame(self, bg="#f8fafc")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        canvas = tk.Canvas(content_frame, bg="#f8fafc", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg="#f8fafc")

        scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_content, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ----------------------------------------------------
        # Section 1: Folder Selection
        # ----------------------------------------------------
        sec1 = self._create_section(scroll_content, "📁 1. Folder to Watch")
        
        lbl_sec1_desc = tk.Label(
            sec1,
            text="Choose the folder where your PNG screenshots or images are created.",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#64748b",
        )
        lbl_sec1_desc.pack(anchor="w", pady=(0, 8))

        folder_bar = tk.Frame(sec1, bg="#ffffff")
        folder_bar.pack(fill=tk.X)

        btn_browse = tk.Button(
            folder_bar,
            text="📂 Browse Folder...",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._pick_folder,
        )
        btn_browse.pack(side=tk.LEFT, padx=(0, 10))

        self.chip_folder = tk.Label(
            folder_bar,
            textvariable=self.var_folder,
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg="#1e40af" if self.var_folder.get() else "#dc2626",
            padx=10,
            pady=6,
            relief="solid",
            borderwidth=1,
            wraplength=400,
        )
        self.chip_folder.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if not self.var_folder.get():
            self.chip_folder.config(text="⚠️ No folder selected yet (Click 'Browse Folder...')")

        # ----------------------------------------------------
        # Section 2: Output Location
        # ----------------------------------------------------
        sec2 = self._create_section(scroll_content, "💾 2. Where to Save JPG Images")

        for mode_val, title, desc in OUTPUT_MODES:
            card = ModernOptionCard(
                sec2,
                title=title,
                description=desc,
                value=mode_val,
                variable=self.var_output_mode,
            )
            card.pack(fill=tk.X, pady=3)

        # ----------------------------------------------------
        # Section 3: Original PNG Handling
        # ----------------------------------------------------
        sec3 = self._create_section(scroll_content, "🎨 3. Original PNG Handling")

        for mode_val, title, desc in KEEP_ORIGINAL_MODES:
            card = ModernOptionCard(
                sec3,
                title=title,
                description=desc,
                value=mode_val,
                variable=self.var_keep_original,
                on_select=lambda v: self._update_apply_existing_visibility(),
            )
            card.pack(fill=tk.X, pady=3)

        # Danger Option: Apply delete to already processed images
        self.box_apply_existing = tk.Frame(
            sec3,
            bg="#fef2f2",
            padx=12,
            pady=10,
            highlightthickness=1,
            highlightbackground="#fca5a5",
        )

        chk_apply_existing = ttk.Checkbutton(
            self.box_apply_existing,
            text="Apply to processed images (Danger)",
            variable=self.var_apply_delete_to_existing,
        )
        chk_apply_existing.pack(anchor="w")

        lbl_danger_desc = tk.Label(
            self.box_apply_existing,
            text="Delete existing original PNGs in this folder if a matching JPG already exists.",
            font=("Segoe UI", 8),
            bg="#fef2f2",
            fg="#991b1b",
            anchor="w",
            wraplength=480,
            justify="left",
        )
        lbl_danger_desc.pack(anchor="w", padx=(20, 0), pady=(2, 0))

        self._update_apply_existing_visibility()

        # ----------------------------------------------------
        # Section 4: JPG Quality & Options
        # ----------------------------------------------------
        sec4 = self._create_section(scroll_content, "🎚️ 4. Quality & Existing Images")

        q_row = tk.Frame(sec4, bg="#ffffff")
        q_row.pack(fill=tk.X, pady=(0, 6))

        tk.Label(q_row, text="JPG Quality:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#0f172a").pack(side=tk.LEFT)

        self.lbl_qual_badge = tk.Label(
            q_row,
            text=f"{self.var_jpg_quality.get()}% (High Quality)",
            font=("Segoe UI", 9, "bold"),
            bg="#eff6ff",
            fg="#2563eb",
            padx=8,
            pady=2,
            relief="solid",
            borderwidth=1,
        )
        self.lbl_qual_badge.pack(side=tk.LEFT, padx=(10, 0))

        slider_bar = tk.Frame(sec4, bg="#ffffff")
        slider_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(slider_bar, text="50%", font=("Segoe UI", 8), bg="#ffffff", fg="#94a3b8").pack(side=tk.LEFT)

        scale = ttk.Scale(
            slider_bar,
            from_=50,
            to=100,
            variable=self.var_jpg_quality,
            command=self._on_quality_change,
        )
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        tk.Label(slider_bar, text="100%", font=("Segoe UI", 8), bg="#ffffff", fg="#94a3b8").pack(side=tk.RIGHT)

        chk_exist = ttk.Checkbutton(
            sec4,
            text="Convert existing PNG images in this folder upon startup",
            variable=self.var_process_existing,
        )
        chk_exist.pack(anchor="w", pady=(4, 0))

        # ----------------------------------------------------
        # Section 5: When to Watch (Per-Rule Trigger)
        # ----------------------------------------------------
        sec5 = self._create_section(scroll_content, "🎮 5. When to Watch This Folder")

        for mode_val, title, desc in WATCH_MODES:
            card = ModernOptionCard(
                sec5,
                title=title,
                description=desc,
                value=mode_val,
                variable=self.var_watch_mode,
                on_select=lambda v: self._update_app_picker_visibility(),
            )
            card.pack(fill=tk.X, pady=3)

        # App Picker container inside section 5
        self.app_picker_box = tk.Frame(sec5, bg="#f8fafc", padx=12, pady=10, highlightthickness=1, highlightbackground="#cbd5e1")
        self.app_picker_box.pack(fill=tk.X, pady=(6, 0))

        tk.Label(
            self.app_picker_box,
            text="Target Game / Application Executable:",
            font=("Segoe UI", 9, "bold"),
            bg="#f8fafc",
            fg="#0f172a",
        ).pack(anchor="w", pady=(0, 6))

        app_btn_row = tk.Frame(self.app_picker_box, bg="#f8fafc")
        app_btn_row.pack(fill=tk.X)

        btn_pick_exe = tk.Button(
            app_btn_row,
            text="🎮 Select Game / App (.exe)...",
            font=("Segoe UI", 9, "bold"),
            bg="#8b5cf6",
            fg="#ffffff",
            activebackground="#7c3aed",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._pick_app_exe,
        )
        btn_pick_exe.pack(side=tk.LEFT, padx=(0, 10))

        self.chip_app = tk.Label(
            app_btn_row,
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#16a34a" if self.var_app_name.get() else "#dc2626",
            padx=10,
            pady=6,
            relief="solid",
            borderwidth=1,
            wraplength=340,
        )
        self.chip_app.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._update_app_label()
        self._update_app_picker_visibility()

        # ----------------------------------------------------
        # Bottom Dialog Actions
        # ----------------------------------------------------
        footer = tk.Frame(self, bg="#ffffff", padx=20, pady=12, highlightthickness=1, highlightbackground="#e2e8f0")
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        btn_cancel = tk.Button(
            footer,
            text="Cancel",
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg="#475569",
            activebackground="#e2e8f0",
            relief="flat",
            padx=16,
            pady=7,
            cursor="hand2",
            command=self.destroy,
        )
        btn_cancel.pack(side=tk.RIGHT, padx=(8, 0))

        btn_save = tk.Button(
            footer,
            text="💾 Save Rule",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief="flat",
            padx=20,
            pady=7,
            cursor="hand2",
            command=self._save_rule,
        )
        btn_save.pack(side=tk.RIGHT)

    def _create_section(self, parent: tk.Widget, title: str) -> tk.Frame:
        card = tk.Frame(parent, bg="#ffffff", padx=16, pady=14, highlightthickness=1, highlightbackground="#e2e8f0")
        card.pack(fill=tk.X, pady=(0, 12))

        lbl_title = tk.Label(
            card,
            text=title,
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#0f172a",
        )
        lbl_title.pack(anchor="w", pady=(0, 8))
        return card

    def _on_quality_change(self, value):
        val = int(float(value))
        if val >= 95:
            qual_text = f"{val}% (Maximum Quality)"
        elif val >= 85:
            qual_text = f"{val}% (High Quality - Recommended)"
        elif val >= 70:
            qual_text = f"{val}% (Balanced Quality & Size)"
        else:
            qual_text = f"{val}% (Medium Quality, Small File)"
        self.lbl_qual_badge.config(text=qual_text)

    def _update_apply_existing_visibility(self):
        val = self.var_keep_original.get()
        if val in (KEEP_ORIGINAL_NEVER, KEEP_ORIGINAL_DELETE_NO_ALPHA):
            self.box_apply_existing.pack(fill=tk.X, pady=(8, 0))
        else:
            self.var_apply_delete_to_existing.set(False)
            self.box_apply_existing.pack_forget()

    def _update_app_picker_visibility(self):
        if self.var_watch_mode.get() == WATCH_MODE_ON_APP:
            self.app_picker_box.pack(fill=tk.X, pady=(6, 0))
        else:
            self.app_picker_box.pack_forget()

    def _update_app_label(self):
        name = self.var_app_name.get()
        if name:
            self.chip_app.config(
                text=f"Selected: {name}",
                fg="#16a34a",
                bg="#f0fdf4",
                highlightbackground="#bbf7d0",
            )
        else:
            self.chip_app.config(
                text="⚠️ No .exe selected yet",
                fg="#dc2626",
                bg="#fef2f2",
                highlightbackground="#fecaca",
            )

    def _pick_folder(self):
        initial = self.var_folder.get() or os.path.expanduser("~")
        selected = filedialog.askdirectory(
            parent=self,
            title="Select Folder to Watch for PNG Images",
            initialdir=initial,
        )
        if selected:
            norm = os.path.normpath(selected)
            self.var_folder.set(norm)
            self.chip_folder.config(
                text=norm,
                fg="#1e40af",
                bg="#eff6ff",
                font=("Segoe UI", 9, "bold"),
            )

    def _pick_app_exe(self):
        initial_dir = os.path.dirname(self.var_app_path.get()) if self.var_app_path.get() else r"C:\Program Files"
        selected = filedialog.askopenfilename(
            parent=self,
            title="Select Game or Application Executable (.exe)",
            initialdir=initial_dir,
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")],
        )
        if selected:
            norm = os.path.normpath(selected)
            name = os.path.basename(norm)
            self.var_app_path.set(norm)
            self.var_app_name.set(name)
            self._update_app_label()

    def _save_rule(self):
        folder = self.var_folder.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror(
                "Folder Required",
                "Please click 'Browse Folder...' and select a valid folder to watch.",
                parent=self,
            )
            return

        if self.var_watch_mode.get() == WATCH_MODE_ON_APP:
            if not self.var_app_path.get() and not self.var_app_name.get():
                messagebox.showerror(
                    "Game / App Required",
                    "You selected 'Watch When Game / App Runs'.\nPlease click 'Select Game / App (.exe)...' to pick the target game executable.",
                    parent=self,
                )
                return

        folder_base = os.path.basename(os.path.normpath(folder))
        rule_name = folder_base if folder_base else folder

        self.rule["name"] = rule_name
        self.rule["watch_folder"] = folder
        self.rule["output_mode"] = self.var_output_mode.get()
        self.rule["keep_original"] = self.var_keep_original.get()
        self.rule["apply_delete_to_existing"] = (
            self.var_apply_delete_to_existing.get()
            if self.var_keep_original.get() != KEEP_ORIGINAL_ALWAYS
            else False
        )
        self.rule["jpg_quality"] = int(self.var_jpg_quality.get())
        self.rule["process_existing"] = self.var_process_existing.get()
        self.rule["watch_mode"] = self.var_watch_mode.get()
        self.rule["target_app_path"] = self.var_app_path.get()
        self.rule["target_app_name"] = self.var_app_name.get() or (
            os.path.basename(self.var_app_path.get()) if self.var_app_path.get() else ""
        )
        self.rule["enabled"] = True

        if self.on_save:
            self.on_save(self.rule)
        self.destroy()


class ConfigApp(tk.Tk):
    """
    Modern Configuration Window for PNG Folder Watch.
    Features card-based rule management, global Windows startup toggle, and status badges.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        on_start_watching: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.config_manager = config_manager
        self.on_start_watching = on_start_watching

        self.title("PNG Folder Watch — Dashboard & Rules")
        self.geometry("940x700")
        self.minsize(860, 580)
        self.config(bg="#f8fafc")

        ensure_icon_files()
        if os.path.exists(ICON_ICO_PATH):
            try:
                self.iconbitmap(ICON_ICO_PATH)
            except Exception:
                pass

        self._init_variables()
        self._build_ui()
        self.center_window()
        self.refresh_rules_list()

        self._prompt_after_id = None
        # Prompt for first rule if empty
        if not self.config_manager.rules:
            self._prompt_after_id = self.after(200, self._open_add_rule_dialog)

    def _init_variables(self):
        self.var_startup = tk.BooleanVar(value=self.config_manager.start_with_windows)
        self.var_notify = tk.BooleanVar(value=self.config_manager.notify_on_convert)

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        # ----------------------------------------------------
        # Modern Dark Hero Header
        # ----------------------------------------------------
        hero = tk.Frame(self, bg="#0f172a", padx=20, pady=16)
        hero.pack(fill=tk.X)

        title_box = tk.Frame(hero, bg="#0f172a")
        title_box.pack(side=tk.LEFT, fill=tk.Y)

        lbl_hero_title = tk.Label(
            title_box,
            text="📸 PNG Folder Watch",
            font=("Segoe UI", 16, "bold"),
            bg="#0f172a",
            fg="#ffffff",
        )
        lbl_hero_title.pack(anchor="w")

        lbl_hero_sub = tk.Label(
            title_box,
            text="Set-and-forget background converter for game screenshots & folders",
            font=("Segoe UI", 9),
            bg="#0f172a",
            fg="#94a3b8",
        )
        lbl_hero_sub.pack(anchor="w", pady=(2, 0))

        # Add Rule Button in Hero
        btn_add = tk.Button(
            hero,
            text="➕ Add Watch Folder Rule",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._open_add_rule_dialog,
        )
        btn_add.pack(side=tk.RIGHT, padx=4)

        # ----------------------------------------------------
        # Status & Overview Bar
        # ----------------------------------------------------
        status_bar = tk.Frame(self, bg="#f1f5f9", padx=20, pady=8, highlightthickness=1, highlightbackground="#e2e8f0")
        status_bar.pack(fill=tk.X)

        self.lbl_status_badge = tk.Label(
            status_bar,
            text="🟢 Ready • 0 Rules Configured",
            font=("Segoe UI", 9, "bold"),
            bg="#f1f5f9",
            fg="#334155",
        )
        self.lbl_status_badge.pack(side=tk.LEFT)

        # ----------------------------------------------------
        # Scrollable Rules List Container
        # ----------------------------------------------------
        list_container = tk.Frame(self, bg="#f8fafc", padx=16, pady=10)
        list_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(list_container, bg="#f8fafc", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.cards_frame = tk.Frame(self.canvas, bg="#f8fafc")

        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")

        def _on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)

        self.canvas.bind("<Configure>", _on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ----------------------------------------------------
        # Bottom Global Settings & Actions Footer
        # ----------------------------------------------------
        footer = tk.Frame(self, bg="#ffffff", padx=24, pady=16, highlightthickness=1, highlightbackground="#e2e8f0")
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        # Footer Action Button (Pack FIRST on RIGHT to guarantee full width and prevent overflow)
        btn_start = tk.Button(
            footer,
            text="🚀 Start Watching & Minimize to Tray",
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief="flat",
            padx=22,
            pady=10,
            cursor="hand2",
            command=self._on_start_and_close,
        )
        btn_start.pack(side=tk.RIGHT, padx=(16, 0))

        # Global Options (Checkboxes stacked vertically on LEFT)
        global_opts = tk.Frame(footer, bg="#ffffff")
        global_opts.pack(side=tk.LEFT, fill=tk.X, expand=True)

        chk_win = ttk.Checkbutton(
            global_opts,
            text="Start with Windows (Launch silently in system tray on boot)",
            variable=self.var_startup,
            command=self._on_toggle_startup,
        )
        chk_win.pack(anchor="w", pady=(0, 6))

        chk_notify = ttk.Checkbutton(
            global_opts,
            text="Show notification toast on image conversion",
            variable=self.var_notify,
            command=self._on_toggle_notify,
        )
        chk_notify.pack(anchor="w")

    def _on_toggle_startup(self):
        val = self.var_startup.get()
        self.config_manager.start_with_windows = val
        self.config_manager.save()
        set_startup(val)

    def _on_toggle_notify(self):
        val = self.var_notify.get()
        self.config_manager.notify_on_convert = val
        self.config_manager.save()

    def _on_start_and_close(self):
        if not self.config_manager.rules:
            messagebox.showwarning(
                "No Rules Configured",
                "Please add at least one folder watch rule before starting.",
                parent=self,
            )
            return

        self.config_manager.save()
        if self.on_start_watching:
            self.on_start_watching()
        self.destroy()

    def destroy(self):
        if hasattr(self, "_prompt_after_id") and self._prompt_after_id:
            try:
                self.after_cancel(self._prompt_after_id)
            except Exception:
                pass
            self._prompt_after_id = None
        super().destroy()

    def refresh_rules_list(self):
        """Re-render the list of rule cards."""
        for child in self.cards_frame.winfo_children():
            child.destroy()

        rules = self.config_manager.rules
        active_count = sum(1 for r in rules if r.get("enabled", True))
        self.lbl_status_badge.config(
            text=f"🟢 Ready • {active_count} of {len(rules)} Rules Active"
        )

        if not rules:
            empty_frame = tk.Frame(self.cards_frame, bg="#ffffff", padx=30, pady=40, highlightthickness=1, highlightbackground="#e2e8f0")
            empty_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=10)

            tk.Label(
                empty_frame,
                text="📂",
                font=("Segoe UI", 32),
                bg="#ffffff",
            ).pack(pady=(0, 8))

            tk.Label(
                empty_frame,
                text="No Watch Rules Configured Yet",
                font=("Segoe UI", 12, "bold"),
                bg="#ffffff",
                fg="#0f172a",
            ).pack()

            tk.Label(
                empty_frame,
                text="Click '+ Add Watch Folder Rule' above to select your first screenshot folder.",
                font=("Segoe UI", 9),
                bg="#ffffff",
                fg="#64748b",
            ).pack(pady=(4, 0))
            return

        for idx, rule in enumerate(rules):
            self._create_rule_card(rule, idx)

    def _create_rule_card(self, rule: Dict[str, Any], idx: int):
        is_enabled = rule.get("enabled", True)
        card_bg = "#ffffff" if is_enabled else "#f8fafc"
        border_color = "#e2e8f0" if is_enabled else "#cbd5e1"

        card = tk.Frame(
            self.cards_frame,
            bg=card_bg,
            padx=16,
            pady=14,
            highlightthickness=1,
            highlightbackground=border_color,
        )
        card.pack(fill=tk.X, padx=4, pady=6)

        # Top Row: Rule Name & Actions
        top_row = tk.Frame(card, bg=card_bg)
        top_row.pack(fill=tk.X, pady=(0, 6))

        name_box = tk.Frame(top_row, bg=card_bg)
        name_box.pack(side=tk.LEFT)

        status_dot = "🟢" if is_enabled else "⚪"
        lbl_name = tk.Label(
            name_box,
            text=f"{status_dot} {rule.get('name', 'Folder Rule')}",
            font=("Segoe UI", 11, "bold"),
            bg=card_bg,
            fg="#0f172a" if is_enabled else "#94a3b8",
        )
        lbl_name.pack(side=tk.LEFT)

        # Action Buttons
        btn_box = tk.Frame(top_row, bg=card_bg)
        btn_box.pack(side=tk.RIGHT)

        btn_toggle = tk.Button(
            btn_box,
            text="Disable" if is_enabled else "Enable",
            font=("Segoe UI", 8),
            bg="#f1f5f9",
            fg="#334155" if is_enabled else "#15803d",
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=lambda r=rule: self._toggle_rule(r),
        )
        btn_toggle.pack(side=tk.LEFT, padx=3)

        btn_edit = tk.Button(
            btn_box,
            text="✏️ Edit",
            font=("Segoe UI", 8),
            bg="#eff6ff",
            fg="#1d4ed8",
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=lambda r=rule: self._open_edit_rule_dialog(r),
        )
        btn_edit.pack(side=tk.LEFT, padx=3)

        btn_del = tk.Button(
            btn_box,
            text="🗑️ Delete",
            font=("Segoe UI", 8),
            bg="#fef2f2",
            fg="#b91c1c",
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=lambda r=rule: self._delete_rule(r),
        )
        btn_del.pack(side=tk.LEFT, padx=3)

        # Watched Folder Path Chip
        folder_path = rule.get("watch_folder", "")
        folder_row = tk.Frame(card, bg=card_bg)
        folder_row.pack(fill=tk.X, pady=(2, 8))

        lbl_path_chip = tk.Label(
            folder_row,
            text=f"📁 {folder_path}",
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg="#1e40af",
            padx=8,
            pady=4,
            relief="solid",
            borderwidth=1,
            wraplength=780,
            justify="left",
        )
        lbl_path_chip.pack(anchor="w")

        # Badges Row
        badges_row = tk.Frame(card, bg=card_bg)
        badges_row.pack(fill=tk.X)

        # Output Badge
        out_mode = rule.get("output_mode", OUTPUT_MODE_SAME)
        out_labels = {
            OUTPUT_MODE_SAME: "Save: Same Folder",
            OUTPUT_MODE_JPG_SUB: "Save: ./jpg/ Subfolder",
            OUTPUT_MODE_MIRROR: "Save: Mirror Structure",
        }
        self._add_badge(badges_row, out_labels.get(out_mode, "Same Folder"), "#eff6ff", "#1d4ed8", "#bfdbfe")

        # Keep Badge
        keep_mode = rule.get("keep_original", KEEP_ORIGINAL_ALWAYS)
        keep_labels = {
            KEEP_ORIGINAL_ALWAYS: "Keep PNG: Always",
            KEEP_ORIGINAL_NEVER: "Keep PNG: Never (Delete)",
            KEEP_ORIGINAL_DELETE_NO_ALPHA: "Keep PNG: Only if Transparent",
        }
        self._add_badge(badges_row, keep_labels.get(keep_mode, "Keep"), "#f8fafc", "#475569", "#cbd5e1")

        if is_enabled and rule.get("apply_delete_to_existing", False) and keep_mode != KEEP_ORIGINAL_ALWAYS:
            self._add_badge(badges_row, "⚠️ Deletes Processed PNGs", "#fef2f2", "#b91c1c", "#fca5a5")

        # Quality Badge
        quality = rule.get("jpg_quality", 90)
        self._add_badge(badges_row, f"Quality: {quality}%", "#f8fafc", "#475569", "#cbd5e1")

        # Trigger / Watch Mode Badge
        watch_mode = rule.get("watch_mode", WATCH_MODE_ALWAYS)
        if watch_mode == WATCH_MODE_ON_APP:
            app_name = rule.get("target_app_name") or os.path.basename(rule.get("target_app_path", "Game.exe"))
            self._add_badge(badges_row, f"🎮 Active when {app_name} runs", "#f5f3ff", "#6d28d9", "#ddd6fe")
        else:
            self._add_badge(badges_row, "⚡ Continuous Watch", "#f0fdf4", "#15803d", "#bbf7d0")

    def _add_badge(self, parent: tk.Frame, text: str, bg: str, fg: str, border: str):
        badge = tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 8),
            bg=bg,
            fg=fg,
            padx=6,
            pady=2,
            relief="solid",
            borderwidth=1,
        )
        badge.pack(side=tk.LEFT, padx=(0, 6))

    def _open_add_rule_dialog(self):
        RuleEditorDialog(
            parent=self,
            rule=None,
            on_save=self._on_rule_saved,
        )

    def _open_edit_rule_dialog(self, rule: Dict[str, Any]):
        RuleEditorDialog(
            parent=self,
            rule=rule,
            on_save=self._on_rule_saved,
        )

    def _on_rule_saved(self, rule: Dict[str, Any]):
        rule_id = rule.get("id")
        existing = self.config_manager.get_rule(rule_id)
        if existing:
            self.config_manager.update_rule(rule_id, rule)
        else:
            self.config_manager.add_rule(rule)
        self.refresh_rules_list()

    def _toggle_rule(self, rule: Dict[str, Any]):
        rule["enabled"] = not rule.get("enabled", True)
        self.config_manager.update_rule(rule["id"], rule)
        self.refresh_rules_list()

    def _delete_rule(self, rule: Dict[str, Any]):
        confirm = messagebox.askyesno(
            "Delete Rule",
            f"Are you sure you want to delete the rule for:\n{rule.get('watch_folder')}?",
            parent=self,
        )
        if confirm:
            self.config_manager.remove_rule(rule["id"])
            self.refresh_rules_list()


def show_config_gui(config_manager: Optional[ConfigManager] = None, on_start_callback: Optional[Callable] = None):
    """Launch the modern configuration GUI."""
    cm = config_manager or ConfigManager()
    app = ConfigApp(cm, on_start_watching=on_start_callback)
    app.mainloop()


if __name__ == "__main__":
    show_config_gui()
