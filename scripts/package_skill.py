#!/usr/bin/env python3
"""打包通用 Agent Skills 規範的 zip：dist/skill-safety-guard.zip。

zip 內是單一頂層資料夾 `skill-safety-guard/`，SKILL.md 位於該資料夾根層，
只含運行必需文件（SKILL.md + scripts/ + src/ + 文檔），不含開發文件
（tests/ demo/ web/ .github/ memory/ 等），可直接上傳 claude.ai
或匯入任何支援 zip 安裝的環境。
"""
from __future__ import annotations

import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "skill-safety-guard"
DIST_DIR = REPO_ROOT / "dist"

# 運行必需 + 用戶文檔；其餘（tests/demo/web/extension/.github/memory 等）為開發文件
# 注意：不放 package.json——其 pi manifest（skills + extensions）會讓部分平台的
# 上傳檢查誤判「多個入口」；package.json 僅服務 pi install / npm 分發。
INCLUDE_FILES = [
    "SKILL.md",
    "README.md",
    "USAGE.md",
    "CHANGELOG.md",
    "LICENSE",
]
INCLUDE_DIRS = ["scripts", "src"]
EXCLUDE_SUFFIXES = {".pyc"}
EXCLUDE_DIR_NAMES = {"__pycache__", ".pytest_cache"}


def iter_files(base: Path):
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix in EXCLUDE_SUFFIXES:
            continue
        if any(part in EXCLUDE_DIR_NAMES for part in p.relative_to(base).parts):
            continue
        yield p


def main() -> int:
    DIST_DIR.mkdir(exist_ok=True)
    out_path = DIST_DIR / f"{SKILL_NAME}.zip"
    count = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in INCLUDE_FILES:
            f = REPO_ROOT / name
            if f.exists():
                zf.write(f, f"{SKILL_NAME}/{name}")
                count += 1
        for d in INCLUDE_DIRS:
            for f in iter_files(REPO_ROOT / d):
                zf.write(f, f"{SKILL_NAME}/{d}/{f.relative_to(REPO_ROOT / d)}")
                count += 1
    size_kb = out_path.stat().st_size / 1024
    print(f"✅ {out_path.relative_to(REPO_ROOT)}（{count} 個文件，{size_kb:.0f} KB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
