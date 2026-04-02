# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""UI translations"""

TRANSLATIONS = {
    "en": {
        "window_title": "Steam Guide Downloader",
        "lbl_url": "🔗  Steam Guide URL",
        "lbl_save_settings": "💾  Save Settings",
        "url_placeholder": "Paste or drag & drop Steam guide URL here…",
        "url_valid": "Valid Steam guide URL",
        "btn_browse": "📂 Browse",
        "btn_open_dir": "📁 Open folder",
        "btn_download": "⬇  Download DOCX",
        "btn_downloading": "⏳ Downloading…",
        "btn_cancel": "Cancel",
        "btn_clear_log": "🗑 Clear",
        "chk_pdf": "Convert to PDF",
        "chk_save_images": "Save images separately",
        "lbl_log": "📋  Log",
        "lbl_theme": "Theme:",
        "lbl_lang": "Lang:",
        "menu_about": "ℹ About",
        "dlg_select_save_folder": "Select save folder",
        "err_no_url": "Please enter a Steam guide URL.",
        "err_bad_url": (
            "This is not a valid Steam guide URL.\n\n"
            "Expected format:\n"
            "https://steamcommunity.com/sharedfiles/filedetails/?id=XXXXXX"
        ),
        "err_bad_path": (
            "Invalid save path.\n"
            "The folder does not exist and cannot be created."
        ),
        "err_path_not_writable": "Save folder is not writable.",
        "err_folder_not_exists": "Folder does not exist yet.",
        "err_net_connection": "⚠ No internet connection or Steam is unavailable.",
        "err_net_timeout": "⚠ Connection timed out.",
        "err_access": "🔒 Access error (HTTP {}). The guide may be private.",
        "err_content": "Guide content was not found on the page.",
        "err_permission": "🔒 File is locked. Close Word and try again.",
        "err_creating_dir": "Error creating folder:",
        "err_pdf_failed": "PDF conversion failed:",
        "err_pdf_no_support": (
            "PDF conversion requires LibreOffice or MS Word."
        ),
        "err_net": "Network error:",
        "err_already_downloading": (
            "Download is already in progress. Please wait or cancel first."
        ),
        "err_page_too_large": (
            "The guide page is very large ({} MB).\n"
            "This may use a lot of memory.\n\n"
            "Continue anyway?"
        ),
        "log_start": "🌐 Connecting to: {}…",
        "log_success": "\n✅ Done! File saved:\n{}",
        "log_pdf_success": "  📄 PDF saved: {}",
        "log_pdf_converting": "🔄 Converting to PDF…",
        "log_cancelled": "⛔ Download cancelled.",
        "log_cancelled_partial": "⛔ Cancelled. Partial file saved:\n{}",
        "log_sections_found": "📑 Found {} sections",
        "log_processing": "⚙ Processing: {}",
        "log_file_target": "📁 Target: {}",
        "log_protocol_changed": "ℹ Note: URL protocol changed to HTTPS",
        "log_images_saved": "🖼 Images saved to: {}",
        "log_image_saved": "  ✔ Saved: {}",
        "log_images_total": "  🖼 Total images saved: {}",
        "msg_error": "Error",
        "msg_warning": "Warning",
        "msg_validation_title": "Validation",
        "msg_confirm": "Confirm",
        "ctx_paste": "📋 Paste",
        "ctx_clear": "🗑 Clear",
        "ctx_copy_all": "📋 Copy log",
        "status_ready": "✔ Ready",
        "status_downloading": "⬇ Downloading…",
        "status_done": "✅ Done",
        "status_log_cleared": "🗑 Log cleared & saved",
        "status_log_empty": "🗑 Log is already empty",
    },
    "ru": {
        "window_title": "Загрузчик руководств Steam",
        "lbl_url": "🔗  Ссылка на руководство Steam",
        "lbl_save_settings": "💾  Настройки сохранения",
        "url_placeholder": "Вставьте или перетащите ссылку на руководство…",
        "url_valid": "Корректная ссылка на руководство",
        "btn_browse": "📂 Обзор",
        "btn_open_dir": "📁 Открыть папку",
        "btn_download": "⬇  Скачать DOCX",
        "btn_downloading": "⏳ Скачивание…",
        "btn_cancel": "Отмена",
        "btn_clear_log": "🗑 Очистить",
        "chk_pdf": "Конвертировать в PDF",
        "chk_save_images": "Сохранить картинки отдельно",
        "lbl_log": "📋  Лог",
        "lbl_theme": "Тема:",
        "lbl_lang": "Язык:",
        "menu_about": "ℹ О программе",
        "dlg_select_save_folder": "Выбор папки сохранения",
        "err_no_url": "Введите ссылку на руководство Steam.",
        "err_bad_url": (
            "Это не ссылка на руководство Steam.\n\n"
            "Ожидаемый формат:\n"
            "https://steamcommunity.com/sharedfiles/filedetails/?id=XXXXXX"
        ),
        "err_bad_path": (
            "Неверный путь сохранения.\n"
            "Папка не существует и не может быть создана."
        ),
        "err_path_not_writable": "Папка сохранения недоступна для записи.",
        "err_folder_not_exists": "Папка ещё не существует.",
        "err_net_connection": "⚠ Нет интернета или Steam недоступен.",
        "err_net_timeout": "⚠ Время ожидания истекло.",
        "err_access": (
            "🔒 Ошибка доступа (HTTP {}). Руководство может быть приватным."
        ),
        "err_content": "Контент руководства не найден на странице.",
        "err_permission": "🔒 Файл занят. Закройте Word и попробуйте снова.",
        "err_creating_dir": "Ошибка создания папки:",
        "err_pdf_failed": "Ошибка конвертации в PDF:",
        "err_pdf_no_support": (
            "Для конвертации в PDF необходим LibreOffice или MS Word."
        ),
        "err_net": "Ошибка сети:",
        "err_already_downloading": (
            "Загрузка уже выполняется. Подождите или отмените текущую."
        ),
        "err_page_too_large": (
            "Страница руководства очень большая ({} МБ).\n"
            "Это может занять много памяти.\n\n"
            "Продолжить?"
        ),
        "log_start": "🌐 Подключение к: {}…",
        "log_success": "\n✅ Готово! Файл сохранён:\n{}",
        "log_pdf_success": "  📄 PDF сохранён: {}",
        "log_pdf_converting": "🔄 Конвертация в PDF…",
        "log_cancelled": "⛔ Загрузка отменена.",
        "log_cancelled_partial": "⛔ Отменено. Частичный файл сохранён:\n{}",
        "log_sections_found": "📑 Найдено секций: {}",
        "log_processing": "⚙ Обработка: {}",
        "log_file_target": "📁 Целевой файл: {}",
        "log_protocol_changed": "ℹ Примечание: протокол URL изменён на HTTPS",
        "log_images_saved": "🖼 Картинки сохранены в: {}",
        "log_image_saved": "  ✔ Сохранено: {}",
        "log_images_total": "  🖼 Всего сохранено картинок: {}",
        "msg_error": "Ошибка",
        "msg_warning": "Внимание",
        "msg_validation_title": "Проверка",
        "msg_confirm": "Подтверждение",
        "ctx_paste": "📋 Вставить",
        "ctx_clear": "🗑 Очистить",
        "ctx_copy_all": "📋 Копировать лог",
        "status_ready": "✔ Готово",
        "status_downloading": "⬇ Скачивание…",
        "status_done": "✅ Завершено",
        "status_log_cleared": "🗑 Лог очищен и сохранён",
        "status_log_empty": "🗑 Лог уже пуст",
    }
}


def get_text(lang_code: str, key: str, *args) -> str:
    """Get translated text by key with optional format arguments."""
    lang_dict = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
    template = lang_dict.get(key, key)
    if args:
        try:
            return template.format(*args)
        except (IndexError, KeyError):
            return template
    return template