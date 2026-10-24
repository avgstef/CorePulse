"""Small formatting and packaged-resource helpers for CorePulse."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


APP_NAME = "CorePulse"
ACCENT = "#FF8126"
ACCENT_SOFT = "#FFB16E"
BACKGROUND = "#08090B"
SIDEBAR = "#0D0F12"
CARD = "#111419"
SURFACE = "#171B21"
BORDER = "#2A3039"
TEXT = "#F4F5F7"
MUTED = "#929BA8"
SUCCESS = "#67D391"
DANGER = "#F16D75"


def resource_path(relative_path: str) -> str:
    """Return an asset path that works both from source and PyInstaller."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base / relative_path)


def bytes_to_human(value: float | int | None) -> str:
    """Format a byte value without pretending missing values are measurements."""
    if value is None:
        return "Not available"
    value = float(value)
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{value:.0f} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return "Not available"


def uptime_text(seconds: float | int | None) -> str:
    if seconds is None or seconds < 0:
        return "Not available"
    duration = timedelta(seconds=int(seconds))
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes = remainder // 60
    if days:
        return f"{days}d {hours:02}h {minutes:02}m"
    return f"{hours:02}h {minutes:02}m"


def format_boot_time(timestamp: float | int | None) -> str:
    if not timestamp:
        return "Not available"
    try:
        return datetime.fromtimestamp(timestamp).strftime("%d %b %Y, %H:%M")
    except (OSError, OverflowError, ValueError):
        return "Not available"


def system_drive_path() -> str:
    """Get Windows' selected system drive; use root when running elsewhere."""
    if os.name == "nt":
        return os.environ.get("SystemDrive", "C:") + "\\"
    return os.path.abspath(os.sep)


def compact_name(value: str, max_length: int = 46) -> str:
    """Create a display-friendly label while retaining full text in a tooltip."""
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"
