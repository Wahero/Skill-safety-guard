"""許可證系統測試（P2-1）"""
from skill_safety_guard.license import (
    verify_license_key, generate_license_key, can_scan, record_scan,
)


def test_verify_invalid_key():
    """無效密鑰"""
    assert verify_license_key("") is False
    assert verify_license_key("invalid-key") is False
    assert verify_license_key("ssg-pro-invalid") is False


def test_generate_and_verify():
    """生成並驗證密鑰"""
    key = generate_license_key()
    assert key.startswith("ssg-pro-")
    assert verify_license_key(key) is True


def test_can_scan_free_tier(monkeypatch, tmp_path):
    """Free 層可掃描（5 次額度）"""
    import skill_safety_guard.license as lic
    monkeypatch.setattr(lic, "LICENSE_FILE", tmp_path / "license.json")
    monkeypatch.setattr(lic, "USAGE_FILE", tmp_path / "usage.json")

    can, info = can_scan()
    assert can is True
    assert info["tier"] == "free"
    assert info["remaining"] == 5


def test_record_scan_increments(monkeypatch, tmp_path):
    """記錄掃描後剩餘次數遞減"""
    import skill_safety_guard.license as lic
    monkeypatch.setattr(lic, "LICENSE_FILE", tmp_path / "license.json")
    monkeypatch.setattr(lic, "USAGE_FILE", tmp_path / "usage.json")

    record_scan()
    can, info = can_scan()
    assert info["remaining"] == 4

    record_scan()
    can, info = can_scan()
    assert info["remaining"] == 3
