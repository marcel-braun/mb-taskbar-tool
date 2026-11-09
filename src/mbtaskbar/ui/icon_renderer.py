from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPixmap

ICON_SIZE = 64


def taskbar_is_light() -> bool:
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
            return bool(value)
    except (OSError, ImportError):
        return False


def fitting_font(text: str, size: int, family: str = "Segoe UI") -> QFont:
    font = QFont(family)
    font.setBold(True)
    pixel_size = size
    while pixel_size > 6:
        font.setPixelSize(pixel_size)
        fm = QFontMetrics(font)
        if fm.horizontalAdvance(text) <= size and fm.ascent() - fm.descent() <= size:
            break
        pixel_size -= 1
    return font


def render_text_icon(
    text: str, light_taskbar: bool | None = None, *, alert: bool = False
) -> QIcon:
    if light_taskbar is None:
        light_taskbar = taskbar_is_light()
    if alert:
        color = QColor("#ff4343")
    else:
        color = QColor(0, 0, 0) if light_taskbar else QColor(255, 255, 255)

    pixmap = QPixmap(ICON_SIZE, ICON_SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setFont(fitting_font(text, ICON_SIZE))
    painter.setPen(color)
    painter.drawText(QRect(0, 0, ICON_SIZE, ICON_SIZE), Qt.AlignmentFlag.AlignCenter, text)
    painter.end()
    return QIcon(pixmap)
