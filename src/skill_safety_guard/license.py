"""Freemium 許可證系統（F-033~F-036）

設計理念：
- 離線驗證（不需要網路請求）
- HMAC 簽名防偽造
- 本地使用計數（每週 5 次免費）
- Pro 用戶無限制

許可證密鑰格式：ssg-pro-XXXX-XXXX-XXXX-XXXX
其中 XXXX 為 base32 編碼的隨機字節
- 前 16 字節：HMAC 校驗數據
- 後 16 字節：HMAC 簽名（用 SECRET_KEY 計算）

本系統使用固定的 SECRET_KEY（演示用）。
生產環境應使用：
  - 環境變量 SSG_LICENSE_SECRET
  - 或從 license server 獲取公鑰進行驗證
"""
import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


# ⚠️ 演示用 SECRET_KEY。實際部署應使用環境變量或 KMS。
SECRET_KEY = os.environ.get(
    "SSG_LICENSE_SECRET",
    "skill-safety-guard-demo-secret-DO-NOT-USE-IN-PRODUCTION-2026",
).encode()

# 免費層限制
FREE_SCANS_PER_WEEK = 5
PRO_PRICE_MONTHLY_USD = 4.99
PRO_PRICE_YEARLY_USD = 39.00

LICENSE_FILE = Path.home() / ".skill-safety-guard" / "license.json"
USAGE_FILE = Path.home() / ".skill-safety-guard" / "usage.json"


@dataclass
class License:
    """許可證數據結構"""
    tier: str  # "free" / "pro"
    key: Optional[str]  # 原始密鑰（Pro 用戶）
    activated_at: float  # 激活時間戳
    expires_at: Optional[float]  # 過期時間（None = 永久）

    def is_valid(self) -> bool:
        """檢查許可證是否有效"""
        if self.tier == "free":
            return True
        if self.expires_at is None:
            return True
        return time.time() < self.expires_at

    def is_pro(self) -> bool:
        return self.tier == "pro" and self.is_valid()


def generate_license_key(plan: str = "monthly") -> str:
    """生成 Pro 許可證密鑰（用於測試 / demo）

    base32 編碼規則：
    - 10 字節隨機數據 + 10 字節 HMAC 簽名 = 20 字節 payload
    - base32(20 bytes) = 32 chars → 8 組 XXXX
    """
    # 10 字節隨機數據
    import secrets
    random_bytes = secrets.token_bytes(10)

    # 計算 HMAC（取 10 字節）
    signature = hmac.new(SECRET_KEY, random_bytes, hashlib.sha256).digest()[:10]

    # 拼接 + base32 編碼
    payload = random_bytes + signature
    encoded = base64.b32encode(payload).decode().rstrip("=")

    # 格式化為 XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX（8 組）
    parts = [encoded[i:i+4] for i in range(0, len(encoded), 4)]
    key = "ssg-pro-" + "-".join(parts)

    return key


def verify_license_key(key: str) -> bool:
    """驗證 Pro 許可證密鑰"""
    if not key.startswith("ssg-pro-"):
        return False

    # 提取編碼部分
    encoded = key.replace("ssg-pro-", "").replace("-", "")

    try:
        payload = base64.b32decode(encoded + "=" * (-len(encoded) % 8))
    except Exception:
        return False

    if len(payload) != 20:
        return False

    random_bytes = payload[:10]
    signature = payload[10:]

    # 驗證簽名
    expected_signature = hmac.new(SECRET_KEY, random_bytes, hashlib.sha256).digest()[:10]
    return hmac.compare_digest(signature, expected_signature)


def activate_license(key: str, plan: str = "monthly") -> License:
    """激活 Pro 許可證"""
    if not verify_license_key(key):
        raise ValueError(f"Invalid license key: {key}")

    if plan == "yearly":
        expires_at = time.time() + 365 * 24 * 3600
    else:  # monthly
        expires_at = time.time() + 30 * 24 * 3600

    license = License(
        tier="pro",
        key=key,
        activated_at=time.time(),
        expires_at=expires_at,
    )
    save_license(license)
    return license


def save_license(license: License) -> None:
    """保存許可證到磁盤"""
    LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(asdict(license), f, indent=2)


def load_license() -> License:
    """加載許可證。如果沒有則返回 free"""
    if not LICENSE_FILE.exists():
        return License(tier="free", key=None, activated_at=time.time(), expires_at=None)

    try:
        with open(LICENSE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return License(**data)
    except Exception:
        return License(tier="free", key=None, activated_at=time.time(), expires_at=None)


def load_usage() -> dict:
    """加載使用計數"""
    if not USAGE_FILE.exists():
        return {"week_start": 0, "scans": 0}

    try:
        with open(USAGE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"week_start": 0, "scans": 0}


def save_usage(usage: dict) -> None:
    """保存使用計數"""
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(usage, f, indent=2)


def get_week_start() -> float:
    """獲取本週開始時間（週一 00:00 UTC）"""
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    week_start = now - datetime.timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    return week_start.timestamp()


def can_scan() -> tuple[bool, dict]:
    """檢查用戶是否可以掃描（基於許可證和使用計數）

    返回：(can_scan, info_dict)
    """
    license = load_license()

    # Pro 用戶無限制
    if license.is_pro():
        return True, {
            "tier": "pro",
            "remaining": "unlimited",
            "expires_at": license.expires_at,
        }

    # Free 用戶檢查本週計數
    usage = load_usage()
    week_start = get_week_start()

    # 新的一週：重置計數
    if usage["week_start"] < week_start:
        usage = {"week_start": week_start, "scans": 0}
        save_usage(usage)

    remaining = FREE_SCANS_PER_WEEK - usage["scans"]
    can_scan = remaining > 0

    return can_scan, {
        "tier": "free",
        "remaining": max(0, remaining),
        "limit": FREE_SCANS_PER_WEEK,
        "resets_at": week_start + 7 * 24 * 3600,
    }


def record_scan() -> None:
    """記錄一次掃描使用"""
    license = load_license()
    if license.is_pro():
        return  # Pro 用戶不計數

    usage = load_usage()
    week_start = get_week_start()

    if usage["week_start"] < week_start:
        usage = {"week_start": week_start, "scans": 0}

    usage["scans"] += 1
    save_usage(usage)


def print_tier_banner() -> None:
    """打印許可證狀態橫幅"""
    license = load_license()
    can, info = can_scan()

    if info["tier"] == "pro":
        expires = time.strftime("%Y-%m-%d", time.localtime(info["expires_at"]))
        print(f"[PRO] Unlimited scans · expires {expires}")
    else:
        remaining = info["remaining"]
        limit = info["limit"]
        if remaining > 0:
            print(f"[FREE] {remaining}/{limit} scans remaining this week")
        else:
            resets = time.strftime("%Y-%m-%d", time.localtime(info["resets_at"]))
            print(f"[FREE] 0/{limit} remaining · resets {resets}")
            print("  Upgrade to Pro: $4.99/month or $39/year")
            print("  Run: safety-check --activate-pro <key>")