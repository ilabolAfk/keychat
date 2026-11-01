import colorsys
import os
import sys

# Базовый (тёмный) акцент по умолчанию.
DEFAULT_ACCENT = "#FF7A1A"


def is_hex_color(s) -> bool:
    return isinstance(s, str) and len(s) == 7 and s[0] == "#"


def _app_icon_dir() -> str:
    """Папка с иконками: там же, где main.py (или рядом с exe в frozen-режиме)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def app_icon_path(theme="dark") -> str:
    """Иконка приложения: светлая тема — icon_black.ico, тёмная — icon_white.ico."""
    name = "icon_black.ico" if theme == "light" else "icon_white.ico"
    path = os.path.join(_app_icon_dir(), name)
    return path if os.path.exists(path) else ""


def _lighten(hex_color, factor):
    """Светлее цвет на factor через HSV (hex -> hex)."""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    v = min(1.0, v + (1.0 - v) * factor)
    nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
    return "#{:02X}{:02X}{:02X}".format(int(nr * 255) % 256, int(ng * 255) % 256, int(nb * 255) % 256)


def _darken(hex_color, factor):
    """Темнее цвет на factor через HSL (hex -> hex)."""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    v = max(0.0, v * (1.0 - factor))
    nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
    return "#{:02X}{:02X}{:02X}".format(int(nr * 255) % 256, int(ng * 255) % 256, int(nb * 255) % 256)


# Очки к t для контрастного текста на акценте (оценка яркости).
def _contrast_text(hex_color):
    lum = (
        int(hex_color[1:3], 16) * 299
        + int(hex_color[3:5], 16) * 587
        + int(hex_color[5:7], 16) * 114
    ) / 1000
    return "#101010" if lum > 150 else "#FFFFFF"


def build_palette(accent=DEFAULT_ACCENT, theme="dark"):
    """Строит палитру цветов под заданный акцент и режим (dark/light)."""
    accent = accent.upper()
    light = theme == "light"
    base = {
        "orange": accent,
        "orange_light": _lighten(accent, 0.18),
        "orange_dark": _darken(accent, 0.22),
    }
    if light:
        base.update({
            "bg": "#F5F2EE",
            "bg_elevated": "#FFFFFF",
            "bg_card": "#FFFFFF",
            "bg_input": "#FFFFFF",
            "border": "#DDD6CC",
            "text": "#201A12",
            "text_dim": "#8A7F70",
            "text_on_orange": _contrast_text(accent),
            "bubble_me": accent,
            "bubble_peer": "#EFEAE2",
            "scroll": "#C9C0B0",
            "danger": "#D23",
        })
    else:
        base.update({
            "bg": "#14100C",
            "bg_elevated": "#1E1811",
            "bg_card": "#251D13",
            "bg_input": "#2B2217",
            "border": "#3A2E1E",
            "text": "#F5EFE6",
            "text_dim": "#A89A88",
            "text_on_orange": _contrast_text(accent),
            "bubble_me": accent,
            "bubble_peer": "#2B2217",
            "scroll": "#4A3B26",
            "danger": "#E14B4B",
        })
    return base


PALETTE = build_palette()


def _qss(p):
    return f"""
* {{
    font-family: "Segoe UI";
    outline: none;
}}
QWidget {{
    background-color: {p['bg']};
    color: {p['text']};
}}
QMainWindow, QWidget#Root {{
    background-color: {p['bg']};
}}
QFrame#Sidebar, QWidget#Sidebar {{
    background-color: {p['bg_elevated']};
}}
QLabel#BrandTitle {{
    font-size: 20px;
    font-weight: 700;
    color: {p['orange']};
}}
QLabel#BrandSub {{
    font-size: 12px;
    color: {p['text_dim']};
}}
QLabel#UserName {{ font-size: 15px; font-weight: 600; }}
QLabel#UserStatus {{ font-size: 11px; color: {p['text_dim']}; }}
QLabel#HeaderPeer {{ font-size: 16px; font-weight: 600; }}
QLabel#SectionTitle {{
    font-size: 12px; font-weight: 700; color: {p['text_dim']}; letter-spacing: 1px;
}}
QPushButton {{
    background-color: {p['bg_card']};
    border: 1px solid {p['border']};
    border-radius: 10px;
    color: {p['text']};
    font-size: 14px; font-weight: 600; padding: 8px 14px;
}}
QPushButton:hover {{ background-color: {p['bg_input']}; border-color: {p['orange_light']}; }}
QPushButton:pressed {{ background-color: {p['orange_dark']}; color: {p['text_on_orange']}; }}
QPushButton#Accent {{ background-color: {p['orange']}; border: none; color: {p['text_on_orange']}; }}
QPushButton#Accent:hover {{ background-color: {p['orange_light']}; }}
QPushButton#Accent:pressed {{ background-color: {p['orange_dark']}; }}
QPushButton#Ghost {{ background-color: transparent; border: 1px solid {p['border']}; }}
QPushButton#Ghost:hover {{ border-color: {p['orange']}; color: {p['orange']}; }}
QPushButton#Danger {{ background-color: transparent; border: 1px solid {p['danger']}; color: {p['danger']}; }}
QPushButton#Danger:hover {{ background-color: rgba(220,80,80,0.15); }}
QPushButton#IconBtn {{ background-color: transparent; border: none; border-radius: 8px; padding: 6px; }}
QPushButton#IconBtn:hover {{ background-color: {p['border']}; }}
QLineEdit, QTextEdit {{
    background-color: {p['bg_input']};
    border: 1px solid {p['border']};
    border-radius: 10px; padding: 8px 12px; font-size: 14px;
    selection-background-color: {p['orange']};
}}
QLineEdit:focus, QTextEdit:focus {{ border-color: {p['orange']}; }}
QListWidget {{ background-color: transparent; border: none; font-size: 14px; }}
QListWidget::item {{ border-radius: 10px; padding: 8px 10px; margin: 1px 2px; color: {p['text']}; }}
QListWidget::item:selected {{
    background-color: rgba(255,122,26,0.20);
    border-left: 3px solid {p['orange']};
    color: {p['text']};
}}
QListWidget::item:hover:!selected {{ background-color: {p['bg_card']}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {p['scroll']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {p['orange']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{ background: {p['scroll']}; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QDialog {{ background-color: {p['bg_elevated']}; }}
QDialog QLabel#DialogTitle {{ font-size: 18px; font-weight: 700; color: {p['orange']}; }}
QMessageBox QLabel {{ font-size: 14px; }}
QToolTip {{
    background-color: {p['bg_card']}; color: {p['text']};
    border: 1px solid {p['border']}; padding: 4px 8px; border-radius: 6px;
}}
QTabBar::tab {{
    background: transparent; color: {p['text_dim']};
    padding: 8px 20px; font-size: 13px; font-weight: 600;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{ color: {p['orange']}; border-bottom: 2px solid {p['orange']}; }}
QComboBox {{
    background-color: {p['bg_input']}; border: 1px solid {p['border']};
    border-radius: 10px; padding: 8px 12px; font-size: 14px;
}}
QComboBox:drop-down {{ border-left: 1px solid {p['border']}; width: 30px; }}
QComboBox QAbstractItemView {{
    background-color: {p['bg_elevated']}; border: 1px solid {p['border']};
    selection-background-color: {p['orange']}; selection-color: {p['text_on_orange']};
}}
"""


# Возвращает (палитра, qss).
def build_styles(accent=DEFAULT_ACCENT, theme="dark"):
    pal = build_palette(accent, theme)
    return pal, _qss(pal)


def apply_theme(accent=DEFAULT_ACCENT, theme="dark"):
    """Применяет акцент/режим, обновляя глобальные PALETTE и QSS на месте.

    Мутуирует существующий PALETTE-объект, чтобы виджеты, сделавшие
    `from .theme import PALETTE`, увидели новый цвет, а не старую ссылку.
    """
    global QSS
    new_pal, new_qss = build_styles(accent, theme)
    PALETTE.clear()
    PALETTE.update(new_pal)
    QSS = new_qss
    return new_pal, new_qss


def current_qss():
    """Возвращает актуальную строку QSS (после apply_theme)."""
    return QSS


palette, QSS = build_styles()
FONT_FAMILY = "Segoe UI"