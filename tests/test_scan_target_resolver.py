"""掃描目標解析器測試（P2-1）"""
from pathlib import Path

from skill_safety_guard.scan_target_resolver import (
    is_github_url, parse_github_url, resolve_target,
)


def test_simple_repo_url():
    """簡單 repo URL"""
    url = "https://github.com/user/repo"
    assert is_github_url(url)
    info = parse_github_url(url)
    assert info["user"] == "user"
    assert info["repo"] == "repo"
    assert info["is_raw"] is False
    assert info["is_blob"] is False


def test_tree_url():
    """tree URL（含子路徑）"""
    url = "https://github.com/user/repo/tree/main/skills/foo"
    assert is_github_url(url)
    info = parse_github_url(url)
    assert info["user"] == "user"
    assert info["repo"] == "repo"
    assert info["ref"] == "main"
    assert info["path"] == "skills/foo"


def test_blob_url():
    """blob URL（單檔）"""
    url = "https://github.com/user/repo/blob/main/SKILL.md"
    assert is_github_url(url)
    info = parse_github_url(url)
    assert info["is_blob"] is True
    assert info["path"] == "SKILL.md"


def test_raw_url():
    """raw URL"""
    url = "https://raw.githubusercontent.com/user/repo/main/SKILL.md"
    assert is_github_url(url)
    info = parse_github_url(url)
    assert info["is_raw"] is True


def test_non_github_url():
    """非 GitHub URL"""
    assert not is_github_url("https://example.com/foo")
    assert not is_github_url("not a url at all")


def test_resolve_local_path(tmp_path):
    """本地路徑解析"""
    test_file = tmp_path / "test.md"
    test_file.write_text("hello", encoding="utf-8")
    result = resolve_target(str(test_file))
    assert result is not None
    assert result.kind == "local"
    assert result.cleanup is False
