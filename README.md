# 📸 PNG Folder Watch

> **Set-and-forget automatic PNG to JPG converter for Windows.**
>
> Watches your screenshot folders, game captures, or scan directories and automatically converts new PNGs into lightweight, high-quality JPGs in real-time.

---

## ✨ Key Features

- **🎨 Modernized Desktop UI**: Sleek dark-slate hero header, interactive selectable option cards, live quality sliders, status badges, and path chips.
- **🛡️ 100% Constrained Choices (Zero Typing Required)**: Every setting uses native Windows folder/file path finders, interactive option cards, sliders, or checkboxes.
- **📁 Flexible Output Locations**:
  - **Same Folder (Default)**: Save `.jpg` alongside your `.png`.
  - **Subfolder (`./jpg/`)**: Save `.jpg` in a neat `jpg` subfolder.
  - **Mirror Hierarchy (`../jpg-root/`)**: Mirror the entire folder structure in a sibling folder.
- **🖼️ Intelligent Transparency Protection**:
  - Keep both `.png` and `.jpg`.
  - Always delete original `.png` after conversion.
  - **Delete only if no transparency**: Keeps `.png` if it has transparent pixels (preserving alpha), but deletes original if it's fully opaque.
- **🎚️ Configurable JPG Quality**: Visual slider with real-time percentage display (default 90%).
- **⚡ Catch Existing Images**: Option to convert existing PNGs in folder on startup (default enabled).
- **🎮 Per-Rule Game / App Triggers**:
  - Each rule can either watch continuously or watch **only while a specific game or app (.exe) is running** (selected via native Windows `.exe` path finder).
- **🚀 Global Windows Startup Toggle**: One-click checkbox to automatically start PNG Folder Watch in the system tray on Windows boot.
- **📌 System Tray Background Service**:
  - Unobtrusive tray icon with quick pause/resume, status info, settings access, and one-click folder opening.
  - Native Windows toast notifications when files are converted.
- **🔀 Multi-Rule Support**: Monitor multiple folders simultaneously with different rules.

---

## 🚀 Quick Start Guide

### 1. Download & Extract
Download or place this folder anywhere on your computer (e.g. `C:\Tools\PNGWatch`).

### 2. Double-Click `PNGWatch.bat`
- On first launch, the app automatically prepares its self-contained runtime (~11MB) in a couple of seconds.
- The **Settings & Rules** window will appear automatically.

### 3. Set Up Your First Watch Rule
1. Click **📁 Browse Folder...** to choose the folder containing your screenshots or images.
2. Select your preferred **JPG Location** (Same folder, `./jpg/` subfolder, or mirrored folder).
3. Select your **Original PNG Handling** policy (Keep original, delete always, or delete only if no transparency).
4. Adjust **JPG Quality** slider (default 90% is optimal).
5. Choose **When to Watch** (Continuous or only when a game/app is running).
6. Click **💾 Save Rule**.

### 4. Start Watching
Click **🚀 Start Watching & Minimize to Tray**. The app will sit quietly in your Windows taskbar tray (near the clock) and convert files automatically as soon as they appear!

---

## ⚙️ Modifying Rules Later

To change rules or add new folders:
- **Option A**: Double-click `PNGWatch.bat` again.
- **Option B**: Right-click the **PNG Folder Watch** icon in your system tray and select **⚙️ Settings & Rules...**.

---

## 🗂️ Project Structure

```text
png-folder-watch/
├── PNGWatch.bat            # Double-click launcher for Windows
├── setup_runtime.ps1       # Self-contained runtime bootstrapper
├── README.md               # User documentation
├── requirements.txt        # Package dependencies
├── assets/
│   ├── icon.ico            # Windows application icon
│   └── icon.png            # System tray icon
├── src/
│   ├── config.py           # Configuration and rules manager
│   ├── converter.py        # Pillow PNG->JPG conversion & alpha detection
│   ├── watcher.py          # Watchdog folder monitoring
│   ├── process_monitor.py  # psutil background process monitor
│   ├── gui.py              # Modern Tkinter configuration GUI
│   ├── tray.py             # Pystray Windows system tray controller
│   ├── startup.py          # Windows Startup shortcut manager
│   ├── icon_generator.py   # Icon graphics generator
│   └── main.py             # Application entry point & single-instance lock
└── tests/
    ├── test_all.py          # Core unit tests
    ├── test_watcher_live.py # Live folder monitoring integration tests
    └── test_gui.py          # GUI widget smoke tests
```

---

## 📜 License

MIT License.
