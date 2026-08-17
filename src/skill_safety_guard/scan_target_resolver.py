"""掃描目標解析器（F-007~F-010 殺手場景）

支援輸入：
- 本地路徑：D:/my-skill 或 ./my-skill
- GitHub URL：https://github.com/user/repo
- GitHub URL 含路徑：https://github.com/user/repo/tree/main/skills/foo
- 粘貼內容：從 stdin 讀取
- Skill 註冊名：community/foo（暫不實現，留作 v1.1）
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple, NamedTuple
from urllib.parse import urlparse


class ScanTarget(NamedTuple):
    """解析後的掃描目標"""
    kind: str  # "local" / "github" / "paste" / "url-raw"
    path: Path  # 本地路徑（temp dir 或真實路徑）
    display_name: str  # 給用戶看的名稱
    cleanup: bool = False  # 是否需要在掃描後清理（temp dir）


# GitHub URL 模式
GITHUB_URL_PATTERNS = [
    # https://github.com/user/repo
    r"^https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$",
    # https://github.com/user/repo/tree/branch/path
    r"^https?://github\.com/([\w.-]+)/([\w.-]+)/tree/([^/]+)(?:/(.+))?/?$",
    # https://github.com/user/repo/blob/branch/path
    r"^https?://github\.com/([\w.-]+)/([\w.-]+)/blob/([^/]+)(?:/(.+))?/?$",
    # raw.githubusercontent.com
    r"^https?://raw\.githubusercontent\.com/([\w.-]+)/([\w.-]+)/([^/]+)(?:/(.+))?/?$",
]


def is_github_url(target: str) -> bool:
    """判斷是否為 GitHub URL"""
    return any(re.match(p, target) for p in GITHUB_URL_PATTERNS)


def parse_github_url(url: str) -> Optional[dict]:
    """解析 GitHub URL

    返回：
    {
        "user": str,
        "repo": str,
        "ref": str,  # branch/tag
        "path": str,  # subdirectory within repo (optional)
        "is_raw": bool,
        "is_blob": bool,
    }
    """
    # Repo URL
    m = re.match(GITHUB_URL_PATTERNS[0], url)
    if m:
        return {
            "user": m.group(1),
            "repo": m.group(2),
            "ref": "HEAD",  # 默認分支
            "path": "",
            "is_raw": False,
            "is_blob": False,
        }

    # tree URL
    m = re.match(GITHUB_URL_PATTERNS[1], url)
    if m:
        return {
            "user": m.group(1),
            "repo": m.group(2),
            "ref": m.group(3),
            "path": m.group(4) or "",
            "is_raw": False,
            "is_blob": False,
        }

    # blob URL
    m = re.match(GITHUB_URL_PATTERNS[2], url)
    if m:
        return {
            "user": m.group(1),
            "repo": m.group(2),
            "ref": m.group(3),
            "path": m.group(4) or "",
            "is_raw": False,
            "is_blob": True,
        }

    # raw URL
    m = re.match(GITHUB_URL_PATTERNS[3], url)
    if m:
        return {
            "user": m.group(1),
            "repo": m.group(2),
            "ref": m.group(3),
            "path": m.group(4) or "",
            "is_raw": True,
            "is_blob": False,
        }

    return None


def fetch_github_repo(user: str, repo: str, ref: str = "HEAD", sub_path: str = "") -> Optional[Path]:
    """從 GitHub 下載整個 repo（或子目錄）到臨時目錄

    返回：本地臨時目錄路徑（如果是子路徑，只返回該子路徑的內容）
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"safety-scan-{repo}-"))

    # 簡化策略：完整淺 clone，之後只保留需要的子路徑
    cmd = [
        "git", "clone",
        "--depth=1",
        f"https://github.com/{user}/{repo}.git",
        str(tmp_dir),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return None

        # 如果指定了子路徑，只保留該子路徑
        if sub_path:
            target_dir = tmp_dir / sub_path
            if not target_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)
                return None
            # 把子路徑的內容移到新的 temp dir
            scan_dir = Path(tempfile.mkdtemp(prefix=f"safety-scan-{repo}-sub-"))
            for item in target_dir.iterdir():
                shutil.move(str(item), str(scan_dir))
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return scan_dir

        return tmp_dir
    except subprocess.TimeoutExpired:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None


def fetch_github_file(user: str, repo: str, ref: str, file_path: str) -> Optional[Path]:
    """從 GitHub 下載單個文件到臨時位置

    適用於 blob URL（單個 SKILL.md）
    """
    raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{ref}/{file_path}"

    try:
        import urllib.request

        with urllib.request.urlopen(raw_url, timeout=15) as resp:
            content = resp.read()

        # 創建臨時目錄 + 文件
        tmp_dir = Path(tempfile.mkdtemp(prefix=f"safety-scan-file-"))
        target = tmp_dir / Path(file_path).name
        target.write_bytes(content)
        return tmp_dir
    except Exception:
        return None


def resolve_paste(content: str) -> Optional[Path]:
    """將粘貼的內容保存到臨時文件，返回臨時目錄"""
    if not content or not content.strip():
        return None

    tmp_dir = Path(tempfile.mkdtemp(prefix="safety-scan-paste-"))
    target = tmp_dir / "SKILL.md"

    # 如果內容看起來像 SKILL.md，直接保存
    # 否則包裝成 SKILL.md
    if content.startswith("---\n") or content.startswith("---\r\n"):
        target.write_text(content, encoding="utf-8")
    else:
        # 包裝成 SKILL.md 格式
        wrapped = f"""---
name: pasted-content
description: 用戶粘貼的內容（未命名）
allowed-tools: [read]
---

{content}
"""
        target.write_text(wrapped, encoding="utf-8")

    return tmp_dir


def resolve_target(target: str) -> Optional[ScanTarget]:
    """解析掃描目標，返回 ScanTarget

    target 可以是：
    - 本地路徑
    - GitHub URL
    - "paste" 關鍵字（讀 stdin）
    """
    # 1. stdin 粘貼
    if target == "paste" or target == "-":
        if not sys.stdin.isatty():
            content = sys.stdin.read()
            path = resolve_paste(content)
            if path:
                return ScanTarget(
                    kind="paste",
                    path=path,
                    display_name="粘貼內容",
                    cleanup=True,
                )
            return None
        else:
            return None

    # 2. GitHub URL
    if is_github_url(target):
        info = parse_github_url(target)
        if info is None:
            return None

        display = f"github.com/{info['user']}/{info['repo']}"
        if info["path"]:
            display += f"/{info['path']}"

        # blob URL 或 raw URL → 下載單個文件
        if info["is_blob"] or info["is_raw"]:
            file_path = info["path"]
            tmp = fetch_github_file(info["user"], info["repo"], info["ref"], file_path)
            if tmp:
                return ScanTarget(
                    kind="github-blob" if info["is_blob"] else "github-raw",
                    path=tmp,
                    display_name=display,
                    cleanup=True,
                )
            return None

        # 普通 URL → 下載整個 repo（或 sparse 子目錄）
        tmp = fetch_github_repo(info["user"], info["repo"], info["ref"], info["path"])
        if tmp:
            return ScanTarget(
                kind="github",
                path=tmp,
                display_name=display,
                cleanup=True,
            )
        return None

    # 3. 本地路徑
    local_path = Path(target).resolve()
    if local_path.exists():
        return ScanTarget(
            kind="local",
            path=local_path,
            display_name=str(local_path),
            cleanup=False,
        )

    return None


def cleanup_target(target: ScanTarget) -> None:
    """清理臨時目錄（如果是臨時的）"""
    if target.cleanup and target.path.exists():
        import shutil

        try:
            shutil.rmtree(target.path, ignore_errors=True)
        except Exception:
            pass