"""CorePulse monitor pages.  Widgets receive local snapshots from MainWindow."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from utils import ACCENT, MUTED, bytes_to_human, format_boot_time, uptime_text
from widgets.visuals import (
    CircularGauge,
    EmptyState,
    InfoRow,
    LineChart,
    MetricCard,
    PageHeader,
    SectionCard,
    UsageBar,
)


def _number_or_unavailable(value: Any, suffix: str = "") -> str:
    return f"{value}{suffix}" if value is not None and value != "Not available on this system." else "Not available on this system."


def _safe_percent(value: Any) -> float | None:
    try:
        return max(0.0, min(100.0, float(value)))
    except (ValueError, TypeError):
        return None


class MonitorPage(QtWidgets.QScrollArea):
    """Scrollable base that maintains the same clean presentation rhythm on every page."""

    page_title = "Overview"
    page_subtitle = "System Intelligence, at a Glance."

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("monitorPage")
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport().setObjectName("pageViewport")
        self.container = QtWidgets.QWidget()
        self.container.setObjectName("pageContainer")
        self.layout = QtWidgets.QVBoxLayout(self.container)
        self.layout.setContentsMargins(30, 22, 30, 30)
        self.layout.setSpacing(18)
        self.setWidget(self.container)
        self._hardware: dict[str, Any] = {}

    def on_snapshot(self, snapshot: dict[str, Any], history: Sequence[float]) -> None:
        """Implemented by child pages receiving a monitor sample."""

    def on_hardware(self, hardware: dict[str, Any]) -> None:
        self._hardware = hardware


class OverviewPage(MonitorPage):
    page_title = "Overview"
    page_subtitle = "Live performance telemetry for this PC."

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        metrics = QtWidgets.QGridLayout()
        metrics.setHorizontalSpacing(14)
        metrics.setVerticalSpacing(14)
        self.cpu_card = MetricCard("CPU load", "LIVE")
        self.memory_card = MetricCard("Memory used", "RAM")
        self.drive_card = MetricCard("System drive", "DISK")
        self.uptime_card = MetricCard("System uptime", "HOST")
        for index, card in enumerate((self.cpu_card, self.memory_card, self.drive_card, self.uptime_card)):
            metrics.addWidget(card, 0, index)
            metrics.setColumnStretch(index, 1)
        self.layout.addLayout(metrics)

        main_row = QtWidgets.QHBoxLayout()
        main_row.setSpacing(18)
        focus = SectionCard("Performance focus", "Smooth, local readings sampled once per second.")
        focus_row = QtWidgets.QHBoxLayout()
        focus_row.setSpacing(4)
        self.cpu_gauge = CircularGauge("Processor", "CPU utilization")
        self.memory_gauge = CircularGauge("Memory", "RAM utilization")
        focus_row.addWidget(self.cpu_gauge, 1)
        focus_row.addWidget(self.memory_gauge, 1)
        focus.layout.addLayout(focus_row)
        main_row.addWidget(focus, 5)
        self.chart = LineChart("CPU activity")
        main_row.addWidget(self.chart, 6)
        self.layout.addLayout(main_row)

        lower_row = QtWidgets.QHBoxLayout()
        lower_row.setSpacing(18)
        self.hardware_card = SectionCard("Hardware snapshot", "Core components discovered from the local operating system.")
        self.hw_processor = InfoRow("Processor")
        self.hw_graphics = InfoRow("Graphics")
        self.hw_memory = InfoRow("Installed RAM")
        self.hw_os = InfoRow("Operating system")
        self.hw_temperature = InfoRow("CPU temperature", "Looking for a supported local sensor…")
        for row in (self.hw_processor, self.hw_graphics, self.hw_memory, self.hw_os, self.hw_temperature):
            self.hardware_card.layout.addWidget(row)
        lower_row.addWidget(self.hardware_card, 6)

        self.storage_card = SectionCard("System storage", "Capacity reported for the configured system volume.")
        self.storage_capacity = InfoRow("Capacity")
        self.storage_available = InfoRow("Available")
        self.storage_bar = UsageBar("System drive")
        self.storage_card.layout.addWidget(self.storage_capacity)
        self.storage_card.layout.addWidget(self.storage_available)
        self.storage_card.layout.addSpacing(4)
        self.storage_card.layout.addWidget(self.storage_bar)
        lower_row.addWidget(self.storage_card, 4)
        self.layout.addLayout(lower_row)

        facts = SectionCard("Quick system facts")
        facts_row = QtWidgets.QHBoxLayout()
        self.logical_fact = InfoRow("Logical processors")
        self.physical_fact = InfoRow("Physical cores")
        self.boot_fact = InfoRow("Last boot")
        self.runtime_fact = InfoRow("Python runtime")
        for row in (self.logical_fact, self.physical_fact, self.boot_fact, self.runtime_fact):
            facts_row.addWidget(row, 1)
        facts.layout.addLayout(facts_row)
        self.layout.addWidget(facts)
        self.layout.addStretch(1)

    def on_hardware(self, hardware: dict[str, Any]) -> None:
        super().on_hardware(hardware)
        processor = str(hardware.get("processor", "Not available on this system."))
        graphics = ", ".join(hardware.get("graphics", ["Not available on this system."]))
        ram = bytes_to_human(hardware.get("installed_ram"))
        os_name = str(hardware.get("operating_system", "Not available on this system."))
        self.hw_processor.set_value(processor)
        self.hw_graphics.set_value(graphics)
        self.hw_memory.set_value(ram)
        self.hw_os.set_value(os_name)
        self.logical_fact.set_value(_number_or_unavailable(hardware.get("logical_cores")))
        self.physical_fact.set_value(_number_or_unavailable(hardware.get("physical_cores")))
        self.boot_fact.set_value(format_boot_time(hardware.get("boot_time")))
        self.runtime_fact.set_value(f"Python {hardware.get('python_version', 'Not available')}")

    def on_snapshot(self, snapshot: dict[str, Any], history: Sequence[float]) -> None:
        cpu = _safe_percent(snapshot.get("cpu_percent"))
        memory = _safe_percent(snapshot.get("memory_percent"))
        drive = _safe_percent(snapshot.get("drive_percent"))
        self.cpu_card.set_metric(f"{cpu:.0f}%" if cpu is not None else "—", "Processor utilization")
        self.memory_card.set_metric(
            f"{memory:.0f}%" if memory is not None else "—",
            f"{bytes_to_human(snapshot.get('memory_used'))} of {bytes_to_human(snapshot.get('memory_total'))}",
        )
        self.drive_card.set_metric(
            f"{drive:.0f}%" if drive is not None else "—",
            f"{bytes_to_human(snapshot.get('drive_free'))} free",
        )
        self.uptime_card.set_metric(uptime_text(snapshot.get("uptime_seconds")), "Since last system boot")
        self.cpu_gauge.set_reading(cpu, "Live local sample")
        self.memory_gauge.set_reading(memory, f"{bytes_to_human(snapshot.get('memory_available'))} available")
        self.chart.set_values(history, f"{cpu:.0f}%" if cpu is not None else "—", "Recent processor utilization")
        temp = snapshot.get("temperature")
        self.hw_temperature.set_value(f"{temp:.0f} °C" if temp is not None else "Not available on this system.")
        self.storage_capacity.set_value(bytes_to_human(snapshot.get("drive_total")))
        self.storage_available.set_value(bytes_to_human(snapshot.get("drive_free")))
        caption = f"{drive:.0f}% used" if drive is not None else "Not available on this system."
        self.storage_bar.set_usage(drive, caption)


class CoreUsageGrid(QtWidgets.QWidget):
    """Actual per-logical-processor utilization bars, created only when exposed by psutil."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(14)
        self.layout.setVerticalSpacing(9)
        self._bars: list[QtWidgets.QProgressBar] = []
        self._labels: list[QtWidgets.QLabel] = []
        self._empty = QtWidgets.QLabel("Waiting for per-core telemetry…")
        self._empty.setObjectName("mutedText")
        self.layout.addWidget(self._empty, 0, 0)

    def set_values(self, values: Sequence[float]) -> None:
        if not values:
            self._empty.setText("Per-core utilization is not available on this system.")
            return
        if len(self._bars) != len(values):
            while self.layout.count():
                item = self.layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            self._bars.clear()
            self._labels.clear()
            columns = 2 if len(values) <= 16 else 3
            for index in range(len(values)):
                cell = QtWidgets.QWidget()
                row_layout = QtWidgets.QHBoxLayout(cell)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)
                label = QtWidgets.QLabel(f"CPU {index + 1}")
                label.setObjectName("coreLabel")
                label.setMinimumWidth(43)
                bar = QtWidgets.QProgressBar()
                bar.setRange(0, 100)
                bar.setTextVisible(True)
                bar.setFormat("%p%")
                bar.setFixedHeight(17)
                bar.setAccessibleName(f"CPU {index + 1} utilization")
                row_layout.addWidget(label)
                row_layout.addWidget(bar, 1)
                self.layout.addWidget(cell, index // columns, index % columns)
                self._labels.append(label)
                self._bars.append(bar)
        for bar, value in zip(self._bars, values):
            bar.setValue(int(max(0, min(100, value))))


class ProcessorPage(MonitorPage):
    page_title = "Processor"
    page_subtitle = "Real-time CPU load, frequency, and logical-processor activity."

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(18)
        gauge_card = SectionCard("Current processor load", "Smoothly animated reading sampled locally.")
        self.gauge = CircularGauge("Processor", "CPU utilization")
        gauge_card.layout.addWidget(self.gauge, 1)
        top.addWidget(gauge_card, 3)
        self.summary = SectionCard("Processor details", "Hardware discovery runs away from the interface thread.")
        self.model = InfoRow("Model")
        self.manufacturer = InfoRow("Manufacturer")
        self.logical = InfoRow("Logical processors")
        self.physical = InfoRow("Physical cores")
        self.socket = InfoRow("Socket")
        self.max_frequency = InfoRow("Maximum frequency")
        self.frequency = InfoRow("Current frequency")
        for row in (self.model, self.manufacturer, self.logical, self.physical, self.socket, self.max_frequency, self.frequency):
            self.summary.layout.addWidget(row)
        top.addWidget(self.summary, 5)
        self.layout.addLayout(top)
        self.chart = LineChart("Processor activity")
        self.layout.addWidget(self.chart)
        cores = SectionCard("Per-logical-processor utilization", "Reported directly by psutil when the operating system makes it available.")
        self.core_grid = CoreUsageGrid()
        cores.layout.addWidget(self.core_grid)
        self.layout.addWidget(cores)
        self.layout.addStretch(1)

    def on_hardware(self, hardware: dict[str, Any]) -> None:
        super().on_hardware(hardware)
        self.model.set_value(hardware.get("processor", "Not available on this system."))
        details = hardware.get("processor_details", {}) or {}
        self.manufacturer.set_value(details.get("manufacturer", "Not available on this system."))
        self.logical.set_value(_number_or_unavailable(hardware.get("logical_cores")))
        self.physical.set_value(_number_or_unavailable(hardware.get("physical_cores")))
        self.socket.set_value(details.get("socket", "Not available on this system."))
        maximum = details.get("max_clock_mhz")
        self.max_frequency.set_value(f"{maximum:,.0f} MHz" if isinstance(maximum, (int, float)) else "Not available on this system.")

    def on_snapshot(self, snapshot: dict[str, Any], history: Sequence[float]) -> None:
        cpu = _safe_percent(snapshot.get("cpu_percent"))
        frequency = snapshot.get("cpu_frequency")
        self.gauge.set_reading(cpu, "Live local sample")
        self.frequency.set_value(f"{frequency:,.0f} MHz" if frequency is not None else "Not available on this system.")
        self.chart.set_values(history, f"{cpu:.0f}%" if cpu is not None else "—", "Recent processor utilization")
        self.core_grid.set_values(snapshot.get("cpu_per_core", []))


class MemoryPage(MonitorPage):
    page_title = "Memory"
    page_subtitle = "Physical and virtual memory usage from Windows system telemetry."

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(18)
        gauge_card = SectionCard("Physical memory", "Current pressure on installed RAM.")
        self.gauge = CircularGauge("Memory", "RAM utilization")
        gauge_card.layout.addWidget(self.gauge, 1)
        top.addWidget(gauge_card, 3)
        self.breakdown = SectionCard("Memory breakdown", "Values are retrieved from the local operating system.")
        self.total = InfoRow("Total physical RAM")
        self.used = InfoRow("Used memory")
        self.available = InfoRow("Available memory")
        self.usage = UsageBar("Physical memory")
        for row in (self.total, self.used, self.available):
            self.breakdown.layout.addWidget(row)
        self.breakdown.layout.addSpacing(5)
        self.breakdown.layout.addWidget(self.usage)
        top.addWidget(self.breakdown, 5)
        self.layout.addLayout(top)
        swap = SectionCard("Virtual memory / swap", "Swap is shown only when the operating system reports it.")
        self.swap_total = InfoRow("Swap capacity")
        self.swap_used = InfoRow("Swap used")
        self.swap_bar = UsageBar("Swap usage")
        swap.layout.addWidget(self.swap_total)
        swap.layout.addWidget(self.swap_used)
        swap.layout.addWidget(self.swap_bar)
        self.layout.addWidget(swap)
        modules = SectionCard("Installed memory modules", "DIMM details are retrieved from Windows CIM during hardware discovery.")
        self.module_table = QtWidgets.QTableWidget(0, 5)
        self.module_table.setObjectName("hardwareTable")
        self.module_table.setHorizontalHeaderLabels(("Slot", "Capacity", "Speed", "Manufacturer", "Part number"))
        self.module_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.module_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.module_table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.module_table.setShowGrid(False)
        self.module_table.setMinimumHeight(122)
        self.module_table.verticalHeader().setVisible(False)
        self.module_table.verticalHeader().setDefaultSectionSize(36)
        module_header = self.module_table.horizontalHeader()
        module_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        module_header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Stretch)
        modules.layout.addWidget(self.module_table)
        self.layout.addWidget(modules)
        note = EmptyState("A note about RAM readings", "CorePulse reports the memory definitions returned by psutil and Windows. Cached or standby memory may be accounted for differently by other utilities.")
        self.layout.addWidget(note)
        self.layout.addStretch(1)

    def on_hardware(self, hardware: dict[str, Any]) -> None:
        super().on_hardware(hardware)
        modules = hardware.get("memory_modules", []) or []
        self.module_table.setRowCount(len(modules))
        for row, module in enumerate(modules):
            speed = module.get("speed_mhz")
            values = (
                str(module.get("slot", "Not available on this system.")),
                bytes_to_human(module.get("capacity")),
                f"{speed:,.0f} MHz" if isinstance(speed, (int, float)) else "Not available on this system.",
                str(module.get("manufacturer", "Not available on this system.")),
                str(module.get("part_number", "Not available on this system.")),
            )
            for column, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setToolTip(value)
                self.module_table.setItem(row, column, item)
        if not modules:
            self.module_table.setRowCount(1)
            item = QtWidgets.QTableWidgetItem("Not available on this system.")
            item.setToolTip(item.text())
            self.module_table.setItem(0, 0, item)
            self.module_table.setSpan(0, 0, 1, 5)

    def on_snapshot(self, snapshot: dict[str, Any], history: Sequence[float]) -> None:
        percent = _safe_percent(snapshot.get("memory_percent"))
        total = snapshot.get("memory_total")
        used = snapshot.get("memory_used")
        available = snapshot.get("memory_available")
        swap_percent = _safe_percent(snapshot.get("swap_percent"))
        self.gauge.set_reading(percent, f"{bytes_to_human(available)} available")
        self.total.set_value(bytes_to_human(total))
        self.used.set_value(bytes_to_human(used))
        self.available.set_value(bytes_to_human(available))
        self.usage.set_usage(percent, f"{percent:.0f}% used" if percent is not None else "Not available on this system.")
        self.swap_total.set_value(bytes_to_human(snapshot.get("swap_total")))
        self.swap_used.set_value(bytes_to_human(snapshot.get("swap_used")))
        self.swap_bar.set_usage(swap_percent, f"{swap_percent:.0f}% used" if swap_percent is not None else "Not available on this system.")


class StoragePage(MonitorPage):
    page_title = "Storage"
    page_subtitle = "Mounted local volumes, refreshed safely without blocking the interface."

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        summary = SectionCard("System drive", "Primary system-volume capacity and current free space.")
        self.drive_label = InfoRow("Volume")
        self.drive_capacity = InfoRow("Capacity")
        self.drive_free = InfoRow("Free space")
        self.drive_bar = UsageBar("System drive")
        summary.layout.addWidget(self.drive_label)
        summary.layout.addWidget(self.drive_capacity)
        summary.layout.addWidget(self.drive_free)
        summary.layout.addWidget(self.drive_bar)
        self.layout.addWidget(summary)

        table_card = SectionCard("Mounted volumes", "Inaccessible or permission-restricted volumes are marked instead of causing a refresh failure.")
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setObjectName("storageTable")
        self.table.setHorizontalHeaderLabels(("Volume", "Filesystem", "Total", "Used", "Free", "Usage"))
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(250)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        for col in range(2, 6):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        table_card.layout.addWidget(self.table)
        self.layout.addWidget(table_card)
        physical = SectionCard("Physical storage devices", "Model and transport information discovered through local Windows CIM.")
        self.physical_table = QtWidgets.QTableWidget(0, 5)
        self.physical_table.setObjectName("hardwareTable")
        self.physical_table.setHorizontalHeaderLabels(("Model", "Interface", "Media", "Capacity", "Status"))
        self.physical_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.physical_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.physical_table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.physical_table.setShowGrid(False)
        self.physical_table.setMinimumHeight(115)
        self.physical_table.verticalHeader().setVisible(False)
        self.physical_table.verticalHeader().setDefaultSectionSize(36)
        physical_header = self.physical_table.horizontalHeader()
        physical_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for column in range(1, 5):
            physical_header.setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        physical.layout.addWidget(self.physical_table)
        self.layout.addWidget(physical)
        self.layout.addStretch(1)

    def on_hardware(self, hardware: dict[str, Any]) -> None:
        super().on_hardware(hardware)
        disks = hardware.get("physical_disks", []) or []
        self.physical_table.setRowCount(len(disks))
        for row, disk in enumerate(disks):
            values = (
                str(disk.get("model", "Not available on this system.")),
                str(disk.get("interface", "Not available on this system.")),
                str(disk.get("media_type", "Not available on this system.")),
                bytes_to_human(disk.get("size")),
                str(disk.get("status", "Not available on this system.")),
            )
            for column, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setToolTip(value)
                self.physical_table.setItem(row, column, item)
        if not disks:
            self.physical_table.setRowCount(1)
            item = QtWidgets.QTableWidgetItem("Not available on this system.")
            self.physical_table.setItem(0, 0, item)
            self.physical_table.setSpan(0, 0, 1, 5)

    def on_snapshot(self, snapshot: dict[str, Any], history: Sequence[float]) -> None:
        drive = _safe_percent(snapshot.get("drive_percent"))
        self.drive_label.set_value(snapshot.get("drive_path", "Not available on this system."))
        self.drive_capacity.set_value(bytes_to_human(snapshot.get("drive_total")))
        self.drive_free.set_value(bytes_to_human(snapshot.get("drive_free")))
        self.drive_bar.set_usage(drive, f"{drive:.0f}% used" if drive is not None else "Not available on this system.")
        volumes = snapshot.get("volumes", [])
        self.table.setRowCount(len(volumes))
        for row, volume in enumerate(volumes):
            if volume.get("available"):
                values = (
                    str(volume.get("mount", "")),
                    str(volume.get("filesystem", "Unknown")),
                    bytes_to_human(volume.get("total")),
                    bytes_to_human(volume.get("used")),
                    bytes_to_human(volume.get("free")),
                    f"{float(volume.get('percent', 0)):.0f}%",
                )
            else:
                values = (
                    str(volume.get("mount", "")),
                    str(volume.get("filesystem", "Unknown")),
                    "Unavailable", "Unavailable", "Unavailable", "—",
                )
            for column, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setToolTip(value)
                if column >= 2:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, column, item)


class GraphicsPage(MonitorPage):
    page_title = "Graphics"
    page_subtitle = "Adapter, driver, display, and reported memory information from Windows CIM."

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        intro = SectionCard("Graphics hardware", "Static adapter facts are discovered locally during startup. Values are shown only when Windows reports them.")
        intro_row = QtWidgets.QHBoxLayout()
        self.adapter_count = InfoRow("Detected adapters", "Discovering…")
        self.discovery_source = InfoRow("Discovery source", "Windows CIM / PowerShell")
        intro_row.addWidget(self.adapter_count, 1)
        intro_row.addWidget(self.discovery_source, 1)
        intro.layout.addLayout(intro_row)
        self.layout.addWidget(intro)

        self.adapters_host = QtWidgets.QWidget()
        self.adapters_layout = QtWidgets.QVBoxLayout(self.adapters_host)
        self.adapters_layout.setContentsMargins(0, 0, 0, 0)
        self.adapters_layout.setSpacing(18)
        self.layout.addWidget(self.adapters_host)
        self.telemetry_note = EmptyState(
            "Live GPU metrics are intentionally scoped",
            "CorePulse currently validates graphics hardware through Windows CIM. GPU utilization, temperatures, clocks, fan speeds, and power are not shown because they require a vendor-specific sensor provider that is not bundled with the application.",
        )
        self.layout.addWidget(self.telemetry_note)
        self.layout.addStretch(1)

    def on_hardware(self, hardware: dict[str, Any]) -> None:
        super().on_hardware(hardware)
        adapters = hardware.get("gpu_adapters", []) or []
        self.adapter_count.set_value(str(len(adapters)) if adapters else "Not available on this system.")
        while self.adapters_layout.count():
            item = self.adapters_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not adapters:
            self.adapters_layout.addWidget(EmptyState("No adapter details returned", "Windows CIM did not return graphics-adapter details for this system or account. The rest of CorePulse remains fully functional."))
            return
        for index, adapter in enumerate(adapters, start=1):
            card = SectionCard(f"Adapter {index:02}", "Reported by the local Windows video-controller class.")
            name = QtWidgets.QLabel(str(adapter.get("name", "Not available on this system.")))
            name.setObjectName("gpuName")
            name.setWordWrap(True)
            name.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            card.layout.addWidget(name)
            rows = (
                ("Video processor", adapter.get("video_processor", "Not available on this system.")),
                ("Driver version", adapter.get("driver_version", "Not available on this system.")),
                ("Reported adapter memory", bytes_to_human(adapter.get("adapter_ram"))),
                ("Active display mode", adapter.get("display_mode", "Not available on this system.")),
                ("Device status", adapter.get("status", "Not available on this system.")),
                ("PNP device ID", adapter.get("pnp_device_id", "Not available on this system.")),
            )
            for label, value in rows:
                card.layout.addWidget(InfoRow(label, str(value)))
            self.adapters_layout.addWidget(card)


class SystemPage(MonitorPage):
    page_title = "System"
    page_subtitle = "Device identity and hardware details discovered on this PC."

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(18)
        identity = SectionCard("System identity", "Operating-system details retrieved locally during startup.")
        self.computer = InfoRow("Computer name")
        self.manufacturer = InfoRow("System manufacturer")
        self.model = InfoRow("System model")
        self.os = InfoRow("Operating system")
        self.architecture = InfoRow("Architecture")
        self.system_type = InfoRow("System type")
        self.boot = InfoRow("Boot time")
        for row in (self.computer, self.manufacturer, self.model, self.os, self.architecture, self.system_type, self.boot):
            identity.layout.addWidget(row)
        top.addWidget(identity, 1)
        compute = SectionCard("Compute hardware", "CPU and installed-memory details supplied by local Windows APIs.")
        self.processor = InfoRow("Processor")
        self.cores = InfoRow("Physical cores")
        self.logical = InfoRow("Logical processors")
        self.ram = InfoRow("Installed RAM")
        self.python = InfoRow("Python runtime")
        for row in (self.processor, self.cores, self.logical, self.ram, self.python):
            compute.layout.addWidget(row)
        top.addWidget(compute, 1)
        self.layout.addLayout(top)
        platform_card = SectionCard("Platform & firmware", "Board and BIOS facts are shown only when Windows CIM returns them.")
        platform_row = QtWidgets.QHBoxLayout()
        self.board = InfoRow("Baseboard")
        self.bios = InfoRow("BIOS")
        platform_row.addWidget(self.board, 1)
        platform_row.addWidget(self.bios, 1)
        platform_card.layout.addLayout(platform_row)
        self.layout.addWidget(platform_card)
        graphics = SectionCard("Graphics adapters", "Adapter names are discovered through Windows CIM when it is available. Full driver and display details are available in Graphics.")
        self.graphics_layout = QtWidgets.QVBoxLayout()
        self.graphics_layout.setContentsMargins(0, 2, 0, 0)
        self.graphics_layout.setSpacing(0)
        self.graphics_layout.addWidget(QtWidgets.QLabel("Discovering local graphics adapters…"))
        graphics.layout.addLayout(self.graphics_layout)
        self.layout.addWidget(graphics)
        disclaimer = EmptyState("Telemetry scope", "CorePulse does not infer GPU utilization, GPU temperature, fan speeds, or other values not returned by an implemented local source. Unavailable readings remain clearly labeled.")
        self.layout.addWidget(disclaimer)
        self.layout.addStretch(1)

    def on_hardware(self, hardware: dict[str, Any]) -> None:
        super().on_hardware(hardware)
        self.computer.set_value(hardware.get("computer_name", "Not available on this system."))
        self.manufacturer.set_value(hardware.get("system_manufacturer", "Not available on this system."))
        self.model.set_value(hardware.get("system_model", "Not available on this system."))
        self.os.set_value(hardware.get("operating_system", "Not available on this system."))
        self.architecture.set_value(hardware.get("architecture", "Not available on this system."))
        self.system_type.set_value(hardware.get("system_type", "Not available on this system."))
        self.boot.set_value(format_boot_time(hardware.get("boot_time")))
        self.processor.set_value(hardware.get("processor", "Not available on this system."))
        self.cores.set_value(_number_or_unavailable(hardware.get("physical_cores")))
        self.logical.set_value(_number_or_unavailable(hardware.get("logical_cores")))
        self.ram.set_value(bytes_to_human(hardware.get("installed_ram")))
        self.python.set_value(f"Python {hardware.get('python_version', 'Not available')}")
        self.board.set_value(hardware.get("board", "Not available on this system."))
        self.bios.set_value(hardware.get("bios", "Not available on this system."))
        while self.graphics_layout.count():
            item = self.graphics_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        graphics = hardware.get("graphics") or ["Not available on this system."]
        for index, adapter in enumerate(graphics, start=1):
            self.graphics_layout.addWidget(InfoRow(f"Adapter {index}", str(adapter)))


PAGE_TYPES = (OverviewPage, ProcessorPage, MemoryPage, StoragePage, GraphicsPage, SystemPage)
