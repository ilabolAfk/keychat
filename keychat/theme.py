PALETTE = {
    "orange": "#FF7A1A",
    "orange_light": "#FF9A4D",
    "orange_dark": "#E66500",
    "bg": "#14100C",
    "bg_elevated": "#1E1811",
    "bg_card": "#251D13",
    "bg_input": "#2B2217",
    "border": "#3A2E1E",
    "text": "#F5EFE6",
    "text_dim": "#A89A88",
    "text_on_orange": "#1A0F00",
    "bubble_me": "#FF7A1A",
    "bubble_peer": "#2B2217",
    "scroll": "#4A3B26",
    "danger": "#E14B4B",
}

# Размеры адаптируются к DPI при построении виджетов через Scale-хелперы.
FONT_FAMILY = "Segoe UI"

QSS = """
* {
    font-family: "Segoe UI";
    outline: none;
}
QWidget {
    background-color: %(bg)s;
    color: %(text)s;
}
QMainWindow, QWidget#Root {
    background-color: %(bg)s;
}
QFrame#Sidebar, QWidget#Sidebar {
    background-color: %(bg_elevated)s;
}
QLabel#BrandTitle {
    font-size: 20px;
    font-weight: 700;
    color: %(orange)s;
}
QLabel#BrandSub {
    font-size: 12px;
    color: %(text_dim)s;
}
QLabel#UserName {
    font-size: 15px;
    font-weight: 600;
}
QLabel#UserStatus {
    font-size: 11px;
    color: %(text_dim)s;
}
QLabel#HeaderPeer {
    font-size: 16px;
    font-weight: 600;
}
QLabel#SectionTitle {
    font-size: 12px;
    font-weight: 700;
    color: %(text_dim)s;
    letter-spacing: 1px;
}
QPushButton {
    background-color: %(bg_card)s;
    border: 1px solid %(border)s;
    border-radius: 10px;
    color: %(text)s;
    font-size: 14px;
    font-weight: 600;
    padding: 8px 14px;
}
QPushButton:hover {
    background-color: %(bg_input)s;
    border-color: %(orange_light)s;
}
QPushButton:pressed {
    background-color: %(orange_dark)s;
    color: %(text_on_orange)s;
}
QPushButton#Accent {
    background-color: %(orange)s;
    border: none;
    color: %(text_on_orange)s;
}
QPushButton#Accent:hover {
    background-color: %(orange_light)s;
}
QPushButton#Accent:pressed {
    background-color: %(orange_dark)s;
}
QPushButton#Ghost {
    background-color: transparent;
    border: 1px solid %(border)s;
}
QPushButton#Ghost:hover {
    border-color: %(orange)s;
    color: %(orange)s;
}
QPushButton#Danger {
    background-color: transparent;
    border: 1px solid %(danger)s;
    color: %(danger)s;
}
QPushButton#Danger:hover {
    background-color: rgba(225, 75, 75, 0.15);
}
QPushButton#IconBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 6px;
    font-size: 16px;
}
QPushButton#IconBtn:hover {
    background-color: %(border)s;
}
QLineEdit, QTextEdit {
    background-color: %(bg_input)s;
    border: 1px solid %(border)s;
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 14px;
    selection-background-color: %(orange)s;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: %(orange)s;
}
QListWidget {
    background-color: transparent;
    border: none;
    font-size: 14px;
}
QListWidget::item {
    border-radius: 10px;
    padding: 8px 10px;
    margin: 1px 2px;
    color: %(text)s;
}
QListWidget::item:selected {
    background-color: rgba(255, 122, 26, 0.20);
    border-left: 3px solid %(orange)s;
    color: %(text)s;
}
QListWidget::item:hover:!selected {
    background-color: %(bg_card)s;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: %(scroll)s;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: %(orange)s;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
}
QScrollBar::handle:horizontal {
    background: %(scroll)s;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QDialog {
    background-color: %(bg_elevated)s;
}
QDialog QLabel#DialogTitle {
    font-size: 18px;
    font-weight: 700;
    color: %(orange)s;
}
QMessageBox QLabel {
    font-size: 14px;
}
QToolTip {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    padding: 4px 8px;
    border-radius: 6px;
}
QComboBox {
    background-color: %(bg_input)s;
    border: 1px solid %(border)s;
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 14px;
}
QComboBox:drop-down {
    border-left: 1px solid %(border)s;
    width: 30px;
}
QComboBox QAbstractItemView {
    background-color: %(bg_elevated)s;
    border: 1px solid %(border)s;
    selection-background-color: %(orange)s;
    selection-color: %(text_on_orange)s;
}
""" % PALETTE