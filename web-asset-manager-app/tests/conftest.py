from __future__ import annotations

import os
import sys


def pytest_configure() -> None:
    root = os.path.dirname(os.path.dirname(__file__))
    src_path = os.path.join(root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
