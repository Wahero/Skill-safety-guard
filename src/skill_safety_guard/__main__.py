"""Entry point: python -m skill_safety_guard"""
import sys


def _setup_utf8_stdio():
    """Windows 終端 GBK 兼容性：強制 UTF-8 輸出，避免報告中的 emoji 觸發 UnicodeEncodeError."""
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


from .cli import main

if __name__ == "__main__":
    _setup_utf8_stdio()
    main()
