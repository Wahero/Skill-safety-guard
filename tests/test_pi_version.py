"""V-03: Pi Agent 版本 CVE 檢測測試（P2-2）

測試 _parse_version 和 _is_below 的版本比較邏輯。
"""
from skill_safety_guard.pi_check.version import _parse_version, _is_below, KNOWN_CVES


def test_parse_version_standard():
    """標準版本號解析"""
    assert _parse_version("0.81.0") == (0, 81, 0)
    assert _parse_version("1.2.3") == (1, 2, 3)
    assert _parse_version("0.84.0") == (0, 84, 0)


def test_parse_version_no_patch():
    """無 patch 號的版本"""
    assert _parse_version("0.81") == (0, 81, 0)
    assert _parse_version("1.2") == (1, 2, 0)


def test_parse_version_invalid():
    """無效版本號返回 (0, 0, 0)"""
    assert _parse_version("invalid") == (0, 0, 0)
    assert _parse_version("") == (0, 0, 0)


def test_is_below_true():
    """0.81.0 < 0.82.0 → True（CVE-2026-54326 命中）"""
    assert _is_below((0, 81, 0), "0.82.0") is True
    assert _is_below((0, 81, 0), "0.84.0") is True


def test_is_below_equal():
    """0.82.0 不低於 0.82.0 → False"""
    assert _is_below((0, 82, 0), "0.82.0") is False


def test_is_below_above():
    """0.86.0 不低於 0.85.0 → False（不命中任何 CVE）"""
    assert _is_below((0, 86, 0), "0.85.0") is False
    assert _is_below((0, 86, 0), "0.82.0") is False


def test_cve_coverage():
    """確認已知 CVE 的 affected_below 邊界正確"""
    # CVE-2026-54326: < 0.82.0
    cve_54326 = [c for c in KNOWN_CVES if c["cve_id"] == "CVE-2026-54326"][0]
    assert _is_below((0, 81, 0), cve_54326["affected_below"]) is True
    assert _is_below((0, 82, 0), cve_54326["affected_below"]) is False

    # CVE-2026-54327: < 0.85.0
    cve_54327 = [c for c in KNOWN_CVES if c["cve_id"] == "CVE-2026-54327"][0]
    assert _is_below((0, 84, 0), cve_54327["affected_below"]) is True
    assert _is_below((0, 85, 0), cve_54327["affected_below"]) is False
