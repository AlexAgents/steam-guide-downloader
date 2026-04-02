# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""App icon provider — file or generated"""
import os
import sys
import logging

from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QFont,
    QPen, QBrush, QLinearGradient, QPolygonF
)
from PyQt6.QtCore import Qt, QRect, QPointF

from app.paths import get_assets_dir

logger = logging.getLogger(__name__)


def get_icon() -> QIcon:
    icon = _load_from_file()
    if icon and not icon.isNull():
        return icon
    return _generate_builtin_icon()


def _load_from_file() -> QIcon | None:
    assets_dir = get_assets_dir()
    for name in ("icon.ico", "icon.png", "icon.svg"):
        path = os.path.join(assets_dir, name)
        if os.path.isfile(path):
            try:
                icon = QIcon(path)
                if not icon.isNull():
                    return icon
            except Exception as e:
                logger.warning(f"Icon error {path}: {e}")
    return None


def _generate_builtin_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(_draw_icon(size))
    return icon


def _draw_icon(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    s = size
    margin = max(1, s // 16)

    bg_rect = QRect(margin, margin, s - 2 * margin, s - 2 * margin)
    radius = max(2, s // 6)

    bg = QLinearGradient(0, 0, 0, s)
    bg.setColorAt(0.0, QColor(27, 40, 56))
    bg.setColorAt(1.0, QColor(15, 25, 40))

    painter.setPen(QPen(QColor(42, 71, 94), max(1, s // 32)))
    painter.setBrush(QBrush(bg))
    painter.drawRoundedRect(bg_rect, radius, radius)

    cx, cy = s / 2, s / 2
    arrow_w = s * 0.35
    arrow_h = s * 0.22
    shaft_w = s * 0.14
    shaft_h = s * 0.18
    bar_w = s * 0.45
    bar_h = max(2, s * 0.07)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(164, 208, 7)))

    shaft_x = cx - shaft_w / 2
    shaft_y = cy - shaft_h - arrow_h * 0.3
    painter.drawRect(QRect(
        int(shaft_x), int(shaft_y), int(shaft_w), int(shaft_h)
    ))

    tip_y = shaft_y + shaft_h + arrow_h
    painter.drawPolygon(QPolygonF([
        QPointF(cx - arrow_w, shaft_y + shaft_h),
        QPointF(cx + arrow_w, shaft_y + shaft_h),
        QPointF(cx, tip_y),
    ]))

    bar_y = tip_y + s * 0.06
    painter.setBrush(QBrush(QColor(102, 192, 244)))
    painter.drawRoundedRect(QRect(
        int(cx - bar_w / 2), int(bar_y), int(bar_w), int(bar_h)
    ), max(1, s // 32), max(1, s // 32))

    if s >= 48:
        fs = max(6, s // 6)
        font = QFont("Arial", fs, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(200, 200, 220, 120)))
        painter.drawText(
            QRect(s - margin - fs - 2, margin + 1, fs + 4, fs + 4),
            Qt.AlignmentFlag.AlignCenter, "S"
        )

    painter.end()
    return pixmap


def setup_app_icon(app, window):
    icon = get_icon()
    window.setWindowIcon(icon)
    app.setWindowIcon(icon)
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "alexagents.steamguidedownloader.app.v2"
            )
        except Exception:
            pass