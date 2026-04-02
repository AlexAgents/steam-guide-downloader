# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""
Project build script for Steam Guide Downloader EXE generation.
Automatically finds dependencies, generates icon, builds EXE and computes checksums.
Supports Russian and English languages.
"""

import os
import sys
import shutil
import subprocess
import hashlib
import time
import struct
import argparse
import re
import locale
from datetime import datetime
from typing import List, Optional, Dict

# ════════════════════ CONFIGURATION ════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
ICON_NAME = "icon.ico"
ICON_PATH = os.path.join(ASSETS_DIR, ICON_NAME)

sys.path.insert(0, PROJECT_ROOT)

try:
    from app.about import APP_NAME
    PROJECT_NAME = APP_NAME.replace(" ", "")
except ImportError:
    PROJECT_NAME = "SteamGuideDownloader"

EXE_EXT = ".exe" if sys.platform.startswith("win") else ""
EXE_NAME = f"{PROJECT_NAME}{EXE_EXT}"
EXE_PATH = os.path.join(DIST_DIR, EXE_NAME)

ICON_COLOR = (27, 40, 56)
ICON_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

PROJECT_PACKAGES = ["app", "app/core", "app/gui"]


def default_ui_mode() -> str:
    return "windowed" if sys.platform.startswith("win") else "console"


def resolve_ui_mode(args) -> str:
    if getattr(args, "console", False):
        return "console"
    if getattr(args, "windowed", False):
        return "windowed"
    if getattr(args, "debug", False):
        return "console"
    return default_ui_mode()


# ════════════════════ LOCALIZATION ════════════════════

CURRENT_LANG = "en"

LANG: Dict[str, Dict[str, str]] = {
    "ru": {
        "menu_title": "Сборщик проекта",
        "menu_root": "Корень",
        "menu_entry": "Вход",
        "menu_icon": "Иконка",
        "menu_exe": "EXE",
        "menu_choice": "Ваш выбор",
        "opt_build": "Собрать EXE",
        "opt_regen_icon": "Перегенерировать иконку",
        "opt_clean_build": "Очистить build/",
        "opt_clean_dist": "Очистить dist/",
        "opt_clean_all": "Очистить всё",
        "opt_checksums": "SHA-256 хеши",
        "opt_change_lang": "Change language / Сменить язык",
        "opt_exit": "Выход",
        "status_yes": "Есть",
        "status_no": "Нет",
        "status_not_built": "не собран",
        "status_not_found": "НЕ НАЙДЕН",
        "checking_pyinstaller": "Проверка PyInstaller...",
        "pyinstaller_found": "PyInstaller найден",
        "pyinstaller_not_found": "PyInstaller не найден!",
        "pyinstaller_install_prompt": "Установить через pip? (y/n)",
        "pyinstaller_installed": "PyInstaller установлен",
        "pyinstaller_install_failed": "Не удалось установить",
        "generating_icon": "Генерация иконки",
        "icon_created_pillow": "Иконка создана (Pillow)",
        "icon_created_fallback": "Иконка создана (Fallback)",
        "icon_create_failed": "Не удалось создать иконку",
        "cleaning_build": "Очистка build/...",
        "cleaning_dist": "Очистка dist/...",
        "temp_files_cleaned": "Временные файлы очищены",
        "dist_cleaned": "dist/ очищена",
        "clean_error": "Ошибка очистки",
        "starting_pyinstaller": "ЗАПУСК PYINSTALLER",
        "building": "Сборка",
        "entry_point": "Точка входа",
        "icon_label": "Иконка",
        "yes": "Да",
        "no": "Нет",
        "build_complete": "Сборка завершена за",
        "sec": "сек",
        "file_label": "Файл",
        "size_label": "Размер",
        "build_error": "Ошибка сборки!",
        "last_errors": "ОШИБКИ (STDERR)",
        "full_log": "Полный лог",
        "build_timeout": "Таймаут сборки (10 мин)",
        "critical_error": "Критическая ошибка",
        "entry_not_found": "__main__.py не найден!",
        "press_enter": "Enter для продолжения...",
        "goodbye": "До свидания!",
        "ready_files": "Готовые файлы",
        "invalid_choice": "Неверный выбор",
        "select_language": "Выберите язык / Select language",
        "lang_option_ru": "Русский",
        "lang_option_en": "English",
        "operation_cancelled": "Прервано",
        "scanning_imports": "Сканирование импортов...",
        "found_imports": "Найдено импортов",
        "checksum_title": "SHA-256",
        "checksum_saved": "Сохранено в",
        "checksum_no_files": "Нет файлов в dist/",
        "checksum_no_dist": "dist/ не найдена",
        "checksum_computing": "Вычисление хешей...",
        "checksum_github": "Для GitHub Release",
        "checksum_verify_ps": "Проверка (PowerShell)",
        "checksum_verify_bash": "Проверка (bash)",
    },
    "en": {
        "menu_title": "Project Builder",
        "menu_root": "Root",
        "menu_entry": "Entry",
        "menu_icon": "Icon",
        "menu_exe": "EXE",
        "menu_choice": "Your choice",
        "opt_build": "Build EXE",
        "opt_regen_icon": "Regenerate icon",
        "opt_clean_build": "Clean build/",
        "opt_clean_dist": "Clean dist/",
        "opt_clean_all": "Clean all",
        "opt_checksums": "SHA-256 checksums",
        "opt_change_lang": "Change language / Сменить язык",
        "opt_exit": "Exit",
        "status_yes": "Yes",
        "status_no": "No",
        "status_not_built": "not built",
        "status_not_found": "NOT FOUND",
        "checking_pyinstaller": "Checking PyInstaller...",
        "pyinstaller_found": "PyInstaller found",
        "pyinstaller_not_found": "PyInstaller not found!",
        "pyinstaller_install_prompt": "Install via pip? (y/n)",
        "pyinstaller_installed": "PyInstaller installed",
        "pyinstaller_install_failed": "Failed to install",
        "generating_icon": "Generating icon",
        "icon_created_pillow": "Icon created (Pillow)",
        "icon_created_fallback": "Icon created (Fallback)",
        "icon_create_failed": "Failed to create icon",
        "cleaning_build": "Cleaning build/...",
        "cleaning_dist": "Cleaning dist/...",
        "temp_files_cleaned": "Temp files cleaned",
        "dist_cleaned": "dist/ cleaned",
        "clean_error": "Clean error",
        "starting_pyinstaller": "STARTING PYINSTALLER",
        "building": "Building",
        "entry_point": "Entry point",
        "icon_label": "Icon",
        "yes": "Yes",
        "no": "No",
        "build_complete": "Build complete in",
        "sec": "sec",
        "file_label": "File",
        "size_label": "Size",
        "build_error": "Build error!",
        "last_errors": "ERRORS (STDERR)",
        "full_log": "Full log",
        "build_timeout": "Build timeout (10 min)",
        "critical_error": "Critical error",
        "entry_not_found": "__main__.py not found!",
        "press_enter": "Press Enter...",
        "goodbye": "Goodbye!",
        "ready_files": "Ready files",
        "invalid_choice": "Invalid choice",
        "select_language": "Выберите язык / Select language",
        "lang_option_ru": "Русский",
        "lang_option_en": "English",
        "operation_cancelled": "Cancelled",
        "scanning_imports": "Scanning imports...",
        "found_imports": "Hidden imports found",
        "checksum_title": "SHA-256",
        "checksum_saved": "Saved to",
        "checksum_no_files": "No files in dist/",
        "checksum_no_dist": "dist/ not found",
        "checksum_computing": "Computing checksums...",
        "checksum_github": "For GitHub Release",
        "checksum_verify_ps": "Verify (PowerShell)",
        "checksum_verify_bash": "Verify (bash)",
    }
}


def t(key: str) -> str:
    return LANG.get(CURRENT_LANG, LANG["en"]).get(key, key)


def detect_system_language() -> str:
    try:
        loc = locale.getdefaultlocale()[0] or ""
        if loc.lower().startswith("ru"):
            return "ru"
    except Exception:
        pass
    return "en"


def set_language(lang: str):
    global CURRENT_LANG
    if lang in LANG:
        CURRENT_LANG = lang


def prompt_language_selection():
    print(f"\n🌐 {t('select_language')}")
    print(f"   [1] {t('lang_option_ru')}")
    print(f"   [2] {t('lang_option_en')}")
    choice = input("   > ").strip()
    if choice == "1":
        set_language("ru")
    elif choice == "2":
        set_language("en")


# ════════════════════ UI HELPERS ════════════════════

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    print(f"\n{'═' * 60}\n   {text}\n{'═' * 60}")

def print_section(text):
    print(f"\n{'─' * 60}\n {text}\n{'─' * 60}")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_warn(text):
    print(f"⚠  {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def pause():
    input(f"\n⏎ {t('press_enter')}")

def get_file_info(path):
    if not os.path.exists(path):
        return t("status_not_built")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
    return f"{size_mb:.2f} MB | {mtime}"


# ════════════════════ CHECKSUM ════════════════════

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_checksums(show_github=True):
    if not os.path.exists(DIST_DIR):
        print_error(t("checksum_no_dist"))
        return False
    files = sorted(f for f in os.listdir(DIST_DIR)
                   if os.path.isfile(os.path.join(DIST_DIR, f))
                   and not f.endswith(".txt"))
    if not files:
        print_error(t("checksum_no_files"))
        return False

    print_info(t("checksum_computing"))
    print_section(t("checksum_title"))
    lines = []
    for fn in files:
        fp = os.path.join(DIST_DIR, fn)
        fh = sha256_file(fp)
        sz = os.path.getsize(fp) / (1024 * 1024)
        lines.append(f"{fh}  {fn}")
        print(f"\n  📦 {fn}\n  🔑 {fh}\n  📏 {sz:.1f} MB")

    cp = os.path.join(DIST_DIR, "checksums.txt")
    with open(cp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n{'─' * 60}")
    print_success(f"{t('checksum_saved')}: {cp}")

    if show_github:
        print(f"\n📋 {t('checksum_github')}:\n```text")
        for l in lines:
            print(l)
        print("```")
    return True


# ════════════════════ BUILD ════════════════════

def find_entry_point():
    for c in ["__main__.py"]:
        p = os.path.join(PROJECT_ROOT, c)
        if os.path.exists(p):
            return p
    return None


def check_pyinstaller():
    print_info(t("checking_pyinstaller"))
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                       capture_output=True, check=True)
        print_success(t("pyinstaller_found"))
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warn(t("pyinstaller_not_found"))
        choice = input(f"   {t('pyinstaller_install_prompt')}: ").strip().lower()
        if choice in ('y', 'д', 'yes', 'да'):
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"],
                               check=True)
                print_success(t("pyinstaller_installed"))
                return True
            except subprocess.CalledProcessError:
                print_error(t("pyinstaller_install_failed"))
        return False


def generate_icon_pillow(path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False
    try:
        img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([10, 10, 246, 246], radius=40, fill=ICON_COLOR)
        try:
            font = ImageFont.truetype("arial.ttf", 140)
        except IOError:
            font = ImageFont.load_default()
        draw.text((128, 128), "⬇", font=font, fill=(164, 208, 7), anchor="mm")
        img.save(path, format='ICO', sizes=ICON_SIZES)
        return True
    except Exception as e:
        print_warn(f"Pillow error: {e}")
        return False


def generate_icon_fallback(path):
    header = struct.pack('<HHH', 0, 1, 1)
    w, h = 32, 32
    bhs = 40
    pds = w * h * 4
    entry = struct.pack('<BBBBHHII', w, h, 0, 0, 1, 32, bhs + pds, 22)
    bmp = struct.pack('<IIIHHIIIIII', bhs, w, h * 2, 1, 32, 0, pds, 0, 0, 0, 0)
    px = struct.pack('BBBB', 56, 40, 27, 255) * (w * h)
    try:
        with open(path, 'wb') as f:
            f.write(header + entry + bmp + px)
        return True
    except Exception:
        return False


def ensure_assets():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    if os.path.exists(ICON_PATH) and os.path.getsize(ICON_PATH) > 0:
        return
    print_info(f"{t('generating_icon')} {ICON_NAME}...")
    if generate_icon_pillow(ICON_PATH):
        print_success(t("icon_created_pillow"))
    elif generate_icon_fallback(ICON_PATH):
        print_success(t("icon_created_fallback"))
    else:
        print_error(t("icon_create_failed"))


def scan_hidden_imports():
    print_info(t("scanning_imports"))
    imports = set()
    imports.update([
        "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui",
        "bs4", "docx", "PIL", "requests", "lxml",
    ])
    stdlib_skip = {
        'os', 'sys', 're', 'time', 'json', 'math', 'hashlib',
        'logging', 'traceback', 'subprocess', 'shutil', 'tempfile',
        'struct', 'argparse', 'locale', 'datetime', 'enum',
        'dataclasses', 'typing', '__future__', 'io', 'threading',
        'functools', 'urllib', 'pathlib',
        'app', 'themes',
    }
    py_files = []
    for pkg in [""] + PROJECT_PACKAGES:
        d = os.path.join(PROJECT_ROOT, pkg) if pkg else PROJECT_ROOT
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".py"):
                    py_files.append(os.path.join(d, f))
    for fp in py_files:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                for m in re.findall(r'^(?:from|import)\s+([\w.]+)', f.read(), re.MULTILINE):
                    top = m.split('.')[0]
                    if top not in stdlib_skip:
                        imports.add(m)
        except Exception:
            pass
    result = sorted(imports)
    print_info(f"   {t('found_imports')}: {len(result)}")
    return result


def clean_build_dir():
    print_info(t("cleaning_build"))
    try:
        if os.path.exists(BUILD_DIR):
            shutil.rmtree(BUILD_DIR)
        for f in os.listdir(PROJECT_ROOT):
            if f.endswith(".spec"):
                os.remove(os.path.join(PROJECT_ROOT, f))
        for root, dirs, _ in os.walk(PROJECT_ROOT):
            for d in dirs:
                if d in ("__pycache__", ".pytest_cache"):
                    shutil.rmtree(os.path.join(root, d), ignore_errors=True)
        print_success(t("temp_files_cleaned"))
    except Exception as e:
        print_error(f"{t('clean_error')}: {e}")


def clean_dist_dir():
    print_info(t("cleaning_dist"))
    try:
        if os.path.exists(DIST_DIR):
            shutil.rmtree(DIST_DIR)
        print_success(t("dist_cleaned"))
    except Exception as e:
        print_error(f"{t('clean_error')}: {e}")


def build_exe(args=None):
    entry = find_entry_point()
    if not entry:
        print_error(t("entry_not_found"))
        return False
    if not check_pyinstaller():
        return False
    ensure_assets()

    if args is None:
        class _A:
            debug = False
            console = False
            windowed = False
        args = _A()

    ui_mode = resolve_ui_mode(args)
    sep = ";" if sys.platform.startswith("win") else ":"
    hidden = scan_hidden_imports()
    hidden_args = []
    for imp in hidden:
        hidden_args.extend(["--hidden-import", imp])

    add_data = [
        f"{ASSETS_DIR}{sep}assets",
        f"{os.path.join(PROJECT_ROOT, 'themes')}{sep}themes",
    ]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onefile", "--clean",
        "--name", PROJECT_NAME,
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        "--specpath", BUILD_DIR,
        "--paths", PROJECT_ROOT,
    ]
    cmd.append("--windowed" if ui_mode == "windowed" else "--console")
    if getattr(args, "debug", False):
        cmd += ["--log-level", "DEBUG"]
    if os.path.exists(ICON_PATH):
        cmd.extend(["--icon", ICON_PATH])
    cmd.extend(hidden_args)
    for data in add_data:
        cmd.extend(["--add-data", data])
    cmd.append(entry)

    print_section(t("starting_pyinstaller"))
    print(f"🔨 {t('building')}: {PROJECT_NAME}")
    print(f"📂 {t('entry_point')}: {os.path.basename(entry)}")
    print(f"🖼️  {t('icon_label')}: {t('yes') if os.path.exists(ICON_PATH) else t('no')}")
    print(f"🧰 UI: {ui_mode}")
    print(f"📦 Imports: {len(hidden)}")

    os.makedirs(BUILD_DIR, exist_ok=True)
    log_file = os.path.join(BUILD_DIR, "build.log")
    start = time.time()

    try:
        with open(log_file, "w", encoding="utf-8") as log:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=600)
            log.write(proc.stdout + "\n=== STDERR ===\n" + proc.stderr)

        if proc.returncode == 0:
            elapsed = time.time() - start
            print_success(f"{t('build_complete')} {elapsed:.1f} {t('sec')}!")
            print(f"📂 {t('file_label')}: {EXE_PATH}")
            if os.path.exists(EXE_PATH):
                print(f"📦 {t('size_label')}: {os.path.getsize(EXE_PATH) / 1024 / 1024:.2f} MB")
            print()
            compute_checksums(show_github=True)
            return True

        print_error(t("build_error"))
        print_section(t("last_errors"))
        for line in proc.stderr.splitlines()[-20:]:
            print(f"  {line}")
        print_info(f"{t('full_log')}: {log_file}")
        return False
    except subprocess.TimeoutExpired:
        print_error(t("build_timeout"))
        return False
    except Exception as e:
        print_error(f"{t('critical_error')}: {e}")
        return False


# ════════════════════ MENU ════════════════════

def interactive_menu():
    while True:
        clear_screen()
        entry = find_entry_point()
        entry_name = os.path.basename(entry) if entry else f"{t('status_not_found')} ❌"
        icon_st = f"✅ {t('status_yes')}" if os.path.exists(ICON_PATH) else f"❌ {t('status_no')}"
        exe_info = get_file_info(EXE_PATH)
        li = "🇷🇺 RU" if CURRENT_LANG == "ru" else "🇬🇧 EN"

        print_header(f"{t('menu_title')}: {PROJECT_NAME} [{li}]")
        print(f" 📂 {t('menu_root')}: {PROJECT_ROOT}")
        print(f" 🐍 {t('menu_entry')}: {entry_name}")
        print(f" 🖼️  {t('menu_icon')}: {icon_st}")
        print(f" 📦 {t('menu_exe')}: {exe_info}")
        print("-" * 60)
        print(f" 1. 🔨 {t('opt_build')}")
        print(f" 2. 🖼️  {t('opt_regen_icon')}")
        print(f" 3. 🔑 {t('opt_checksums')}")
        print(f" 4. 🧹 {t('opt_clean_build')}")
        print(f" 5. 🧹 {t('opt_clean_dist')}")
        print(f" 6. 🗑  {t('opt_clean_all')}")
        print(f" 7. 🌐 {t('opt_change_lang')}")
        print(f" q. 👋 {t('opt_exit')}")
        print("-" * 60)
        ch = input(f" {t('menu_choice')}: ").strip().lower()

        if ch == '1':
            build_exe()
            pause()
        elif ch == '2':
            if os.path.exists(ICON_PATH):
                os.remove(ICON_PATH)
            ensure_assets()
            pause()
        elif ch == '3':
            compute_checksums()
            pause()
        elif ch == '4':
            clean_build_dir()
            pause()
        elif ch == '5':
            clean_dist_dir()
            pause()
        elif ch == '6':
            clean_build_dir()
            clean_dist_dir()
            pause()
        elif ch == '7':
            prompt_language_selection()
        elif ch in ('q', 'й'):
            print(f"\n👋 {t('goodbye')}")
            if os.path.exists(DIST_DIR) and os.listdir(DIST_DIR):
                print(f"📂 {t('ready_files')}: {DIST_DIR}")
            break
        else:
            print_warn(t("invalid_choice"))
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(
        description=f"{PROJECT_NAME} Builder"
    )
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--clean-all", action="store_true")
    parser.add_argument("--checksums", action="store_true")
    parser.add_argument("--lang", choices=["ru", "en"])
    parser.add_argument("--debug", action="store_true")
    ui = parser.add_mutually_exclusive_group()
    ui.add_argument("--console", action="store_true")
    ui.add_argument("--windowed", action="store_true")
    args = parser.parse_args()

    set_language(args.lang if args.lang else detect_system_language())
    os.makedirs(ASSETS_DIR, exist_ok=True)

    if args.build:
        build_exe(args)
    elif args.clean:
        clean_build_dir()
    elif args.clean_all:
        clean_build_dir()
        clean_dist_dir()
    elif args.checksums:
        compute_checksums()
    else:
        prompt_language_selection()
        interactive_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n👋 {t('operation_cancelled')}")
        sys.exit(0)