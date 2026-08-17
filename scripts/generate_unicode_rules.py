# -*- coding: utf-8 -*-
"""Generate unicode_steganography.yaml with literal high-codepoint characters."""
from pathlib import Path

TARGET_FILE = Path(__file__).resolve().parent.parent / "rules" / "unicode_steganography.yaml"

# 預構建所有需要的 pattern
ZWSP = chr(0x200B)
ZWNJ = chr(0x200C)
ZWJ = chr(0x200D)
BOM = chr(0xFEFF)
SHY = chr(0x00AD)
MVS = chr(0x180E)
WJ = chr(0x2060)
FA = chr(0x2061)
IT = chr(0x2062)
IS = chr(0x2063)
IP = chr(0x2064)
TAG_START = chr(0xE0000)
TAG_END = chr(0xE007F)
CJK_START = chr(0x4E00)
CJK_END = chr(0x9FFF)

# 構建所有規則
rules_yaml = f'''# skill-safety-guard 規則庫：Unicode 隱寫檢測
#
# 由 scripts/generate_unicode_rules.py 自動生成
# 請勿手動編輯本文件，請編輯生成腳本

rules:
  # === 零寬字符 ===

  - id: unicode-zwsp
    name: "Zero-Width Space (U+200B)"
    pattern: "[{ZWSP}]"
    severity: high
    confidence: high
    category: unicode
    description: 零寬空格 - 隱寫攻擊最常用的字符
    remediation: 移除所有 U+200B 字符

  - id: unicode-zwnj
    name: "Zero-Width Non-Joiner (U+200C)"
    pattern: "[{ZWNJ}]"
    severity: high
    confidence: high
    category: unicode
    description: 零寬不連字符 - 可用於字符間隱藏指令
    remediation: 移除所有 U+200C 字符

  - id: unicode-zwj
    name: "Zero-Width Joiner (U+200D)"
    pattern: "[{ZWJ}]"
    severity: high
    confidence: high
    category: unicode
    description: 零寬連字符 - 字符連接序列中可隱藏指令
    remediation: 移除所有 U+200D 字符

  - id: unicode-bom
    name: "Byte Order Mark (U+FEFF)"
    pattern: "[{BOM}]"
    severity: medium
    confidence: medium
    category: unicode
    description: BOM 字符 - 偶爾出現在文件開頭
    remediation: 確保文件編碼為 UTF-8 無 BOM

  - id: unicode-soft-hyphen
    name: "Soft Hyphen (U+00AD)"
    pattern: "[{SHY}]"
    severity: medium
    confidence: medium
    category: unicode
    description: 軟連字符 - 在視覺上不可見
    remediation: 移除

  - id: unicode-mongolian-sep
    name: "Mongolian Vowel Separator (U+180E)"
    pattern: "[{MVS}]"
    severity: medium
    confidence: medium
    category: unicode
    description: 蒙古元音分隔符 - 罕見字符
    remediation: 移除

  - id: unicode-word-joiner
    name: "Word Joiner (U+2060)"
    pattern: "[{WJ}]"
    severity: high
    confidence: high
    category: unicode
    description: 字連接符 - 類似零寬空格
    remediation: 移除

  - id: unicode-fn-applied
    name: "Function Application (U+2061)"
    pattern: "[{FA}]"
    severity: high
    confidence: high
    category: unicode
    description: 函數應用符 - 不可見字符
    remediation: 移除

  - id: unicode-invisible-times
    name: "Invisible Times (U+2062)"
    pattern: "[{IT}]"
    severity: high
    confidence: high
    category: unicode
    description: 隱式時間符
    remediation: 移除

  - id: unicode-invisible-sep
    name: "Invisible Separator (U+2063)"
    pattern: "[{IS}]"
    severity: high
    confidence: high
    category: unicode
    description: 隱式分隔符
    remediation: 移除

  - id: unicode-invisible-plus
    name: "Invisible Plus (U+2064)"
    pattern: "[{IP}]"
    severity: high
    confidence: high
    category: unicode
    description: 隱式加號
    remediation: 移除

  - id: unicode-tag-block
    name: "Tag Characters (U+E0000-U+E007F)"
    pattern: "[{TAG_START}-{TAG_END}]"
    severity: critical
    confidence: high
    category: unicode
    description: |
      Tag 字符區塊 - 設計上用於隱藏文本。
      任何使用都極度可疑，可能是 Unicode 隱寫攻擊。
    remediation: 立即移除。Tag 字符在正常文本中不應出現

  - id: unicode-zwc-sequence
    name: "Zero-width character sequence (3+)"
    pattern: "[{ZWSP}{ZWNJ}{ZWJ}{BOM}{WJ}]{{3,}}"
    severity: critical
    confidence: high
    category: unicode
    description: 連續 3+ 零寬字符 - 強烈暗示隱寫攻擊
    remediation: 移除所有零寬字符序列

  - id: unicode-mixed-zwc
    name: "Mixed zero-width with text"
    pattern: "[a-zA-{CJK_START}-{CJK_END}][{ZWSP}{ZWNJ}{ZWJ}{BOM}][a-zA-{CJK_START}-{CJK_END}]"
    severity: high
    confidence: medium
    category: unicode
    description: 文本字符之間夾雜零寬字符 - 隱寫攻擊的典型模式
    remediation: 移除文本間的零寬字符
'''

TARGET_FILE.write_text(rules_yaml, encoding="utf-8")
print(f"Generated: {TARGET_FILE}")

# 驗證
import yaml
data = yaml.safe_load(rules_yaml)
print(f"Loaded {len(data['rules'])} rules:")
for r in data["rules"]:
    if "tag" in r["id"]:
        chars = [hex(ord(c)) for c in r["pattern"]]
        print(f"  - {r['id']}: {chars}")