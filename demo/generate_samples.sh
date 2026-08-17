#!/bin/bash
# skill-safety-guard Demo 自動生成腳本
# 在 demo/outputs/ 生成真實掃描輸出

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$SCRIPT_DIR/outputs"

mkdir -p "$OUTPUT_DIR"

cd "$PROJECT_DIR"

echo "======================================"
echo "  skill-safety-guard Demo 生成器"
echo "======================================"
echo ""

run_scan() {
    local target="$1"
    local output_file="$2"
    local label="$3"
    echo "[${label}] 掃描 ${target}..."
    # 使用 tee 而不是 > redirect 以避免 Windows 上的問題
    PYTHONIOENCODING=utf-8 python scripts/safety-check "$target" 2>&1 | tee "$output_file" > /dev/null
}

# 1. Pi 全局檢查
run_scan "--pi" "$OUTPUT_DIR/01-pi-global.md" "1/6"

# 2. 危險 Shell 命令
run_scan "tests/fixtures/malicious/dangerous_shell" "$OUTPUT_DIR/02-malicious-shell.md" "2/6"

# 3. 憑證洩露
run_scan "tests/fixtures/malicious/credential_leak" "$OUTPUT_DIR/03-credential-leak.md" "3/6"

# 4. 敏感路徑訪問
run_scan "tests/fixtures/malicious/sensitive_path" "$OUTPUT_DIR/04-sensitive-path.md" "4/6"

# 5. Unicode 隱寫
run_scan "tests/fixtures/malicious/unicode_stego/SKILL.md" "$OUTPUT_DIR/05-unicode-stego.md" "5/6"

# 6. 乾淨樣本
run_scan "tests/fixtures/clean/hello-world" "$OUTPUT_DIR/06-clean-sample.md" "6/6"

echo ""
echo "======================================"
echo "  完成！輸出在："
echo "  $OUTPUT_DIR"
echo "======================================"
ls -la "$OUTPUT_DIR"