"""Unicode 隱寫檢測器"""
import re
import unicodedata
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class UnicodeDetector(BaseDetector):
    """檢測文本中的 Unicode 隱寫字符

"""
    category = "unicode"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        findings = []
        for rule, pattern in self._iter_compiled_rules():
            for line_no, line in enumerate(content.splitlines(), start=1):
                # 跳過過長的行（性能保護）
                if len(line) > 50000:
                    continue

                matches = list(pattern.finditer(line))
                if matches:
                    # 取第一個匹配
                    match = matches[0]
                    matched_text = match.group(0)

                    # 對於零寬字符，顯示 codepoint 而不是字符本身
                    display_text = self._format_matched_text(matched_text)

                    finding = Finding(
                        rule_id=rule["id"],
                        rule_name=rule["name"],
                        severity=rule.get("severity", "medium"),
                        confidence=rule.get("confidence", "medium"),
                        category=rule.get("category", "unicode"),
                        description=rule.get("description", ""),
                        remediation=rule.get("remediation", ""),
                        file_path=str(file_path),
                        line_number=line_no,
                        matched_text=display_text,
                        context_line=line.strip()[:200],
                    )
                    findings.append(finding)
                    # 一個文件對每條規則只報告一次（取第一個匹配位置）
                    break

        # === 額外檢測：統計整個文件的不可見字符 ===

        invisible_chars = self._count_invisible_chars(content)
        if invisible_chars["total"] >= 5:
            # 多個不可見字符 → 額外的綜合報告
            findings.append(Finding(
                rule_id="unicode-summary",
                rule_name=f"文件中包含 {invisible_chars['total']} 個不可見字符",
                severity="high",
                confidence="high",
                category="unicode",
                description=(
                    f"文件中發現 {invisible_chars['total']} 個隱寫字符：\n"
                    + "\n".join(f"  - {k}: {v} 個" for k, v in invisible_chars["breakdown"].items())
                ),
                remediation="審查並移除所有隱寫字符",
                file_path=str(file_path),
                line_number=0,
                matched_text=f"{invisible_chars['total']} 個不可見字符",
                context_line="",
            ))

        return findings

    def _format_matched_text(self, text: str) -> str:
        """將不可見字符格式化為 codepoint 表示"""
        parts = []
        for ch in text:
            cp = ord(ch)
            name = unicodedata.name(ch, f"U+{cp:04X}")
            if cp < 0x20 or cp == 0x7F or cp in (0x00AD, 0x200B, 0x200C, 0x200D, 0xFEFF) or 0x2060 <= cp <= 0x2064 or 0xE0000 <= cp <= 0xE007F:
                parts.append(f"[{name} U+{cp:04X}]")
            else:
                parts.append(ch)
        return " ".join(parts)

    def _count_invisible_chars(self, content: str) -> dict:
        """統計文件中所有不可見字符"""
        invisible_chars = {
            0x200B: "Zero-Width Space",
            0x200C: "Zero-Width Non-Joiner",
            0x200D: "Zero-Width Joiner",
            0xFEFF: "BOM",
            0x00AD: "Soft Hyphen",
            0x180E: "Mongolian Vowel Sep",
            0x2060: "Word Joiner",
            0x2061: "Function Application",
            0x2062: "Invisible Times",
            0x2063: "Invisible Separator",
            0x2064: "Invisible Plus",
        }
        # 加上 Tag 區塊
        tag_range_start = 0xE0000
        tag_range_end = 0xE007F

        breakdown = {}
        total = 0

        for ch in content:
            cp = ord(ch)
            if cp in invisible_chars:
                name = invisible_chars[cp]
                breakdown[name] = breakdown.get(name, 0) + 1
                total += 1
            elif tag_range_start <= cp <= tag_range_end:
                name = "Tag Characters"
                breakdown[name] = breakdown.get(name, 0) + 1
                total += 1

        return {"total": total, "breakdown": breakdown}