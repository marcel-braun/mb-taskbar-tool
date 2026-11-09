from PySide6.QtCore import QRect

from mbtaskbar.ui.hover_popup import popup_position

SCREEN = QRect(0, 0, 1920, 1032)  # taskbar at bottom (48 px)


def test_bottom_taskbar_places_above() -> None:
    pos = popup_position(QRect(1700, 1040, 24, 24), (200, 100), SCREEN)
    assert pos.y() + 100 <= 1040
    assert 0 <= pos.x() <= 1920 - 200


def test_clamped_to_right_edge() -> None:
    pos = popup_position(QRect(1900, 1040, 20, 24), (300, 100), SCREEN)
    assert pos.x() + 300 <= SCREEN.right()


def test_top_taskbar_places_below() -> None:
    screen = QRect(0, 48, 1920, 1032)
    pos = popup_position(QRect(1700, 10, 24, 24), (200, 100), screen)
    assert pos.y() == 56
    assert abs(pos.x() + 100 - 1712) <= 1
