# CorePulse v1.0.0

> **System Intelligence, at a Glance.**

The first release candidate of CorePulse, a premium Windows system monitor built with Python, PySide6, psutil, and local Windows CIM hardware discovery.

## Highlights

- Premium black-and-orange Windows desktop interface
- Animated CPU and RAM gauges
- Live 60-second processor activity chart
- Real CPU, RAM, swap, uptime, boot-time, frequency, and storage telemetry
- Per-logical-processor utilization when exposed by the operating system
- Dedicated Overview, Processor, Memory, Storage, Graphics, and System pages
- Detailed Windows hardware discovery in a background worker thread
- High-resolution CorePulse application icon and standalone executable build support
- Local-only monitoring with no account, analytics, cloud service, or network telemetry

## Hardware details included

### Processor
- Processor model and manufacturer
- Socket designation
- Physical and logical core counts
- Maximum advertised frequency
- Current frequency when exposed by Windows
- Live overall and per-logical-processor utilization

### Memory
- Total, used, and available physical memory
- Virtual memory / swap usage
- Installed DIMM slot, capacity, speed, manufacturer, and part number when available

### Storage
- Mounted-volume capacity, usage, free space, and filesystem
- Physical-disk model, interface, media type, capacity, and status when available

### Graphics
- Detected Windows graphics adapters
- Adapter name and video processor
- Driver version
- Reported adapter memory
- Active display mode when exposed
- Device status and PNP device identifier

### System
- Computer name, system manufacturer, model, architecture, and system type
- Motherboard and BIOS details when available
- Operating-system details and boot time
- Python runtime information

## Privacy

CorePulse runs entirely on the local computer.

It does not:
- upload system metrics;
- create an account;
- use analytics;
- contact cloud services; or
- make network requests.

Windows hardware discovery uses local PowerShell/CIM queries only.

## Known limitations

- GPU utilization, GPU temperature, fan speed, power, and clock telemetry are intentionally not shown because CorePulse does not yet include a validated vendor-specific GPU sensor provider.
- CPU temperature is shown only when a supported local sensor source is exposed through `psutil`.
- Some removable, encrypted, restricted, or network-mounted volumes may be unavailable.
- CPU-frequency availability depends on Windows, firmware, drivers, and the active power plan.

## Installation

Download `CorePulse.exe` from the release assets and run it on Windows 10 or Windows 11.

No Python installation is required for the packaged executable.

## Feedback

Please open an issue with:
- Windows version;
- CorePulse version;
- hardware configuration;
- reproduction steps; and
- screenshots or error details when appropriate.
