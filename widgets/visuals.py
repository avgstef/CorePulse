"""Custom-painted, reusable presentation widgets used across CorePulse."""
from __future__ import annotations

from collections.abc import Sequence
import math
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from utils import ACCENT, ACCENT_SOFT, BORDER, CARD, DANGER, MUTED, SUCCESS, SURFACE, TEXT


class AtmosphereSurface(QtWidgets.QWidget):
    """A restrained animated technical backdrop behind the dashboard content.

    This is deliberately painted instead of using an image wallpaper so it scales cleanly,
    has no external asset dependency, and remains subtle below data-heavy cards.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._phase = 0.0
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self._animation = QtCore.QPropertyAnimation(self, b"ambientPhase", self)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(13500)
        self._animation.setLoopCount(-1)
        self._animation.setEasingCurve(QtCore.QEasingCurve.Type.InOutSine)
        self._animation.start()

    def _get_phase(self) -> float:
        return self._phase

    def _set_phase(self, value: float) -> None:
        self._phase = float(value)
        self.update()

    ambientPhase = QtCore.Property(float, _get_phase, _set_phase)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        rect = QtCore.QRectF(self.rect())
        base = QtGui.QLinearGradient(rect.topLeft(), rect.bottomRight())
        base.setColorAt(0.0, QtGui.QColor("#08090B"))
        base.setColorAt(0.48, QtGui.QColor("#0A0C10"))
        base.setColorAt(1.0, QtGui.QColor("#08090B"))
        painter.fillRect(rect, base)

        drift = math.sin(self._phase * math.tau) * 0.055
        for x_fraction, y_fraction, radius, alpha in (
            (0.79 + drift, 0.20, max(rect.width(), rect.height()) * 0.54, 21),
            (0.43 - drift * 0.6, 0.88, max(rect.width(), rect.height()) * 0.40, 13),
        ):
            center = QtCore.QPointF(rect.left() + rect.width() * x_fraction, rect.top() + rect.height() * y_fraction)
            glow = QtGui.QRadialGradient(center, radius)
            bright = QtGui.QColor(ACCENT)
            bright.setAlpha(alpha)
            edge = QtGui.QColor(ACCENT)
            edge.setAlpha(0)
            glow.setColorAt(0.0, bright)
            glow.setColorAt(1.0, edge)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(center, radius, radius)

        # A barely-visible technical grid grounds the content without competing with data.
        grid_pen = QtGui.QPen(QtGui.QColor(42, 48, 57, 38), 1)
        painter.setPen(grid_pen)
        step = 56
        for x in range(0, int(rect.width()) + step, step):
            painter.drawLine(x, 0, x, int(rect.height()))
        for y in range(0, int(rect.height()) + step, step):
            painter.drawLine(0, y, int(rect.width()), y)


class BrandMark(QtWidgets.QWidget):
    """The compact geometric CorePulse emblem; scalable and independent of an image."""

    def __init__(self, size: int = 38, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)
        center = rect.center()
        outer = QtGui.QRadialGradient(center, rect.width() / 1.8)
        outer.setColorAt(0, QtGui.QColor("#343A43"))
        outer.setColorAt(1, QtGui.QColor("#101216"))
        painter.setBrush(outer)
        painter.setPen(QtGui.QPen(QtGui.QColor("#3A414B"), 1))
        painter.drawEllipse(rect)
        arc_rect = rect.adjusted(6, 6, -6, -6)
        pen = QtGui.QPen(QtGui.QColor(ACCENT), max(2.4, self._size / 11))
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawArc(arc_rect, 38 * 16, 276 * 16)
        path = QtGui.QPainterPath()
        y = center.y()
        left = rect.left() + self._size * 0.22
        path.moveTo(left, y)
        path.lineTo(left + self._size * 0.13, y)
        path.lineTo(left + self._size * 0.20, y - self._size * 0.15)
        path.lineTo(left + self._size * 0.30, y + self._size * 0.16)
        path.lineTo(left + self._size * 0.40, y - self._size * 0.07)
        path.lineTo(left + self._size * 0.50, y)
        path.lineTo(left + self._size * 0.60, y)
        pulse_pen = QtGui.QPen(QtGui.QColor("#FFF2E9"), max(1.3, self._size / 26))
        pulse_pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pulse_pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pulse_pen)
        painter.drawPath(path)


class StatusDot(QtWidgets.QWidget):
    """A tiny, restrained animated live-status indicator."""

    def __init__(self, color: str = SUCCESS, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QtGui.QColor(color)
        self._phase = 0.0
        self.setFixedSize(15, 15)
        self._animation = QtCore.QPropertyAnimation(self, b"phase", self)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(1700)
        self._animation.setLoopCount(-1)
        self._animation.start()

    def _get_phase(self) -> float:
        return self._phase

    def _set_phase(self, phase: float) -> None:
        self._phase = phase
        self.update()

    phase = QtCore.Property(float, _get_phase, _set_phase)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        radius = 3.2 + self._phase * 3.2
        color = QtGui.QColor(self._color)
        color.setAlphaF(max(0.0, 0.22 * (1 - self._phase)))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(center, radius, radius)
        painter.setBrush(self._color)
        painter.drawEllipse(center, 3.2, 3.2)


class NavigationButton(QtWidgets.QAbstractButton):
    """Flat custom side-navigation control with a fading hover surface."""

    def __init__(self, text: str, icon_name: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._icon_name = icon_name
        self._active = False
        self._hover = 0.0
        self.setText(text)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(46)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self._hover_animation = QtCore.QPropertyAnimation(self, b"hoverAmount", self)
        self._hover_animation.setDuration(150)
        self._hover_animation.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)

    def set_active(self, active: bool) -> None:
        self._active = active
        self.setAccessibleDescription("Current page" if active else f"Open {self.text()} page")
        self.update()

    def _get_hover(self) -> float:
        return self._hover

    def _set_hover(self, value: float) -> None:
        self._hover = value
        self.update()

    hoverAmount = QtCore.Property(float, _get_hover, _set_hover)

    def enterEvent(self, event: QtCore.QEvent) -> None:
        self._animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self._animate_hover(0.0)
        super().leaveEvent(event)

    def _animate_hover(self, end: float) -> None:
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._hover)
        self._hover_animation.setEndValue(end)
        self._hover_animation.start()

    def _draw_icon(self, painter: QtGui.QPainter, rect: QtCore.QRectF, color: QtGui.QColor) -> None:
        pen = QtGui.QPen(color, 1.55)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        if self._icon_name == "overview":
            unit = rect.width() * 0.37
            for x, y in ((rect.left(), rect.top()), (rect.right() - unit, rect.top()),
                         (rect.left(), rect.bottom() - unit), (rect.right() - unit, rect.bottom() - unit)):
                painter.drawRoundedRect(QtCore.QRectF(x, y, unit, unit), 1.5, 1.5)
        elif self._icon_name == "processor":
            inner = rect.adjusted(4, 4, -4, -4)
            painter.drawRoundedRect(inner, 2, 2)
            for fraction in (0.25, 0.5, 0.75):
                x = rect.left() + rect.width() * fraction
                y = rect.top() + rect.height() * fraction
                painter.drawLine(x, rect.top() + 1, x, inner.top())
                painter.drawLine(x, inner.bottom(), x, rect.bottom() - 1)
                painter.drawLine(rect.left() + 1, y, inner.left(), y)
                painter.drawLine(inner.right(), y, rect.right() - 1, y)
        elif self._icon_name == "memory":
            body = rect.adjusted(1.5, 5, -1.5, -5)
            painter.drawRoundedRect(body, 2, 2)
            for fraction in (0.22, 0.42, 0.62, 0.82):
                x = body.left() + body.width() * fraction
                painter.drawLine(x, body.top() + 3, x, body.bottom() - 3)
                painter.drawLine(x, body.bottom(), x, body.bottom() + 3)
        elif self._icon_name == "storage":
            body = rect.adjusted(2, 3, -2, -3)
            painter.drawRoundedRect(body, 3, 3)
            painter.drawLine(body.left(), body.top() + 5, body.right(), body.top() + 5)
            painter.drawEllipse(QtCore.QRectF(body.right() - 5.5, body.top() + 1.7, 2.8, 2.8))
        elif self._icon_name == "graphics":
            body = rect.adjusted(1.5, 4.5, -1.5, -4.5)
            painter.drawRoundedRect(body, 2.5, 2.5)
            fan = QtCore.QRectF(body.center().x() - 3.5, body.center().y() - 3.5, 7, 7)
            painter.drawEllipse(fan)
            for angle in (0, 120, 240):
                radians = math.radians(angle)
                end = QtCore.QPointF(body.center().x() + math.cos(radians) * 5.7, body.center().y() + math.sin(radians) * 5.7)
                painter.drawLine(body.center(), end)
            painter.drawLine(body.left() - 2, body.top() + 3, body.left(), body.top() + 3)
            painter.drawLine(body.left() - 2, body.bottom() - 3, body.left(), body.bottom() - 3)
        else:  # system
            painter.drawEllipse(rect.adjusted(3, 3, -3, -3))
            painter.drawLine(rect.center().x(), rect.top() + 3, rect.center().x(), rect.bottom() - 3)
            painter.drawLine(rect.left() + 3, rect.center().y(), rect.right() - 3, rect.center().y())
            painter.drawArc(rect.adjusted(3, 5, -3, -5), 0, 180 * 16)
            painter.drawArc(rect.adjusted(3, 5, -3, -5), 180 * 16, 180 * 16)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(4, 2, -4, -2)
        if self._active:
            bg = QtGui.QColor(ACCENT)
            bg.setAlpha(35)
            painter.setBrush(bg)
            painter.setPen(QtGui.QPen(QtGui.QColor(ACCENT).lighter(120), 1))
            painter.drawRoundedRect(rect, 8, 8)
            painter.setBrush(QtGui.QColor(ACCENT))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QtCore.QRectF(rect.left(), rect.top() + 10, 3, rect.height() - 20), 1.5, 1.5)
        elif self._hover > 0:
            bg = QtGui.QColor("#FFFFFF")
            bg.setAlpha(int(10 * self._hover))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(rect, 8, 8)
        color = QtGui.QColor(ACCENT if self._active else MUTED)
        self._draw_icon(painter, QtCore.QRectF(rect.left() + 14, rect.center().y() - 9, 18, 18), color)
        painter.setPen(QtGui.QColor(TEXT if self._active else "#C1C7D0"))
        font = QtGui.QFont("Segoe UI", 10)
        font.setWeight(QtGui.QFont.Weight.DemiBold if self._active else QtGui.QFont.Weight.Medium)
        painter.setFont(font)
        painter.drawText(QtCore.QRectF(rect.left() + 45, rect.top(), rect.width() - 54, rect.height()),
                         QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft, self.text())


class MetricCard(QtWidgets.QFrame):
    """Top-row metric card with a small visual hierarchy and a live label."""

    def __init__(self, title: str, category: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setMinimumHeight(136)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(17, 15, 17, 14)
        layout.setSpacing(5)
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(8)
        self.title = QtWidgets.QLabel(title.upper())
        self.title.setObjectName("metricTitle")
        self.category = QtWidgets.QLabel(category)
        self.category.setObjectName("metricCategory")
        self.category.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        top.addWidget(self.title)
        top.addStretch()
        top.addWidget(self.category)
        layout.addLayout(top)
        self.value = QtWidgets.QLabel("—")
        self.value.setObjectName("metricValue")
        self.value.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.value)
        self.detail = QtWidgets.QLabel("Waiting for local telemetry…")
        self.detail.setObjectName("metricDetail")
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.detail)
        layout.addStretch(1)

    def set_metric(self, value: str, detail: str, tooltip: str | None = None) -> None:
        self.value.setText(value)
        self.detail.setText(detail)
        if tooltip:
            self.setToolTip(tooltip)


class CircularGauge(QtWidgets.QWidget):
    """Antialiased utilization gauge with an animated custom Qt property."""

    def __init__(self, title: str, subtitle: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._value = 0.0
        self._target = 0.0
        self._title = title
        self._subtitle = subtitle
        self._detail = "Waiting for telemetry"
        self._animate = QtCore.QPropertyAnimation(self, b"displayValue", self)
        self._animate.setDuration(560)
        self._animate.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self.setMinimumSize(218, 250)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setAccessibleName(f"{title} utilization gauge")

    def _get_display_value(self) -> float:
        return self._value

    def _set_display_value(self, value: float) -> None:
        self._value = max(0.0, min(100.0, float(value)))
        self.update()

    displayValue = QtCore.Property(float, _get_display_value, _set_display_value)

    def set_reading(self, value: float | None, detail: str | None = None) -> None:
        if value is None:
            self._detail = "Not available on this system."
            self.update()
            return
        self._target = max(0.0, min(100.0, float(value)))
        self._detail = detail or "Live local reading"
        self._animate.stop()
        self._animate.setStartValue(self._value)
        self._animate.setEndValue(self._target)
        self._animate.start()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
        area = self.rect().adjusted(12, 9, -12, -11)
        diameter = min(area.width(), area.height() - 45)
        circle = QtCore.QRectF(area.center().x() - diameter / 2, area.top() + 4, diameter, diameter)
        track = circle.adjusted(14, 14, -14, -14)
        # restrained 270 degree gauge, leaving a deliberate lower gap
        track_pen = QtGui.QPen(QtGui.QColor("#2B3038"), max(8.0, diameter * 0.075))
        track_pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawArc(track, 225 * 16, -270 * 16)
        # low-contrast tick marks establish a technical instrument look
        tick_pen = QtGui.QPen(QtGui.QColor("#3A404A"), 1.2)
        painter.setPen(tick_pen)
        center = track.center()
        radius = track.width() / 2
        for index in range(0, 13):
            degrees = 225 - index * 270 / 12
            angle = degrees * math.pi / 180
            outer = QtCore.QPointF(center.x() + math.cos(angle) * (radius + 9), center.y() - math.sin(angle) * (radius + 9))
            inner = QtCore.QPointF(center.x() + math.cos(angle) * (radius + 5), center.y() - math.sin(angle) * (radius + 5))
            painter.drawLine(outer, inner)
        span = -270 * (self._value / 100.0)
        glow_pen = QtGui.QPen(QtGui.QColor(ACCENT), max(9.0, diameter * 0.082))
        glow_pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(glow_pen)
        painter.drawArc(track, 225 * 16, int(span * 16))
        accent_pen = QtGui.QPen(QtGui.QColor(ACCENT_SOFT), max(3.0, diameter * 0.026))
        accent_pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(accent_pen)
        painter.drawArc(track, 225 * 16, int(span * 16))
        # center percentage and meaning
        text_rect = QtCore.QRectF(track.left(), track.center().y() - 31, track.width(), 47)
        painter.setPen(QtGui.QColor(TEXT))
        number_font = QtGui.QFont("Segoe UI", max(22, int(diameter * 0.18)))
        number_font.setWeight(QtGui.QFont.Weight.DemiBold)
        painter.setFont(number_font)
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop,
                         f"{self._value:.0f}%")
        painter.setPen(QtGui.QColor(MUTED))
        caption_font = QtGui.QFont("Segoe UI", 9)
        caption_font.setLetterSpacing(QtGui.QFont.SpacingType.PercentageSpacing, 108)
        painter.setFont(caption_font)
        painter.drawText(QtCore.QRectF(track.left(), track.center().y() + 16, track.width(), 20),
                         QtCore.Qt.AlignmentFlag.AlignHCenter, self._subtitle.upper())
        painter.setPen(QtGui.QColor(TEXT))
        title_font = QtGui.QFont("Segoe UI", 11)
        title_font.setWeight(QtGui.QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.drawText(QtCore.QRectF(area.left(), circle.bottom() + 7, area.width(), 21),
                         QtCore.Qt.AlignmentFlag.AlignHCenter, self._title)
        painter.setPen(QtGui.QColor(MUTED))
        detail_font = QtGui.QFont("Segoe UI", 8)
        painter.setFont(detail_font)
        painter.drawText(QtCore.QRectF(area.left(), circle.bottom() + 27, area.width(), 18),
                         QtCore.Qt.AlignmentFlag.AlignHCenter, self._detail)


class UsageBar(QtWidgets.QWidget):
    """A smooth, custom-drawn capacity bar that does not use platform styling."""

    def __init__(self, label: str = "Usage", parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._value = 0.0
        self._label = label
        self._caption = "Waiting for telemetry…"
        self._animation = QtCore.QPropertyAnimation(self, b"displayValue", self)
        self._animation.setDuration(520)
        self._animation.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self.setMinimumHeight(52)

    def _get_display_value(self) -> float:
        return self._value

    def _set_display_value(self, value: float) -> None:
        self._value = max(0.0, min(100.0, value))
        self.update()

    displayValue = QtCore.Property(float, _get_display_value, _set_display_value)

    def set_usage(self, value: float | None, caption: str) -> None:
        self._caption = caption
        if value is None:
            self._value = 0
            self.update()
            return
        self._animation.stop()
        self._animation.setStartValue(self._value)
        self._animation.setEndValue(float(value))
        self._animation.start()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        label_rect = QtCore.QRectF(0, 0, self.width(), 19)
        painter.setPen(QtGui.QColor(TEXT))
        font = QtGui.QFont("Segoe UI", 9)
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(label_rect, QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter, self._label)
        painter.setPen(QtGui.QColor(MUTED))
        painter.drawText(label_rect, QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter, self._caption)
        bar = QtCore.QRectF(0, 29, self.width(), 9)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor("#262C34"))
        painter.drawRoundedRect(bar, 4.5, 4.5)
        if self._value > 0:
            fill_width = max(7.0, bar.width() * self._value / 100.0)
            fill = QtCore.QRectF(bar.left(), bar.top(), min(fill_width, bar.width()), bar.height())
            gradient = QtGui.QLinearGradient(fill.topLeft(), fill.topRight())
            gradient.setColorAt(0, QtGui.QColor(ACCENT))
            gradient.setColorAt(1, QtGui.QColor(ACCENT_SOFT))
            painter.setBrush(gradient)
            painter.drawRoundedRect(fill, 4.5, 4.5)


class LineChart(QtWidgets.QWidget):
    """Live CPU history chart rendered without a heavyweight chart dependency."""

    def __init__(self, title: str = "CPU activity", parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        self._values: list[float] = []
        self._latest_label = "—"
        self._footer = "Awaiting monitor samples"
        self.setMinimumHeight(245)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setAccessibleName(title)

    def set_values(self, values: Sequence[float], latest_label: str, footer: str) -> None:
        self._values = [max(0.0, min(100.0, float(value))) for value in values]
        self._latest_label = latest_label
        self._footer = footer
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
        outer = QtCore.QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.setBrush(QtGui.QColor(CARD))
        painter.setPen(QtGui.QPen(QtGui.QColor(BORDER), 1))
        painter.drawRoundedRect(outer, 12, 12)
        painter.setPen(QtGui.QColor(TEXT))
        title_font = QtGui.QFont("Segoe UI", 11)
        title_font.setWeight(QtGui.QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.drawText(QtCore.QRectF(19, 15, self.width() - 145, 22), QtCore.Qt.AlignmentFlag.AlignLeft, self._title)
        painter.setPen(QtGui.QColor(ACCENT_SOFT))
        metric_font = QtGui.QFont("Segoe UI", 10)
        metric_font.setWeight(QtGui.QFont.Weight.DemiBold)
        painter.setFont(metric_font)
        painter.drawText(QtCore.QRectF(self.width() - 120, 15, 98, 22), QtCore.Qt.AlignmentFlag.AlignRight, self._latest_label)
        chart = QtCore.QRectF(20, 51, self.width() - 40, max(58, self.height() - 87))
        grid_pen = QtGui.QPen(QtGui.QColor("#252B33"), 1)
        grid_pen.setStyle(QtCore.Qt.PenStyle.DotLine)
        painter.setPen(grid_pen)
        for row in range(5):
            y = chart.top() + chart.height() * row / 4
            painter.drawLine(chart.left(), y, chart.right(), y)
            if row in (0, 2, 4):
                painter.setPen(QtGui.QColor("#626B77"))
                small = QtGui.QFont("Segoe UI", 7)
                painter.setFont(small)
                painter.drawText(QtCore.QRectF(chart.left() + 3, y - 10, 35, 12), f"{100 - row * 25}%")
                painter.setPen(grid_pen)
        if len(self._values) >= 2:
            path = QtGui.QPainterPath()
            points: list[QtCore.QPointF] = []
            length = max(1, len(self._values) - 1)
            for index, value in enumerate(self._values):
                x = chart.left() + chart.width() * index / length
                y = chart.bottom() - chart.height() * value / 100.0
                points.append(QtCore.QPointF(x, y))
            path.moveTo(points[0])
            for index in range(1, len(points)):
                previous, current = points[index - 1], points[index]
                mid_x = (previous.x() + current.x()) / 2
                path.cubicTo(mid_x, previous.y(), mid_x, current.y(), current.x(), current.y())
            fill_path = QtGui.QPainterPath(path)
            fill_path.lineTo(points[-1].x(), chart.bottom())
            fill_path.lineTo(points[0].x(), chart.bottom())
            fill_path.closeSubpath()
            fill_gradient = QtGui.QLinearGradient(chart.topLeft(), chart.bottomLeft())
            top_color = QtGui.QColor(ACCENT)
            top_color.setAlpha(75)
            bottom_color = QtGui.QColor(ACCENT)
            bottom_color.setAlpha(0)
            fill_gradient.setColorAt(0, top_color)
            fill_gradient.setColorAt(1, bottom_color)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(fill_gradient)
            painter.drawPath(fill_path)
            line_pen = QtGui.QPen(QtGui.QColor(ACCENT), 2.1)
            line_pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
            line_pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
            painter.setPen(line_pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
            last = points[-1]
            painter.setBrush(QtGui.QColor("#1A1D22"))
            painter.setPen(QtGui.QPen(QtGui.QColor(ACCENT_SOFT), 2.2))
            painter.drawEllipse(last, 3.7, 3.7)
        else:
            painter.setPen(QtGui.QColor(MUTED))
            painter.setFont(QtGui.QFont("Segoe UI", 9))
            painter.drawText(chart, QtCore.Qt.AlignmentFlag.AlignCenter, "Collecting local CPU history…")
        painter.setPen(QtGui.QColor(MUTED))
        painter.setFont(QtGui.QFont("Segoe UI", 8))
        painter.drawText(QtCore.QRectF(20, self.height() - 28, self.width() - 40, 15),
                         QtCore.Qt.AlignmentFlag.AlignLeft, self._footer)
        painter.drawText(QtCore.QRectF(20, self.height() - 28, self.width() - 40, 15),
                         QtCore.Qt.AlignmentFlag.AlignRight, "60-second window")


class InfoRow(QtWidgets.QFrame):
    """A two-column property row that wraps values safely."""

    def __init__(self, label: str, value: str = "Loading…", parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("infoRow")
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(18)
        self.label = QtWidgets.QLabel(label.upper())
        self.label.setObjectName("infoLabel")
        self.label.setMinimumWidth(115)
        self.value = QtWidgets.QLabel(value)
        self.value.setObjectName("infoValue")
        self.value.setWordWrap(True)
        self.value.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.value.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.label, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.value, 1)

    def set_value(self, value: object, tooltip: Optional[str] = None) -> None:
        text = str(value)
        self.value.setText(text)
        self.value.setToolTip(tooltip or text)


class SectionCard(QtWidgets.QFrame):
    """Consistent panel surface to host richer page-specific layouts."""

    def __init__(self, title: str | None = None, subtitle: str | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionCard")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(19, 17, 19, 17)
        self.layout.setSpacing(10)
        if title:
            title_label = QtWidgets.QLabel(title)
            title_label.setObjectName("sectionTitle")
            self.layout.addWidget(title_label)
        if subtitle:
            subtitle_label = QtWidgets.QLabel(subtitle)
            subtitle_label.setObjectName("sectionSubtitle")
            subtitle_label.setWordWrap(True)
            self.layout.addWidget(subtitle_label)


class EmptyState(QtWidgets.QFrame):
    """Honest neutral state for values the operating system does not expose."""

    def __init__(self, title: str, message: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("emptyState")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        heading = QtWidgets.QLabel(title)
        heading.setObjectName("emptyTitle")
        body = QtWidgets.QLabel(message)
        body.setObjectName("emptyBody")
        body.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(body)


class PageHeader(QtWidgets.QWidget):
    """Title/subtitle header shared by dedicated pages."""

    def __init__(self, title: str, subtitle: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(4)
        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QtWidgets.QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
