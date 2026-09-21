#!/usr/bin/env python3
"""Remove EN/DE catch-all 301s and restore Polylang en_GB + de_DE. Do not publish empty drafts."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "i18n-clone-translate.py")


def main() -> int:
    os.execv(sys.executable, [sys.executable, SCRIPT, "--restore-langs", *sys.argv[1:]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
