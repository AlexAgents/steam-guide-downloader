# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""
CLI test runner for local development.

Usage:
    python tests/run_tests.py

Note: In CI you typically run `pytest -q` directly.
"""

import sys
import os
import subprocess
import locale

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ════════════════════ CONFIGURATION ════════════════════

TEST_MODULES = {
    "1": ("URL Validator", "test_validator"),
    "2": ("Utilities", "test_utils"),
    "3": ("DOCX Builder", "test_docx_builder"),
    "4": ("Config", "test_config"),
    "5": ("Translations", "test_translations"),
    "6": ("Paths", "test_paths"),
    "7": ("Network / Cache", "test_network"),
    "a": ("ALL tests", None),
}

# ════════════════════ LOCALIZATION ════════════════════

LANG = "en"

STRINGS = {
    "en": {
        "title": "Steam Guide Downloader — Test Runner",
        "select": "Select test to run",
        "quit": "Quit",
        "running": "Running",
        "passed": "PASSED",
        "failed": "FAILED",
        "exit_code": "exit code",
        "invalid": "Invalid choice",
        "try_again": "Try again",
        "exiting": "Exiting",
        "all_tests": "ALL tests",
        "results": "Results",
        "total": "Total",
        "lang_prompt": "Language / Язык: [1] English  [2] Русский",
    },
    "ru": {
        "title": "Steam Guide Downloader — Запуск тестов",
        "select": "Выберите тест",
        "quit": "Выход",
        "running": "Запуск",
        "passed": "ПРОЙДЕН",
        "failed": "ОШИБКА",
        "exit_code": "код",
        "invalid": "Неверный выбор",
        "try_again": "Попробуйте снова",
        "exiting": "Выход",
        "all_tests": "ВСЕ тесты",
        "results": "Результаты",
        "total": "Всего",
        "lang_prompt": "Language / Язык: [1] English  [2] Русский",
    }
}


def t(key: str) -> str:
    return STRINGS.get(LANG, STRINGS["en"]).get(key, key)


def detect_language() -> str:
    try:
        loc = locale.getdefaultlocale()[0] or ""
        if loc.lower().startswith("ru"):
            return "ru"
    except Exception:
        pass
    return "en"


def prompt_language():
    global LANG
    print(f"\n🌐 {STRINGS['en']['lang_prompt']}")
    choice = input("   > ").strip()
    if choice == "2":
        LANG = "ru"
    else:
        LANG = "en"


# ════════════════════ RUNNER ════════════════════

def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_test(module_name: str | None) -> int:
    """Run test module(s) via pytest."""
    root = get_project_root()

    if module_name is None:
        # Run all
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/", "-v", "--tb=short",
            "-x",  # stop on first failure
        ]
    else:
        cmd = [
            sys.executable, "-m", "pytest",
            f"tests/{module_name}.py",
            "-v", "--tb=short",
        ]

    result = subprocess.run(cmd, cwd=root)
    return result.returncode


def run_all_individually() -> dict[str, bool]:
    """Run each module individually and collect results."""
    results = {}
    for key, (name, module) in TEST_MODULES.items():
        if key == "a":
            continue
        print(f"\n{'─' * 50}")
        print(f"  ▶ {t('running')}: {name}")
        print(f"{'─' * 50}")
        rc = run_test(module)
        results[name] = (rc == 0)
        if rc == 0:
            print(f"  ✅ {name}: {t('passed')}")
        else:
            print(f"  ❌ {name}: {t('failed')} ({t('exit_code')} {rc})")
    return results


def print_summary(results: dict[str, bool]):
    """Print test results summary."""
    print(f"\n{'═' * 50}")
    print(f"  📊 {t('results')}")
    print(f"{'═' * 50}")

    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        status = t("passed") if ok else t("failed")
        print(f"  {icon} {name}: {status}")

    print(f"{'─' * 50}")
    print(f"  {t('total')}: {len(results)} | "
          f"✅ {passed} | ❌ {failed}")

    if failed == 0:
        print(f"\n  🎉 {'All tests passed!' if LANG == 'en' else 'Все тесты пройдены!'}")
    else:
        print(f"\n  ⚠️  {failed} {'test(s) failed' if LANG == 'en' else 'тест(ов) провалено'}")
    print(f"{'═' * 50}")


# ════════════════════ MENU ════════════════════

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def main():
    prompt_language()

    while True:
        print(f"\n{'═' * 50}")
        print(f"  🧪 {t('title')}")
        print(f"{'═' * 50}")

        for key, (name, _) in TEST_MODULES.items():
            if key == "a":
                print(f"  [{key}] 🔬 {t('all_tests')}")
            else:
                print(f"  [{key}] {name}")

        print(f"  [q] 👋 {t('quit')}")
        print(f"{'─' * 50}")

        choice = input(f"  {t('select')}: ").strip().lower()

        if choice in ('q', 'й'):
            print(f"\n  👋 {t('exiting')}")
            break

        if choice == 'a':
            results = run_all_individually()
            print_summary(results)
            input(f"\n  ⏎ {'Press Enter...' if LANG == 'en' else 'Enter...'}")
            continue

        if choice in TEST_MODULES:
            name, module = TEST_MODULES[choice]
            print(f"\n  ▶ {t('running')}: {name}")
            print(f"{'─' * 40}")
            rc = run_test(module)
            if rc == 0:
                print(f"\n  ✅ {name}: {t('passed')}")
            else:
                print(f"\n  ❌ {name}: {t('failed')} ({t('exit_code')} {rc})")
            input(f"\n  ⏎ {'Press Enter...' if LANG == 'en' else 'Enter...'}")
        else:
            print(f"  ⚠️  {t('invalid')}: '{choice}'. {t('try_again')}.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  👋 {t('exiting')}")
        sys.exit(0)