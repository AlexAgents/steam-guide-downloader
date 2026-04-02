# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""
Main Window — modern card-based UI with light/dark themes
"""

import os
import sys
import logging
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QCheckBox, QProgressBar, QFileDialog, QFrame,
    QMessageBox, QMenu, QApplication, QSizePolicy,
    QSpacerItem, QStatusBar, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QObject, QUrl, QSettings, QTimer
)
from PyQt6.QtGui import (
    QShortcut, QKeySequence, QDesktopServices, QFont,
    QPalette, QColor, QPixmap, QPainter, QPen, QBrush
)

from app.about import get_about_text, APP_NAME, APP_VERSION
from app.config import AppConfig
from app.translations import get_text
from app.core.network import URLValidator
from app.core.parser import GuideDownloader
from app.utils import validate_save_path
from app.paths import get_session_logs_dir, get_assets_dir
from app.gui.icon_provider import get_icon
from themes import load_theme

logger = logging.getLogger(__name__)

# ── Layout constants ──
MIN_WIDTH = 700
MIN_HEIGHT = 600
DEFAULT_WIDTH = 700
DEFAULT_HEIGHT = 600
CONTENT_MARGINS = (14, 10, 14, 6)
SECTION_SPACING = 8
INPUT_HEIGHT = 32
COMBO_HEIGHT = 26
BTN_HEIGHT = 28
BTN_DOWNLOAD_HEIGHT = 40
STATUS_TIMEOUT_MS = 8000

THEMES = ["light", "dark"]

# ── Theme palettes (qBittorrent-inspired) ──
_PALETTES = {
    "light": {
        "window": "#f5f6fa", "base": "#ffffff", "text": "#2d3436",
        "button": "#f0f2f5", "highlight": "#0984e3",
        "tooltip_bg": "#2d3436", "tooltip_fg": "#dfe6e9",
        "chk_bg": "#ffffff", "chk_border": "#b2bec3",
        "chk_fill": "#0984e3",
    },
    "dark": {
        "window": "#1e1e2e", "base": "#313244", "text": "#cdd6f4",
        "button": "#313244", "highlight": "#89b4fa",
        "tooltip_bg": "#313244", "tooltip_fg": "#cdd6f4",
        "chk_bg": "#313244", "chk_border": "#585b70",
        "chk_fill": "#89b4fa",
    },
}

# ── Checkbox PNG generation ──

def _generate_checkbox_pixmaps(theme: str) -> dict[str, QPixmap]:
    c = _PALETTES.get(theme, _PALETTES["dark"])
    sz = 18
    result = {}

    # Unchecked
    pm = QPixmap(sz, sz)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    border = QColor(c["chk_border"])
    p.setPen(QPen(border, 1.5))
    p.setBrush(QBrush(QColor(c["chk_bg"])))
    p.drawRoundedRect(1, 1, sz - 2, sz - 2, 3, 3)
    p.end()
    result["unchecked"] = pm

    # Checked
    pm2 = QPixmap(sz, sz)
    pm2.fill(Qt.GlobalColor.transparent)
    p2 = QPainter(pm2)
    p2.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    fill = QColor(c["chk_fill"])
    p2.setPen(QPen(fill.darker(115), 1.5))
    p2.setBrush(QBrush(fill))
    p2.drawRoundedRect(1, 1, sz - 2, sz - 2, 3, 3)
    pen = QPen(QColor("#ffffff"), 2.0, Qt.PenStyle.SolidLine,
              Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p2.setPen(pen)
    p2.setBrush(Qt.BrushStyle.NoBrush)
    p2.drawLine(5, 9, 7, 13)
    p2.drawLine(7, 13, 13, 5)
    p2.end()
    result["checked"] = pm2

    return result


def _save_checkbox_assets(theme: str):
    assets = get_assets_dir()
    os.makedirs(assets, exist_ok=True)
    unc = os.path.join(assets, f"chk_off_{theme}.png")
    chk = os.path.join(assets, f"chk_on_{theme}.png")

    if not (os.path.isfile(unc) and os.path.isfile(chk)):
        pix = _generate_checkbox_pixmaps(theme)
        pix["unchecked"].save(unc, "PNG")
        pix["checked"].save(chk, "PNG")

    return unc, chk


def _checkbox_qss(theme: str) -> str:
    unc, chk = _save_checkbox_assets(theme)
    u = unc.replace("\\", "/")
    c = chk.replace("\\", "/")
    return (
        "QCheckBox::indicator {"
        "  width: 18px; height: 18px;"
        "  border: none; background: transparent;"
        "  margin: 0px; padding: 0px;"
        "}"
        "QCheckBox::indicator:unchecked { image: url(" + u + "); }"
        "QCheckBox::indicator:checked   { image: url(" + c + "); }"
        "QCheckBox::indicator:unchecked:hover { image: url(" + u + "); }"
        "QCheckBox::indicator:checked:hover   { image: url(" + c + "); }"
    )


# ── Helper widgets ──

class LogSignal(QObject):
    message = pyqtSignal(str)
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)
    page_size_warning = pyqtSignal(float)


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 10, 12, 10)
        self._layout.setSpacing(6)

    def inner_layout(self):
        return self._layout


class LogSessionManager:
    def __init__(self):
        self._dir = get_session_logs_dir()
        self._lines: list[str] = []
        self._active = False
        self._session_date = ""

    def start_session(self):
        now = datetime.now()
        self._session_date = now.strftime("%Y-%m-%d")
        self._lines = [f"=== Session: {now:%Y-%m-%d %H:%M:%S} ==="]
        self._active = True

    def add_line(self, text):
        if self._active:
            self._lines.append(text)

    def _get_session_dir(self) -> str:
        d = os.path.join(
            self._dir,
            self._session_date or datetime.now().strftime("%Y-%m-%d")
        )
        os.makedirs(d, exist_ok=True)
        return d

    def save_session(self):
        if not self._active or not self._lines:
            return
        self._lines.append(
            f"=== End: {datetime.now():%Y-%m-%d %H:%M:%S} ===\n"
        )
        p = os.path.join(
            self._get_session_dir(),
            f"session_{datetime.now():%H%M%S}.log"
        )
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(self._lines))
        except OSError:
            pass
        self._active = False
        self._lines = []

    def save_on_clear(self, text):
        if not text.strip():
            return
        p = os.path.join(
            self._get_session_dir(),
            f"cleared_{datetime.now():%H%M%S}.log"
        )
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError:
            pass


class AboutDialog(QDialog):
    def __init__(self, html, app_pixmap, lang, parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            "О программе" if lang == "ru" else "About"
        )
        self.setFixedSize(380, 300)
        self.setObjectName("about_dialog")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(0)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setPixmap(app_pixmap.scaled(
            56, 56,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        icon_lbl.setObjectName("about_icon")
        lay.addWidget(icon_lbl)
        lay.addSpacing(6)

        text_lbl = QLabel(html)
        text_lbl.setWordWrap(True)
        text_lbl.setOpenExternalLinks(True)
        text_lbl.setObjectName("about_text")
        text_lbl.setTextFormat(Qt.TextFormat.RichText)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(text_lbl)
        lay.addSpacing(16)

        btn = QPushButton(
            "Закрыть" if lang == "ru" else "Close"
        )
        btn.setObjectName("about_close_btn")
        btn.setFixedWidth(100)
        btn.clicked.connect(self.accept)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)


def _show_warning(parent, title, text):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle(title)
    msg.setText(
        '<div style="text-align: center;">'
        + text.replace("\n", "<br>")
        + '</div>'
    )
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    button_box = msg.findChild(QDialogButtonBox)
    if button_box:
        button_box.setCenterButtons(True)
    msg.exec()


def _show_confirm(parent, title, text) -> bool:
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setWindowTitle(title)
    msg.setText(
        '<div style="text-align: center;">'
        + text.replace("\n", "<br>")
        + '</div>'
    )
    msg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    msg.setDefaultButton(QMessageBox.StandardButton.No)
    button_box = msg.findChild(QDialogButtonBox)
    if button_box:
        button_box.setCenterButtons(True)
    return msg.exec() == QMessageBox.StandardButton.Yes


# ══════════════════════════════════════════════
#  Main Window
# ══════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = AppConfig.load()
        self.downloader = None
        self._download_thread = None
        self._download_lock = threading.Lock()
        self.log_manager = LogSessionManager()
        self._current_theme = self.config.theme

        self.log_signal = LogSignal()
        self.log_signal.message.connect(self._append_log)
        self.log_signal.finished.connect(self._on_download_finished)
        self.log_signal.progress.connect(self._on_progress)
        self.log_signal.page_size_warning.connect(
            self._on_page_size_warning
        )

        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._clear_status)

        self.setAcceptDrops(True)
        self._build_ui()
        self._connect_signals()
        self._update_texts()
        self._apply_theme(self.config.theme)
        self._setup_paste_shortcuts()
        self._restore_geometry()
        # Deferred PDF check — don't block startup
        QTimer.singleShot(100, self._check_pdf_availability)

    # ── Build UI ──
    def _build_ui(self):
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.setMenuBar(None)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(*CONTENT_MARGINS)
        root.setSpacing(SECTION_SPACING)

        # Top bar
        root.addLayout(self._build_top_bar())
        # URL card
        root.addWidget(self._build_url_card())
        # Save Settings card
        root.addWidget(self._build_save_card())
        # Action row: Download + Cancel
        root.addLayout(self._build_action_row())
        # Log card (stretches)
        root.addWidget(self._build_log_card(), stretch=1)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setObjectName("main_progress")
        root.addWidget(self.progress)

        # Status bar
        sb = QStatusBar()
        sb.setFixedHeight(22)
        sb.setObjectName("main_status_bar")
        self.setStatusBar(sb)

    def _build_top_bar(self):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 2)
        h.setSpacing(6)

        self.lbl_theme = QLabel()
        self.lbl_theme.setObjectName("toolbar_label")
        h.addWidget(self.lbl_theme)

        self.combo_theme = QComboBox()
        self.combo_theme.setFixedHeight(COMBO_HEIGHT)
        self.combo_theme.setFixedWidth(110)
        self.combo_theme.setObjectName("toolbar_combo")
        self.combo_theme.addItems(["☀ Light", "🌙 Dark"])
        if self.config.theme in THEMES:
            self.combo_theme.setCurrentIndex(
                THEMES.index(self.config.theme)
            )
        h.addWidget(self.combo_theme)

        h.addSpacerItem(QSpacerItem(10, 0))

        self.lbl_lang = QLabel()
        self.lbl_lang.setObjectName("toolbar_label")
        h.addWidget(self.lbl_lang)

        self.combo_lang = QComboBox()
        self.combo_lang.setFixedHeight(COMBO_HEIGHT)
        self.combo_lang.setFixedWidth(105)
        self.combo_lang.setObjectName("toolbar_combo")
        self.combo_lang.addItems(["🇺🇸 English", "🇷🇺 Русский"])
        self.combo_lang.setCurrentIndex(
            0 if self.config.language == "en" else 1
        )
        h.addWidget(self.combo_lang)

        h.addStretch()

        # About button
        self.btn_about = QPushButton("ℹ")
        self.btn_about.setFixedSize(COMBO_HEIGHT, COMBO_HEIGHT)
        self.btn_about.setObjectName("btn_about")
        self.btn_about.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_about.clicked.connect(self._show_about)
        f_about = QFont("Segoe UI", 12)
        self.btn_about.setFont(f_about)
        h.addWidget(self.btn_about)

        return h

    def _build_url_card(self):
        card = Card()
        lay = card.inner_layout()

        self.lbl_url = QLabel()
        self.lbl_url.setObjectName("section_label")
        lay.addWidget(self.lbl_url)

        self.url_input = QLineEdit()
        self.url_input.setFixedHeight(INPUT_HEIGHT)
        self.url_input.setClearButtonEnabled(True)
        self.url_input.setObjectName("url_input")
        self.url_input.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        lay.addWidget(self.url_input)

        self.url_hint = QLabel()
        self.url_hint.setObjectName("hint_label")
        self.url_hint.setVisible(False)
        lay.addWidget(self.url_hint)

        return card

    def _build_save_card(self):
        card = Card()
        lay = card.inner_layout()

        self.lbl_save_settings = QLabel()
        self.lbl_save_settings.setObjectName("section_label")
        lay.addWidget(self.lbl_save_settings)

        # Path row: input + Browse
        path_row = QHBoxLayout()
        path_row.setSpacing(6)

        self.path_input = QLineEdit()
        self.path_input.setFixedHeight(INPUT_HEIGHT)
        self.path_input.setText(self.config.save_dir)
        self.path_input.setObjectName("path_input")
        self.path_input.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        path_row.addWidget(self.path_input)

        self.btn_browse = QPushButton()
        self.btn_browse.setFixedHeight(INPUT_HEIGHT)
        self.btn_browse.setFixedWidth(110)
        self.btn_browse.setObjectName("btn_browse")
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        path_row.addWidget(self.btn_browse)

        lay.addLayout(path_row)

        # Options row: checkboxes side by side
        opts = QHBoxLayout()
        opts.setContentsMargins(0, 4, 0, 0)
        opts.setSpacing(6)

        self.chk_pdf = QCheckBox()
        self.chk_pdf.setChecked(self.config.convert_to_pdf)
        self.chk_pdf.setObjectName("chk_pdf")
        opts.addWidget(self.chk_pdf)

        self.pdf_status_label = QLabel("")
        self.pdf_status_label.setObjectName("pdf_status")
        opts.addWidget(self.pdf_status_label)

        opts.addSpacing(16)

        self.chk_save_images = QCheckBox()
        self.chk_save_images.setChecked(self.config.save_images)
        self.chk_save_images.setObjectName("chk_save_images")
        opts.addWidget(self.chk_save_images)

        opts.addStretch()
        lay.addLayout(opts)

        self.path_error_label = QLabel("")
        self.path_error_label.setObjectName("error_label")
        self.path_error_label.setVisible(False)
        lay.addWidget(self.path_error_label)

        return card

    def _build_action_row(self):
        h = QHBoxLayout()
        h.setSpacing(8)
        h.setContentsMargins(0, 4, 0, 0)

        self.btn_download = QPushButton()
        self.btn_download.setObjectName("btn_download")
        self.btn_download.setFixedHeight(BTN_DOWNLOAD_HEIGHT)
        self.btn_download.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        f = QFont()
        f.setPointSize(11)
        f.setBold(True)
        self.btn_download.setFont(f)
        self.btn_download.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        h.addWidget(self.btn_download)

        self.btn_cancel = QPushButton("✕")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.setFixedSize(
            BTN_DOWNLOAD_HEIGHT, BTN_DOWNLOAD_HEIGHT
        )
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        h.addWidget(self.btn_cancel)

        return h

    def _build_log_card(self):
        card = Card()
        lay = card.inner_layout()
        lay.setSpacing(4)

        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 2)

        self.lbl_log = QLabel()
        self.lbl_log.setObjectName("section_label")
        hdr.addWidget(self.lbl_log)

        hdr.addStretch()

        self.btn_clear_log = QPushButton()
        self.btn_clear_log.setObjectName("btn_clear")
        self.btn_clear_log.setFixedHeight(INPUT_HEIGHT)
        self.btn_clear_log.setFixedWidth(110)
        self.btn_clear_log.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        hdr.addWidget(self.btn_clear_log)

        lay.addLayout(hdr)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setObjectName("log_area")
        self.log_area.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        lf = QFont("Consolas", 9)
        lf.setStyleHint(QFont.StyleHint.Monospace)
        self.log_area.setFont(lf)
        lay.addWidget(self.log_area, stretch=1)

        return card

    # ── Signals ──
    def _connect_signals(self):
        self.url_input.returnPressed.connect(self.start_download)
        self.url_input.textChanged.connect(self._on_url_changed)
        self.url_input.customContextMenuRequested.connect(
            self._url_ctx
        )

        self.path_input.editingFinished.connect(
            self._on_path_edited
        )
        self.path_input.customContextMenuRequested.connect(
            self._path_ctx
        )

        self.btn_browse.clicked.connect(self._browse_folder)
        self.btn_browse.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.btn_browse.customContextMenuRequested.connect(
            lambda _: self._open_save_dir()
        )

        self.chk_pdf.toggled.connect(self._on_pdf_toggled)
        self.chk_save_images.toggled.connect(
            self._on_save_images_toggled
        )

        self.combo_theme.currentIndexChanged.connect(
            self._on_theme_changed
        )
        self.combo_lang.currentIndexChanged.connect(
            self._on_lang_changed
        )

        self.btn_download.clicked.connect(self.start_download)
        self.btn_cancel.clicked.connect(self.cancel_download)
        self.btn_clear_log.clicked.connect(self._clear_log)
        self.log_area.customContextMenuRequested.connect(
            self._log_ctx
        )

    def _setup_paste_shortcuts(self):
        for seq in ("Ctrl+V", "Ctrl+М", "Shift+Insert"):
            QShortcut(
                QKeySequence(seq), self,
                activated=self._paste_focused
            )

    # ── Event handlers ──
    def _paste_focused(self):
        w = QApplication.focusWidget()
        if isinstance(w, QLineEdit):
            t = QApplication.clipboard().text()
            if t:
                w.insert(t.strip())

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() or e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e):
        u = ""
        if e.mimeData().hasUrls():
            u = e.mimeData().urls()[0].toString()
        elif e.mimeData().hasText():
            u = e.mimeData().text().strip()
        if u:
            ok, r = URLValidator.validate(u)
            self.url_input.setText(r if ok else u)

    def _on_url_changed(self, text):
        text = text.strip()
        lang = self.config.language

        if not text:
            self.url_hint.setVisible(False)
            self.url_input.setProperty("state", "")
            self._polish(self.url_input)
            return

        ok, result = URLValidator.validate(text)
        self.url_hint.setVisible(True)
        if ok:
            self.url_hint.setText(
                "  ✓ " + get_text(lang, "url_valid")
            )
            self.url_hint.setProperty("state", "valid")
            self.url_input.setProperty("state", "valid")
        else:
            self.url_hint.setText("  " + result)
            self.url_hint.setProperty("state", "invalid")
            self.url_input.setProperty("state", "invalid")

        self._polish(self.url_hint)
        self._polish(self.url_input)

    @staticmethod
    def _polish(w):
        w.style().unpolish(w)
        w.style().polish(w)

    def _set_status(self, t, ms=STATUS_TIMEOUT_MS):
        self.statusBar().showMessage(t)
        if ms > 0:
            self._status_timer.start(ms)

    def _clear_status(self):
        self.statusBar().clearMessage()

    # ── Text & theme ──
    def _update_texts(self):
        lang = self.config.language
        T = lambda k: get_text(lang, k)
        self.setWindowTitle(APP_NAME + " v" + APP_VERSION)
        self.lbl_url.setText(T("lbl_url"))
        self.url_input.setPlaceholderText(T("url_placeholder"))
        self.lbl_save_settings.setText(T("lbl_save_settings"))
        self.btn_browse.setText(T("btn_browse"))
        self.btn_download.setText(T("btn_download"))
        self.btn_cancel.setToolTip(T("btn_cancel"))
        self.chk_pdf.setText(T("chk_pdf"))
        self.chk_save_images.setText(T("chk_save_images"))
        self.lbl_theme.setText(T("lbl_theme"))
        self.lbl_lang.setText(T("lbl_lang"))
        self.lbl_log.setText(T("lbl_log"))
        self.btn_clear_log.setText(T("btn_clear_log"))
        self.btn_about.setToolTip(T("menu_about"))
        self._set_status(T("status_ready"), 0)

    def _apply_theme(self, name):
        if name not in THEMES:
            name = THEMES[0]
        base_qss = load_theme(name)
        chk_qss = _checkbox_qss(name)
        full_qss = base_qss + "\n" + chk_qss
        self.setStyleSheet(full_qss)
        self._current_theme = name
        self._apply_palette(name)

    def _apply_palette(self, theme_name):
        pal = _PALETTES.get(theme_name, _PALETTES["dark"])
        app = QApplication.instance()
        if not app:
            return

        p = QPalette()
        p.setColor(
            QPalette.ColorRole.Window, QColor(pal["window"])
        )
        p.setColor(
            QPalette.ColorRole.Base, QColor(pal["base"])
        )
        p.setColor(
            QPalette.ColorRole.Text, QColor(pal["text"])
        )
        p.setColor(
            QPalette.ColorRole.WindowText, QColor(pal["text"])
        )
        p.setColor(
            QPalette.ColorRole.Button, QColor(pal["button"])
        )
        p.setColor(
            QPalette.ColorRole.ButtonText, QColor(pal["text"])
        )
        p.setColor(
            QPalette.ColorRole.Highlight, QColor(pal["highlight"])
        )
        p.setColor(
            QPalette.ColorRole.HighlightedText, QColor("#ffffff")
        )
        p.setColor(
            QPalette.ColorRole.ToolTipBase,
            QColor(pal["tooltip_bg"])
        )
        p.setColor(
            QPalette.ColorRole.ToolTipText,
            QColor(pal["tooltip_fg"])
        )
        app.setPalette(p)

    # ── Config handlers ──
    def _on_theme_changed(self, i):
        if 0 <= i < len(THEMES):
            self.config.theme = THEMES[i]
            self.config.save()
            self._apply_theme(THEMES[i])

    def _on_lang_changed(self, i):
        self.config.language = "en" if i == 0 else "ru"
        self.config.save()
        self._update_texts()

    def _on_pdf_toggled(self, c):
        self.config.convert_to_pdf = c
        self.config.save()

    def _on_save_images_toggled(self, c):
        self.config.save_images = c
        self.config.save()

    def _check_pdf_availability(self):
        from app.core.pdf_converter import check_available_converters
        cv = check_available_converters()
        av = [n for n, ok in cv.items() if ok]
        if av:
            self.pdf_status_label.setText(
                "(" + ", ".join(av) + ")"
            )
            self.pdf_status_label.setProperty("available", True)
            self.chk_pdf.setEnabled(True)
        else:
            self.pdf_status_label.setText("(no converter)")
            self.pdf_status_label.setProperty("available", False)
            self.chk_pdf.setEnabled(False)
            self.chk_pdf.setChecked(False)
        self._polish(self.pdf_status_label)

    # ── Context menus ──
    def _url_ctx(self, pos):
        lang = self.config.language
        m = QMenu(self)
        m.addAction(
            get_text(lang, "ctx_paste"),
            lambda: self._pw(self.url_input)
        )
        m.addAction(
            get_text(lang, "ctx_clear"),
            self.url_input.clear
        )
        m.exec(self.url_input.mapToGlobal(pos))

    def _path_ctx(self, pos):
        lang = self.config.language
        m = QMenu(self)
        m.addAction(
            get_text(lang, "ctx_paste"),
            lambda: self._pw(self.path_input)
        )
        m.addAction(
            get_text(lang, "ctx_clear"),
            self.path_input.clear
        )
        m.addSeparator()
        m.addAction(
            get_text(lang, "btn_open_dir"),
            self._open_save_dir
        )
        m.exec(self.path_input.mapToGlobal(pos))

    def _log_ctx(self, pos):
        lang = self.config.language
        m = QMenu(self)
        m.addAction(
            get_text(lang, "ctx_copy_all"),
            self._copy_log
        )
        m.addSeparator()
        m.addAction(
            get_text(lang, "btn_clear_log"),
            self._clear_log
        )
        m.exec(self.log_area.mapToGlobal(pos))

    def _pw(self, w):
        t = QApplication.clipboard().text()
        if t:
            w.clear()
            w.insert(t.strip())

    def _copy_log(self):
        t = self.log_area.toPlainText().strip()
        if t:
            QApplication.clipboard().setText(t)

    # ── Path actions ──
    def _browse_folder(self):
        lang = self.config.language
        d = QFileDialog.getExistingDirectory(
            self,
            get_text(lang, "dlg_select_save_folder"),
            self.config.save_dir
        )
        if d:
            self.path_input.setText(d)
            self.config.save_dir = d
            self.config.save()
            self.path_error_label.setVisible(False)

    def _open_save_dir(self):
        p = self.config.save_dir
        if os.path.isdir(p):
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))
        else:
            self._set_status(
                get_text(
                    self.config.language, "err_folder_not_exists"
                ),
                3000
            )

    def _on_path_edited(self):
        p = self.path_input.text().strip()
        if not p:
            return
        ok, r = validate_save_path(p)
        if ok:
            self.config.save_dir = r
            self.path_input.setText(r)
            self.config.save()
            self.path_error_label.setVisible(False)
        else:
            self.path_error_label.setText("  " + r)
            self.path_error_label.setVisible(True)

    def _validate_path(self):
        p = self.path_input.text().strip()
        lang = self.config.language

        if not p:
            _show_warning(
                self,
                get_text(lang, "msg_validation_title"),
                get_text(lang, "err_bad_path")
            )
            return False

        ok, r = validate_save_path(p)
        if not ok:
            _show_warning(
                self,
                get_text(lang, "msg_validation_title"),
                get_text(lang, "err_bad_path") + "\n\n" + r
            )
            self.path_error_label.setText("  " + r)
            self.path_error_label.setVisible(True)
            return False

        self.config.save_dir = r
        self.path_input.setText(r)
        self.config.save()
        self.path_error_label.setVisible(False)
        return True

    # ── Log ──
    def _append_log(self, msg):
        self.log_manager.add_line(msg)
        c = self._lc(msg)
        e = (msg.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))
        if c:
            self.log_area.append(
                '<span style="color:' + c + ';">'
                + e + '</span>'
            )
        else:
            self.log_area.append(msg)

    @staticmethod
    def _lc(m):
        low = m.strip().lower()
        if not low:
            return None
        if any(k in low for k in (
            "success", "готово", "saved",
            "сохранён", "done"
        )):
            return "#4caf50"
        if any(k in low for k in (
            "error", "ошибка", "failed", "not found",
            "не найден", "cancel", "отмен"
        )):
            return "#ef5350"
        if any(k in low for k in (
            "connect", "подключ", "process", "обработ",
            "trying", "convert", "конверт",
            "found", "найден", "saving", "сохран"
        )):
            return "#42a5f5"
        if any(k in low for k in ("target:", "целевой")):
            return "#888888"
        return None

    def _clear_log(self):
        text = self.log_area.toPlainText().strip()
        if not text:
            self._set_status(
                get_text(self.config.language, "status_log_empty"),
                3000
            )
            return

        self.log_manager.save_on_clear(text)
        self.log_area.clear()
        self._set_status(
            get_text(self.config.language, "status_log_cleared"),
            3000
        )

    def _log_ts(self, m):
        self.log_signal.message.emit(m)

    def _prog_ts(self, c, t):
        self.log_signal.progress.emit(c, t)

    def _on_progress(self, c, t):
        self.progress.setRange(0, t)
        self.progress.setValue(c)

    # ── Page size warning callback ──
    def _page_size_warning_cb(self, size_mb):
        """Called from download thread via signal."""
        self.log_signal.page_size_warning.emit(size_mb)

    def _on_page_size_warning(self, size_mb):
        """Handle large page warning in GUI thread."""
        lang = self.config.language
        confirmed = _show_confirm(
            self,
            get_text(lang, "msg_confirm"),
            get_text(lang, "err_page_too_large", f"{size_mb:.1f}")
        )
        if confirmed:
            if self.downloader:
                self.downloader.confirm_large_page()
        else:
            if self.downloader:
                self.downloader.cancel()

    # ── Download ──
    def start_download(self):
        url = self.url_input.text().strip()
        lang = self.config.language

        # Thread-safe check with lock
        if not self._download_lock.acquire(blocking=False):
            _show_warning(
                self,
                get_text(lang, "msg_warning"),
                get_text(lang, "err_already_downloading")
            )
            return

        try:
            if not url:
                _show_warning(
                    self,
                    get_text(lang, "msg_warning"),
                    get_text(lang, "err_no_url")
                )
                self.url_input.setFocus()
                self._download_lock.release()
                return

            ok, res = URLValidator.validate(url)
            if not ok:
                _show_warning(
                    self,
                    get_text(lang, "msg_validation_title"),
                    get_text(lang, "err_bad_url")
                    + "\n\n(" + res + ")"
                )
                self.url_input.setFocus()
                self.url_input.selectAll()
                self._download_lock.release()
                return

            if not self._validate_path():
                self._download_lock.release()
                return

            self.log_manager.start_session()

            self.btn_download.setEnabled(False)
            self.btn_download.setText(
                get_text(lang, "btn_downloading")
            )
            self.btn_cancel.setEnabled(True)
            self.progress.setRange(0, 0)
            self.progress.setVisible(True)
            self.log_area.clear()
            self._set_status(
                get_text(lang, "status_downloading"), 0
            )

            self.downloader = GuideDownloader(self.config)
            self._download_thread = threading.Thread(
                target=self.downloader.download,
                args=(
                    res, self.config.save_dir,
                    self.config.language,
                    self._log_ts,
                    lambda: self.log_signal.finished.emit(),
                    self.chk_pdf.isChecked(),
                    self._prog_ts,
                    self.chk_save_images.isChecked(),
                    self._page_size_warning_cb,
                ),
                daemon=True, name="DL"
            )
            self._download_thread.start()

        except Exception:
            # Release lock if anything goes wrong during setup
            if self._download_lock.locked():
                self._download_lock.release()
            raise

    def cancel_download(self):
        if self.downloader:
            self.downloader.cancel()

    def _on_download_finished(self):
        lang = self.config.language
        self.btn_download.setEnabled(True)
        self.btn_download.setText(
            get_text(lang, "btn_download")
        )
        self.btn_cancel.setEnabled(False)
        self.progress.setVisible(False)
        self._set_status(get_text(lang, "status_done"))
        self.log_manager.save_session()
        self.downloader = None
        self._download_thread = None
        if self._download_lock.locked():
            self._download_lock.release()
        self.downloader = None
        self._download_thread = None

    def _show_about(self):
        px = get_icon().pixmap(128, 128)
        AboutDialog(
            get_about_text(self.config.language),
            px, self.config.language, self
        ).exec()

    # ── Geometry ──
    def _restore_geometry(self):
        g = QSettings(
            "SteamGuideDownloader", "MW"
        ).value("geo")
        if g:
            self.restoreGeometry(g)

    def _save_geometry(self):
        QSettings(
            "SteamGuideDownloader", "MW"
        ).setValue("geo", self.saveGeometry())

    def closeEvent(self, e):
        if self.downloader:
            self.downloader.cancel()
        # Wait for download thread to finish
        if (self._download_thread
                and self._download_thread.is_alive()):
            self._download_thread.join(timeout=5)
        self._save_geometry()
        self.config.save()
        e.accept()