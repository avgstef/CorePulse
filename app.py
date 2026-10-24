"""CorePulse application entry point."""
from __future__ import annotations

import sys

from ui.main_window import MainWindow, create_application


def main() -> int:
    app = create_application()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
