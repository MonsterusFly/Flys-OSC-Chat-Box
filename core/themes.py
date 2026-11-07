"""User selectable palettes for the native Qt application."""

THEMES = {
    "Midnight Blue": {"bg":"#151a23", "panel":"#10151e", "input":"#202a39", "preview":"#202b3c", "text":"#eaf0fa", "muted":"#a8b7d0", "border":"#455575", "group":"#344156", "button":"#313f58", "hover":"#43577d", "accent":"#5269d7", "accent_hover":"#6880f0", "selected":"#374b89", "selection":"#546de0"},
    "AMOLED Black": {"bg":"#08090b", "panel":"#000000", "input":"#17191f", "preview":"#181b22", "text":"#f4f5f9", "muted":"#a7adb9", "border":"#393e4c", "group":"#353b48", "button":"#272d38", "hover":"#404957", "accent":"#6875e9", "accent_hover":"#8792ff", "selected":"#38416f", "selection":"#535bbb"},
    "Nord Frost": {"bg":"#2e3440", "panel":"#242933", "input":"#3b4252", "preview":"#40495b", "text":"#eceff4", "muted":"#c3cfdf", "border":"#65758d", "group":"#58687e", "button":"#48566b", "hover":"#5a6c85", "accent":"#5e81ac", "accent_hover":"#81a1c1", "selected":"#456487", "selection":"#5e81ac"},
    "Forest": {"bg":"#15201c", "panel":"#0c1713", "input":"#23362d", "preview":"#294235", "text":"#e2f5e9", "muted":"#a5c7b4", "border":"#4a7861", "group":"#345c48", "button":"#2e5140", "hover":"#42765b", "accent":"#27895d", "accent_hover":"#35a873", "selected":"#23694c", "selection":"#27895d"},
    "Royal Purple": {"bg":"#211828", "panel":"#150e1c", "input":"#372841", "preview":"#3d2e4b", "text":"#f4eafa", "muted":"#c9add8", "border":"#745589", "group":"#5d436d", "button":"#51375f", "hover":"#694a7a", "accent":"#8957cb", "accent_hover":"#a678e3", "selected":"#624091", "selection":"#8957cb"},
    "Light": {"bg":"#f3f5f9", "panel":"#e5eaf2", "input":"#ffffff", "preview":"#e9eef7", "text":"#1d2637", "muted":"#4d617a", "border":"#b3c1d4", "group":"#bec9d9", "button":"#d6e0ef", "hover":"#c5d4ea", "accent":"#4263c7", "accent_hover":"#3153b2", "selected":"#b5c9f5", "selection":"#8faaf2"},
}

DEFAULT_THEME = "Midnight Blue"


def normalize_theme(name: str) -> str:
    return name if isinstance(name, str) and name in THEMES else DEFAULT_THEME


def stylesheet(name: str) -> str:
    c = THEMES[normalize_theme(name)]
    return f"""
    QMainWindow, QWidget {{ background: {c['bg']}; color: {c['text']}; font-size: 13px; }}
    QListWidget {{ background: {c['panel']}; border: none; padding: 12px 7px; font-size: 14px; }}
    QListWidget::item {{ padding: 15px 14px; border-radius: 8px; margin: 2px; }}
    QListWidget::item:selected {{ background: {c['selected']}; color: {c['text']}; }}
    QListWidget::item:hover:!selected {{ background: {c['hover']}; }}
    QGroupBox {{ border: 1px solid {c['group']}; border-radius: 10px; margin-top: 15px;
                 padding: 16px 12px 12px; font-weight: bold; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 5px; }}
    QLineEdit, QTextEdit, QSpinBox, QComboBox {{ background: {c['input']}; color: {c['text']}; border: 1px solid {c['border']};
        border-radius: 7px; padding: 8px; selection-background-color: {c['selection']}; }}
    QPushButton {{ background: {c['button']}; color: {c['text']}; border: 0; border-radius: 7px; padding: 11px 15px; }}
    QPushButton:hover {{ background: {c['hover']}; }}
    QPushButton#primary {{ background: {c['accent']}; color: white; font-weight: bold; }}
    QPushButton#primary:hover {{ background: {c['accent_hover']}; }}
    QLabel#header {{ font-size: 25px; font-weight: bold; }}
    QLabel#subtitle {{ color: {c['muted']}; }}
    QLabel#preview {{ background: {c['preview']}; border-radius: 8px; padding: 16px; font-size: 15px; }}
    QLabel#notice {{ color: {c['muted']}; }}
    QLabel#stat {{ font-size: 18px; font-weight: bold; }}
    QProgressBar {{ border: 1px solid {c['border']}; background: {c['input']}; color: {c['text']}; border-radius: 6px; text-align: center; }}
    QProgressBar::chunk {{ background: {c['accent']}; border-radius: 5px; }}
    QToolTip {{ background: {c['input']}; color: {c['text']}; border: 1px solid {c['border']}; }}
    """
