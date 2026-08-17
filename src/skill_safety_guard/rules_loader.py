"""規則庫加載器：從 rules/ 目錄讀取 YAML 規則"""
from pathlib import Path
from typing import Dict, List
import yaml


def get_rules_dir() -> Path:
    """獲取規則目錄的絕對路徑（兼容開發模式和安裝模式）"""
    # 開發模式：src/skill_safety_guard/ → ../../rules/
    here = Path(__file__).resolve().parent
    dev_rules = here.parent.parent / "rules"
    if dev_rules.exists():
        return dev_rules
    # 安裝模式：skill_safety_guard/ 同級的 rules/
    install_rules = here.parent / "rules"
    if install_rules.exists():
        return install_rules
    raise FileNotFoundError(f"規則目錄未找到。已嘗試: {dev_rules}, {install_rules}")


def load_rules_file(filename: str) -> List[Dict]:
    """加載單個規則文件"""
    rules_dir = get_rules_dir()
    rule_file = rules_dir / filename
    if not rule_file.exists():
        return []
    with open(rule_file, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("rules", [])


def load_whitelist() -> Dict:
    """加載白名單"""
    rules_dir = get_rules_dir()
    wl_file = rules_dir / "whitelist.yaml"
    if not wl_file.exists():
        return {}
    with open(wl_file, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_all_rules() -> Dict[str, List[Dict]]:
    """加載所有規則分類"""
    return {
        "credentials": load_rules_file("credentials.yaml"),
        "shell": load_rules_file("dangerous_shell.yaml"),
        "paths": load_rules_file("sensitive_paths.yaml"),
        "unicode": load_rules_file("unicode_steganography.yaml"),
        "critical_paths": load_rules_file("critical_paths.yaml"),
        "installed_extensions": load_rules_file("installed_extensions.yaml"),
        "prompt_injection": load_rules_file("prompt_injection.yaml"),
    }