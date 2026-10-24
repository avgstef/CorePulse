"""The polished CorePulse application shell and monitoring-thread coordination."""
from __future__ import annotations

import ctypes
import os
from collections import deque
from datetime import datetime
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from services.system_monitor import HardwareWorker, MonitorWorker
from ui.pages import GraphicsPage, OverviewPage, ProcessorPage, MemoryPage, StoragePage, SystemPage
from utils import ACCENT, APP_NAME, BACKGROUND, MUTED, SUCCESS, resource_path
from widgets.visuals import AtmosphereSurface, BrandMark, NavigationButton, StatusDot


APPLICATION_STYLE = f"""
QMainWindow {{ background: {BACKGROUND}; }}
QWidget {{
    color: #F4F5F7;
    font-family: "Segoe UI Variable Text", "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}}
QToolTip {{
    background-color: #1C2027;
    color: #F4F5F7;
    border: 1px solid #3B424D;
    border-radius: 5px;
    padding: 6px 8px;
}}
#appRoot {{ background: transparent; }}
#contentLayer, #pageStack {{ background: transparent; }}
#monitorPage, #pageViewport, #pageContainer {{ background: transparent; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
#sidebar {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0E1014, stop:0.55 #0C0E12, stop:1 #0A0C0F); border-right: 1px solid #252B34; }}
#brandName {{ color: #F4F5F7; font-size: 15pt; font-weight: 700; letter-spacing: 0.3px; }}
#brandTag {{ color: #929BA8; font-size: 8pt; }}
#navCaption {{ color: #626B77; font-size: 8pt; font-weight: 700; letter-spacing: 1.1px; padding-left: 15px; }}
#sideLivePanel {{ background: #13171C; border: 1px solid #262D35; border-radius: 10px; }}
#sideLiveTitle {{ color: #E7EAF0; font-size: 9pt; font-weight: 600; }}
#sideLiveDetail {{ color: #929BA8; font-size: 8pt; }}
#sideFooter {{ color: #626B77; font-size: 8pt; }}
#topHeader {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0B0C10, stop:0.7 #0B0D11, stop:1 #111116); border-bottom: 1px solid #252A32; }}
#pageTitle {{ color: #F8F9FB; font-size: 23pt; font-weight: 700; letter-spacing: -0.3px; }}
#pageSubtitle {{ color: #929BA8; font-size: 10pt; }}
#statusPill {{ background: #122119; border: 1px solid #254634; border-radius: 13px; color: #9DE1B6; font-size: 8pt; font-weight: 600; padding: 0 9px; }}
#clockLabel {{ color: #F4F5F7; font-family: "Cascadia Mono", "Consolas", monospace; font-size: 11pt; font-weight: 600; }}
#clockDate {{ color: #7D8795; font-size: 8pt; }}
#pageContainer {{ background: {BACKGROUND}; }}
#metricCard {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #15191F, stop:0.58 #101318, stop:1 #0F1217); border: 1px solid #303741; border-radius: 11px; }}
#metricCard:hover {{ border: 1px solid #545D6A; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #191E25, stop:1 #11151A); }}
#metricTitle {{ color: #929BA8; font-size: 8pt; font-weight: 700; letter-spacing: 0.8px; }}
#metricCategory {{ color: #FFB16E; background: #302015; border-radius: 6px; font-size: 7pt; font-weight: 700; min-width: 29px; max-height: 18px; padding: 1px 4px; }}
#metricValue {{ color: #F4F5F7; font-size: 22pt; font-weight: 700; }}
#metricDetail {{ color: #929BA8; font-size: 8.5pt; }}
#sectionCard {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #13171D, stop:0.52 #101318, stop:1 #0E1115); border: 1px solid #303741; border-radius: 12px; }}
#sectionCard:hover {{ border: 1px solid #414A56; }}
#sectionTitle {{ color: #F4F5F7; font-size: 11pt; font-weight: 700; }}
#sectionSubtitle {{ color: #929BA8; font-size: 8.5pt; }}
#gpuName {{ color: #FFB16E; font-size: 13pt; font-weight: 700; padding: 3px 0 7px 0; }}
#infoRow {{ border-bottom: 1px solid #222831; background: transparent; }}
#infoLabel {{ color: #7E8794; font-size: 8pt; font-weight: 700; letter-spacing: 0.5px; }}
#infoValue {{ color: #E5E8EC; font-size: 9pt; }}
#emptyState {{ background: #101318; border: 1px solid #272E37; border-radius: 10px; }}
#emptyTitle {{ color: #E6E9ED; font-size: 9.5pt; font-weight: 700; }}
#emptyBody {{ color: #929BA8; font-size: 8.5pt; }}
#mutedText {{ color: #929BA8; font-size: 9pt; }}
#coreLabel {{ color: #929BA8; font-size: 8pt; font-family: "Cascadia Mono", "Consolas", monospace; }}
QProgressBar {{ background: #222831; border: 0; border-radius: 5px; color: #F5F1ED; text-align: center; font-size: 7pt; font-weight: 600; }}
QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF6F1C, stop:0.65 #FF8126, stop:1 #FFB16E); border-radius: 5px; }}
#storageTable, #hardwareTable {{ background: transparent; border: none; color: #E2E5EA; selection-background-color: #232932; gridline-color: transparent; }}
#storageTable::item, #hardwareTable::item {{ border-bottom: 1px solid #232932; padding: 7px 8px; }}
#storageTable::item:hover, #hardwareTable::item:hover {{ background: #1A1F26; }}
QHeaderView::section {{ background: #171B21; color: #929BA8; border: none; border-bottom: 1px solid #303742; padding: 9px 8px; font-size: 8pt; font-weight: 700; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: #303640; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #444C58; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
"""


class MainWindow(QtWidgets.QMainWindow):
    """CorePulse root window; owns worker threads and distributes snapshots to pages."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — System Intelligence, at a Glance.")
        self.setWindowIcon(QtGui.QIcon(resource_path("assets/corepulse.png")))
        self.resize(1440, 900)
        self.setMinimumSize(1020, 700)
        self._history: deque[float] = deque(maxlen=60)
        self._latest_hardware: dict[str, Any] = {}
        self._transition: QtCore.QPropertyAnimation | None = None
        self._startup_animation: QtCore.QPropertyAnimation | None = None
        self._closing = False
        self._build_interface()
        self._setup_clock()
        self._start_monitoring()

    def _build_interface(self) -> None:
        root = AtmosphereSurface()
        root.setObjectName("appRoot")
        self.setCentralWidget(root)
        root_layout = QtWidgets.QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())

        content = QtWidgets.QWidget()
        content.setObjectName("contentLayer")
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._build_header())
        self.pages = QtWidgets.QStackedWidget()
        self.pages.setObjectName("pageStack")
        self.overview_page = OverviewPage()
        self.processor_page = ProcessorPage()
        self.memory_page = MemoryPage()
        self.storage_page = StoragePage()
        self.graphics_page = GraphicsPage()
        self.system_page = SystemPage()
        self._page_widgets = [
            self.overview_page,
            self.processor_page,
            self.memory_page,
            self.storage_page,
            self.graphics_page,
            self.system_page,
        ]
        for page in self._page_widgets:
            self.pages.addWidget(page)
        content_layout.addWidget(self.pages, 1)
        root_layout.addWidget(content, 1)
        self._switch_page(0, animate=False)

    def _build_sidebar(self) -> QtWidgets.QWidget:
        sidebar = QtWidgets.QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(228)
        layout = QtWidgets.QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 21, 15, 17)
        layout.setSpacing(6)

        branding = QtWidgets.QHBoxLayout()
        branding.setContentsMargins(8, 0, 6, 20)
        branding.setSpacing(11)
        branding.addWidget(BrandMark(40))
        brand_text = QtWidgets.QVBoxLayout()
        brand_text.setSpacing(0)
        name = QtWidgets.QLabel(APP_NAME)
        name.setObjectName("brandName")
        tag = QtWidgets.QLabel("SYSTEM INTELLIGENCE")
        tag.setObjectName("brandTag")
        brand_text.addWidget(name)
        brand_text.addWidget(tag)
        branding.addLayout(brand_text, 1)
        layout.addLayout(branding)

        nav_caption = QtWidgets.QLabel("MONITORING")
        nav_caption.setObjectName("navCaption")
        layout.addWidget(nav_caption)
        navigation = (
            ("Overview", "overview"),
            ("Processor", "processor"),
            ("Memory", "memory"),
            ("Storage", "storage"),
            ("Graphics", "graphics"),
            ("System", "system"),
        )
        self.nav_buttons: list[NavigationButton] = []
        for index, (label, icon_name) in enumerate(navigation):
            button = NavigationButton(label, icon_name)
            button.clicked.connect(lambda checked=False, index=index: self._switch_page(index))
            self.nav_buttons.append(button)
            layout.addWidget(button)
        layout.addStretch(1)

        status_panel = QtWidgets.QFrame()
        status_panel.setObjectName("sideLivePanel")
        status_layout = QtWidgets.QHBoxLayout(status_panel)
        status_layout.setContentsMargins(11, 10, 9, 10)
        status_layout.setSpacing(8)
        status_layout.addWidget(StatusDot())
        status_text = QtWidgets.QVBoxLayout()
        status_text.setSpacing(1)
        self.side_status_title = QtWidgets.QLabel("Local monitoring")
        self.side_status_title.setObjectName("sideLiveTitle")
        self.side_status_detail = QtWidgets.QLabel("Starting services…")
        self.side_status_detail.setObjectName("sideLiveDetail")
        status_text.addWidget(self.side_status_title)
        status_text.addWidget(self.side_status_detail)
        status_layout.addLayout(status_text, 1)
        layout.addWidget(status_panel)
        footer = QtWidgets.QLabel("CorePulse 1.0.0  •  Local-only")
        footer.setObjectName("sideFooter")
        footer.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        return sidebar

    def _build_header(self) -> QtWidgets.QWidget:
        header = QtWidgets.QFrame()
        header.setObjectName("topHeader")
        header.setFixedHeight(106)
        layout = QtWidgets.QHBoxLayout(header)
        layout.setContentsMargins(31, 17, 31, 16)
        layout.setSpacing(18)
        text = QtWidgets.QVBoxLayout()
        text.setSpacing(2)
        self.header_title = QtWidgets.QLabel()
        self.header_title.setObjectName("pageTitle")
        self.header_subtitle = QtWidgets.QLabel()
        self.header_subtitle.setObjectName("pageSubtitle")
        text.addWidget(self.header_title)
        text.addWidget(self.header_subtitle)
        layout.addLayout(text, 1)

        status = QtWidgets.QFrame()
        status.setObjectName("statusPill")
        status_layout = QtWidgets.QHBoxLayout(status)
        status_layout.setContentsMargins(9, 0, 9, 0)
        status_layout.setSpacing(4)
        status_layout.addWidget(StatusDot())
        self.header_status = QtWidgets.QLabel("MONITORING ACTIVE")
        status_layout.addWidget(self.header_status)
        layout.addWidget(status, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

        clock = QtWidgets.QVBoxLayout()
        clock.setSpacing(1)
        self.clock_label = QtWidgets.QLabel()
        self.clock_label.setObjectName("clockLabel")
        self.clock_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.date_label = QtWidgets.QLabel()
        self.date_label.setObjectName("clockDate")
        self.date_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        clock.addWidget(self.clock_label)
        clock.addWidget(self.date_label)
        layout.addLayout(clock)
        return header

    def _setup_clock(self) -> None:
        self._clock_timer = QtCore.QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._refresh_clock)
        self._refresh_clock()
        self._clock_timer.start()

    def _refresh_clock(self) -> None:
        now = datetime.now()
        self.clock_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%A, %d %b %Y").upper())

    def _switch_page(self, index: int, animate: bool = True) -> None:
        if index < 0 or index >= len(self._page_widgets):
            return
        page = self._page_widgets[index]
        self.pages.setCurrentIndex(index)
        self.header_title.setText(page.page_title)
        self.header_subtitle.setText(page.page_subtitle)
        for button_index, button in enumerate(self.nav_buttons):
            button.set_active(button_index == index)
        if animate:
            effect = QtWidgets.QGraphicsOpacityEffect(page)
            page.setGraphicsEffect(effect)
            self._transition = QtCore.QPropertyAnimation(effect, b"opacity", self)
            self._transition.setDuration(180)
            self._transition.setStartValue(0.18)
            self._transition.setEndValue(1.0)
            self._transition.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
            self._transition.finished.connect(lambda current=page: current.setGraphicsEffect(None))
            self._transition.start()

    def _start_monitoring(self) -> None:
        self.monitor_thread = QtCore.QThread(self)
        self.monitor_worker = MonitorWorker(interval_ms=1000)
        self.monitor_worker.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.monitor_worker.start)
        self.monitor_worker.snapshot_ready.connect(self._on_snapshot)
        self.monitor_worker.monitor_error.connect(self._on_monitor_error)
        self.monitor_thread.finished.connect(self.monitor_worker.deleteLater)
        self.monitor_thread.start()

        self.hardware_thread = QtCore.QThread(self)
        self.hardware_worker = HardwareWorker()
        self.hardware_worker.moveToThread(self.hardware_thread)
        self.hardware_thread.started.connect(self.hardware_worker.collect)
        self.hardware_worker.hardware_ready.connect(self._on_hardware_ready)
        self.hardware_worker.hardware_ready.connect(self.hardware_thread.quit)
        self.hardware_thread.finished.connect(self.hardware_worker.deleteLater)
        self.hardware_thread.start()

    @QtCore.Slot(dict)
    def _on_snapshot(self, snapshot: dict[str, Any]) -> None:
        if self._closing:
            return
        cpu = snapshot.get("cpu_percent")
        if isinstance(cpu, (int, float)):
            self._history.append(float(cpu))
        self.side_status_title.setText("Local monitoring")
        self.side_status_detail.setText("1-second refresh interval")
        self.header_status.setText("MONITORING ACTIVE")
        for page in self._page_widgets:
            page.on_snapshot(snapshot, list(self._history))

    @QtCore.Slot(dict)
    def _on_hardware_ready(self, hardware: dict[str, Any]) -> None:
        if self._closing:
            return
        self._latest_hardware = hardware
        for page in self._page_widgets:
            page.on_hardware(hardware)

    @QtCore.Slot(str)
    def _on_monitor_error(self, message: str) -> None:
        # The dashboard remains usable; do not show a modal dialog every second.
        self.side_status_title.setText("Refresh issue")
        self.side_status_detail.setText("Retrying local telemetry")
        self.header_status.setText("RETRYING")
        self.header_status.parentWidget().setToolTip(message)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        self._enable_windows_dark_title_bar()
        if self._startup_animation is None:
            self.setWindowOpacity(0.0)
            self._startup_animation = QtCore.QPropertyAnimation(self, b"windowOpacity", self)
            self._startup_animation.setDuration(280)
            self._startup_animation.setStartValue(0.0)
            self._startup_animation.setEndValue(1.0)
            self._startup_animation.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
            self._startup_animation.start()

    def _enable_windows_dark_title_bar(self) -> None:
        """Use the documented Windows 10/11 DWM flag when it is present; fail harmlessly."""
        if os.name != "nt":
            return
        try:
            value = ctypes.c_int(1)
            # Attribute 20 is current; 19 covers older Windows 10 builds.
            hwnd = int(self.winId())
            for attribute in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
                )
        except (AttributeError, OSError):
            pass

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._closing = True
        if hasattr(self, "monitor_worker") and self.monitor_thread.isRunning():
            QtCore.QMetaObject.invokeMethod(self.monitor_worker, "stop", QtCore.Qt.ConnectionType.QueuedConnection)
            self.monitor_thread.quit()
            self.monitor_thread.wait(3000)
        if hasattr(self, "hardware_thread") and self.hardware_thread.isRunning():
            self.hardware_thread.quit()
            # GPU discovery has a deliberately bounded PowerShell timeout.
            self.hardware_thread.wait(8000)
        event.accept()


def create_application() -> QtWidgets.QApplication:
    """Configure Qt before creating the first application window."""
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName("CorePulse")
    app.setStyle("Fusion")
    # Windows 11 uses Segoe UI Variable; Windows 10 automatically falls back to Segoe UI.
    interface_font = QtGui.QFont("Segoe UI Variable Text")
    interface_font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferAntialias)
    app.setFont(interface_font)
    app.setStyleSheet(APPLICATION_STYLE)
    app.setWindowIcon(QtGui.QIcon(resource_path("assets/corepulse.png")))
    return app
