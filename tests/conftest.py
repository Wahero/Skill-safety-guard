"""共用測試配置：確保 src/ 在 Python path 中"""
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
