# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""Application metadata"""

APP_NAME = "Steam Guide Downloader"
APP_VERSION = "2.2.0"
APP_AUTHOR = "AlexAgents"
APP_GITHUB = "https://github.com/AlexAgents/steam-guide-downloader"
APP_YEAR = "2025-2026"
APP_LICENSE = "MIT"

APP_DESCRIPTION_EN = "Download Steam Community guides as DOCX & PDF"
APP_DESCRIPTION_RU = "Скачивание руководств Steam в DOCX и PDF"


def get_about_text(lang: str) -> str:
    if lang == "ru":
        return _ABOUT_RU
    return _ABOUT_EN


_ABOUT_EN = f"""
<p style="text-align:center; font-size:14pt; font-weight:bold;
    margin-top:8px; margin-bottom:2px;">
    {APP_NAME}
</p>
<p style="text-align:center; font-size:9pt; margin-top:0;">
    {APP_DESCRIPTION_EN}
</p>
<p style="text-align:center; font-size:8pt; margin-top:12px;">
    {APP_LICENSE} &middot; &copy; {APP_YEAR} {APP_AUTHOR}
</p>
<p style="text-align:center; font-size:8pt; margin-top:10px;">
    <a href="{APP_GITHUB}">{APP_GITHUB}</a>
</p>
"""

_ABOUT_RU = f"""
<p style="text-align:center; font-size:14pt; font-weight:bold;
    margin-top:8px; margin-bottom:2px;">
    {APP_NAME}
</p>
<p style="text-align:center; font-size:9pt; margin-top:0;">
    {APP_DESCRIPTION_RU}
</p>
<p style="text-align:center; font-size:8pt; margin-top:12px;">
    {APP_LICENSE} &middot; &copy; {APP_YEAR} {APP_AUTHOR}
</p>
<p style="text-align:center; font-size:8pt; margin-top:10px;">
    <a href="{APP_GITHUB}">{APP_GITHUB}</a>
</p>
"""