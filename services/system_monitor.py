"""Non-blocking local system telemetry for CorePulse.

Only values returned by local operating-system APIs are exposed.  Failures turn into
an explicit unavailable state rather than a synthetic reading.
"""
from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime
from typing import Any

import psutil
from PySide6 import QtCore

from utils import system_drive_path


UNAVAILABLE = "Not available on this system."


def _safe(callable_, fallback=None):
    try:
        return callable_()
    except (psutil.Error, OSError, ValueError, AttributeError):
        return fallback


def _temperature_reading() -> float | None:
    """Return a real sensor temperature when psutil exposes one, otherwise None."""
    sensors = _safe(lambda: psutil.sensors_temperatures(fahrenheit=False), {}) or {}
    preferred = ("coretemp", "k10temp", "cpu_thermal", "acpitz")
    groups = [sensors[key] for key in preferred if key in sensors]
    groups.extend(group for key, group in sensors.items() if key not in preferred)
    readings: list[float] = []
    for entries in groups:
        for entry in entries:
            current = getattr(entry, "current", None)
            if current is not None and -20 < current < 150:
                readings.append(float(current))
    return max(readings) if readings else None


def _powershell_value(command: str, timeout: int = 7) -> list[str]:
    """Read a Windows CIM value without introducing a WMI Python dependency."""
    if os.name != "nt":
        return []
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=creationflags,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _as_list(value: Any) -> list[dict[str, Any]]:
    """Normalise a PowerShell JSON object (one item) or array to a list of dicts."""
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _powershell_json(command: str, timeout: int = 11) -> dict[str, Any]:
    """Run a bounded local CIM query and decode its deliberately compact JSON output."""
    lines = _powershell_value(command, timeout=timeout)
    if not lines:
        return {}
    try:
        result = json.loads("\n".join(lines))
    except json.JSONDecodeError:
        return {}
    return result if isinstance(result, dict) else {}


def _windows_hardware_details() -> dict[str, Any]:
    """Return detailed Windows CIM facts in one background PowerShell process.

    Values are intentionally static discovery data—not claimed as live sensor data.
    A failed CIM query simply returns an empty mapping so callers can show unavailable
    states without compromising monitoring.
    """
    if os.name != "nt":
        return {}
    command = (
        "$ErrorActionPreference='Stop'; "
        "$cpu=@(Get-CimInstance Win32_Processor | Select-Object -First 1 "
        "Name,Manufacturer,MaxClockSpeed,SocketDesignation,NumberOfCores,NumberOfLogicalProcessors); "
        "$gpu=@(Get-CimInstance Win32_VideoController | Select-Object "
        "Name,AdapterRAM,DriverVersion,VideoProcessor,CurrentHorizontalResolution,"
        "CurrentVerticalResolution,CurrentRefreshRate,VideoModeDescription,Status,PNPDeviceID); "
        "$ram=@(Get-CimInstance Win32_PhysicalMemory | Select-Object "
        "BankLabel,DeviceLocator,Capacity,Speed,ConfiguredClockSpeed,Manufacturer,PartNumber); "
        "$board=Get-CimInstance Win32_BaseBoard | Select-Object -First 1 Manufacturer,Product,Version; "
        "$bios=Get-CimInstance Win32_BIOS | Select-Object -First 1 Manufacturer,SMBIOSBIOSVersion,ReleaseDate; "
        "$computer=Get-CimInstance Win32_ComputerSystem | Select-Object -First 1 Manufacturer,Model,SystemType; "
        "$disks=@(Get-CimInstance Win32_DiskDrive | Select-Object Model,InterfaceType,MediaType,Size,Status); "
        "[PSCustomObject]@{cpu=$cpu[0];gpus=$gpu;memory_modules=$ram;baseboard=$board;"
        "bios=$bios;computer=$computer;disks=$disks} | ConvertTo-Json -Depth 4 -Compress"
    )
    raw = _powershell_json(command)
    if not raw:
        return {}

    cpu_raw = raw.get("cpu") if isinstance(raw.get("cpu"), dict) else {}
    cpu = {
        "name": str(cpu_raw.get("Name") or "").strip() or UNAVAILABLE,
        "manufacturer": str(cpu_raw.get("Manufacturer") or "").strip() or UNAVAILABLE,
        "max_clock_mhz": _as_int(cpu_raw.get("MaxClockSpeed")),
        "socket": str(cpu_raw.get("SocketDesignation") or "").strip() or UNAVAILABLE,
    }
    gpus: list[dict[str, Any]] = []
    for raw_gpu in _as_list(raw.get("gpus")):
        name = str(raw_gpu.get("Name") or "").strip()
        if not name:
            continue
        width = _as_int(raw_gpu.get("CurrentHorizontalResolution"))
        height = _as_int(raw_gpu.get("CurrentVerticalResolution"))
        refresh = _as_int(raw_gpu.get("CurrentRefreshRate"))
        if width and height:
            display_mode = f"{width} × {height}" + (f" @ {refresh} Hz" if refresh else "")
        else:
            display_mode = str(raw_gpu.get("VideoModeDescription") or "").strip() or UNAVAILABLE
        adapter_ram = _as_int(raw_gpu.get("AdapterRAM"))
        gpus.append(
            {
                "name": name,
                "driver_version": str(raw_gpu.get("DriverVersion") or "").strip() or UNAVAILABLE,
                "video_processor": str(raw_gpu.get("VideoProcessor") or "").strip() or UNAVAILABLE,
                "adapter_ram": adapter_ram if adapter_ram and adapter_ram > 0 else None,
                "display_mode": display_mode,
                "status": str(raw_gpu.get("Status") or "").strip() or UNAVAILABLE,
                "pnp_device_id": str(raw_gpu.get("PNPDeviceID") or "").strip() or UNAVAILABLE,
            }
        )
    memory_modules: list[dict[str, Any]] = []
    for raw_module in _as_list(raw.get("memory_modules")):
        capacity = _as_int(raw_module.get("Capacity"))
        memory_modules.append(
            {
                "slot": str(raw_module.get("DeviceLocator") or raw_module.get("BankLabel") or "").strip() or UNAVAILABLE,
                "capacity": capacity if capacity and capacity > 0 else None,
                "speed_mhz": _as_int(raw_module.get("ConfiguredClockSpeed")) or _as_int(raw_module.get("Speed")),
                "manufacturer": str(raw_module.get("Manufacturer") or "").strip() or UNAVAILABLE,
                "part_number": str(raw_module.get("PartNumber") or "").strip() or UNAVAILABLE,
            }
        )
    physical_disks: list[dict[str, Any]] = []
    for raw_disk in _as_list(raw.get("disks")):
        physical_disks.append(
            {
                "model": str(raw_disk.get("Model") or "").strip() or UNAVAILABLE,
                "interface": str(raw_disk.get("InterfaceType") or "").strip() or UNAVAILABLE,
                "media_type": str(raw_disk.get("MediaType") or "").strip() or UNAVAILABLE,
                "size": _as_int(raw_disk.get("Size")),
                "status": str(raw_disk.get("Status") or "").strip() or UNAVAILABLE,
            }
        )
    board_raw = raw.get("baseboard") if isinstance(raw.get("baseboard"), dict) else {}
    bios_raw = raw.get("bios") if isinstance(raw.get("bios"), dict) else {}
    computer_raw = raw.get("computer") if isinstance(raw.get("computer"), dict) else {}
    return {
        "cpu": cpu,
        "gpus": gpus,
        "memory_modules": memory_modules,
        "physical_disks": physical_disks,
        "system_manufacturer": str(computer_raw.get("Manufacturer") or "").strip() or UNAVAILABLE,
        "system_model": str(computer_raw.get("Model") or "").strip() or UNAVAILABLE,
        "system_type": str(computer_raw.get("SystemType") or "").strip() or UNAVAILABLE,
        "board": " ".join(
            part for part in (str(board_raw.get("Manufacturer") or "").strip(), str(board_raw.get("Product") or "").strip()) if part
        ) or UNAVAILABLE,
        "bios": " ".join(
            part for part in (str(bios_raw.get("Manufacturer") or "").strip(), str(bios_raw.get("SMBIOSBIOSVersion") or "").strip()) if part
        ) or UNAVAILABLE,
    }


def _storage_volumes() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    partitions = _safe(lambda: psutil.disk_partitions(all=False), []) or []
    for partition in partitions:
        mount = partition.mountpoint or partition.device
        if not mount or mount in seen:
            continue
        seen.add(mount)
        usage = _safe(lambda mount=mount: psutil.disk_usage(mount))
        if usage is None:
            rows.append(
                {
                    "mount": mount,
                    "device": partition.device or mount,
                    "filesystem": partition.fstype or "Unknown",
                    "total": None,
                    "used": None,
                    "free": None,
                    "percent": None,
                    "available": False,
                }
            )
            continue
        rows.append(
            {
                "mount": mount,
                "device": partition.device or mount,
                "filesystem": partition.fstype or "Unknown",
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
                "available": True,
            }
        )
    return rows


class MonitorWorker(QtCore.QObject):
    """Samples fast metrics in its own event-loop thread once per second."""

    snapshot_ready = QtCore.Signal(dict)
    monitor_error = QtCore.Signal(str)

    def __init__(self, interval_ms: int = 1000) -> None:
        super().__init__()
        self._interval_ms = interval_ms
        self._timer: QtCore.QTimer | None = None
        self._last_frequency_sample = 0.0
        self._cached_frequency: float | None = None

    @QtCore.Slot()
    def start(self) -> None:
        # Prime psutil's non-blocking CPU percentage baseline.
        _safe(lambda: psutil.cpu_percent(interval=None), 0.0)
        _safe(lambda: psutil.cpu_percent(interval=None, percpu=True), [])
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self._interval_ms)
        self._timer.timeout.connect(self.sample)
        self._timer.start()
        self.sample()

    @QtCore.Slot()
    def stop(self) -> None:
        if self._timer is not None:
            self._timer.stop()

    @QtCore.Slot()
    def sample(self) -> None:
        try:
            memory = _safe(psutil.virtual_memory)
            swap = _safe(psutil.swap_memory)
            drive_path = system_drive_path()
            drive = _safe(lambda: psutil.disk_usage(drive_path))
            boot_time = _safe(psutil.boot_time)
            now = time.monotonic()
            if now - self._last_frequency_sample > 4.5:
                frequency = _safe(psutil.cpu_freq)
                self._cached_frequency = float(frequency.current) if frequency else None
                self._last_frequency_sample = now

            snapshot: dict[str, Any] = {
                "cpu_percent": float(_safe(lambda: psutil.cpu_percent(interval=None), 0.0) or 0.0),
                "cpu_per_core": _safe(lambda: psutil.cpu_percent(interval=None, percpu=True), []) or [],
                "memory_total": getattr(memory, "total", None),
                "memory_used": getattr(memory, "used", None),
                "memory_available": getattr(memory, "available", None),
                "memory_percent": float(getattr(memory, "percent", 0.0) or 0.0),
                "swap_total": getattr(swap, "total", None),
                "swap_used": getattr(swap, "used", None),
                "swap_percent": float(getattr(swap, "percent", 0.0) or 0.0),
                "drive_path": drive_path,
                "drive_total": getattr(drive, "total", None),
                "drive_used": getattr(drive, "used", None),
                "drive_free": getattr(drive, "free", None),
                "drive_percent": getattr(drive, "percent", None),
                "uptime_seconds": time.time() - boot_time if boot_time else None,
                "boot_time": boot_time,
                "cpu_frequency": self._cached_frequency,
                "temperature": _temperature_reading(),
                "volumes": _storage_volumes(),
                "sampled_at": datetime.now(),
            }
            self.snapshot_ready.emit(snapshot)
        except Exception as exc:  # Guard a background failure without crashing the UI.
            self.monitor_error.emit(f"Monitoring refresh failed: {exc}")


class HardwareWorker(QtCore.QObject):
    """Performs slower startup hardware discovery outside the GUI thread."""

    hardware_ready = QtCore.Signal(dict)

    @QtCore.Slot()
    def collect(self) -> None:
        try:
            uname = platform.uname()
            physical = _safe(lambda: psutil.cpu_count(logical=False))
            logical = _safe(lambda: psutil.cpu_count(logical=True))
            memory = _safe(psutil.virtual_memory)
            system_name = platform.system()
            release = platform.release()
            version = platform.version()
            windows = _windows_hardware_details()
            cpu_details = windows.get("cpu", {})
            gpu_adapters = windows.get("gpus", [])
            graphics = [str(adapter.get("name")) for adapter in gpu_adapters if adapter.get("name")]
            details: dict[str, Any] = {
                "computer_name": socket.gethostname() or UNAVAILABLE,
                "operating_system": f"{system_name} {release}".strip() or UNAVAILABLE,
                "os_version": version or UNAVAILABLE,
                "architecture": platform.machine() or UNAVAILABLE,
                "processor": cpu_details.get("name") or platform.processor().strip() or UNAVAILABLE,
                "processor_details": cpu_details,
                "physical_cores": physical if physical is not None else UNAVAILABLE,
                "logical_cores": logical if logical is not None else UNAVAILABLE,
                "installed_ram": getattr(memory, "total", None),
                "graphics": graphics or [UNAVAILABLE],
                "gpu_adapters": gpu_adapters,
                "memory_modules": windows.get("memory_modules", []),
                "physical_disks": windows.get("physical_disks", []),
                "system_manufacturer": windows.get("system_manufacturer", UNAVAILABLE),
                "system_model": windows.get("system_model", UNAVAILABLE),
                "system_type": windows.get("system_type", UNAVAILABLE),
                "board": windows.get("board", UNAVAILABLE),
                "bios": windows.get("bios", UNAVAILABLE),
                "python_version": platform.python_version(),
                "boot_time": _safe(psutil.boot_time),
                "platform_node": uname.node or UNAVAILABLE,
            }
        except Exception:
            # A failed optional discovery must never leave the pages in a fake state.
            details = {
                "computer_name": UNAVAILABLE,
                "operating_system": UNAVAILABLE,
                "os_version": UNAVAILABLE,
                "architecture": UNAVAILABLE,
                "processor": UNAVAILABLE,
                "processor_details": {},
                "physical_cores": UNAVAILABLE,
                "logical_cores": UNAVAILABLE,
                "installed_ram": None,
                "graphics": [UNAVAILABLE],
                "gpu_adapters": [],
                "memory_modules": [],
                "physical_disks": [],
                "system_manufacturer": UNAVAILABLE,
                "system_model": UNAVAILABLE,
                "system_type": UNAVAILABLE,
                "board": UNAVAILABLE,
                "bios": UNAVAILABLE,
                "python_version": platform.python_version(),
                "boot_time": None,
                "platform_node": UNAVAILABLE,
            }
        self.hardware_ready.emit(details)
