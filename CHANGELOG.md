# Changelog

All notable changes to skill-safety-guard will be documented in this file.

## [0.1.0] - 2026-08-17

### Phase 0 完成 ✅

#### Added
- **核心架構**
  - SKILL.md 完整 manifest
  - Python 包結構（`src/skill_safety_guard/`）
  - 獨立 CLI 包裝（`scripts/safety-check`）
  - pyproject.toml 配置

- **檢測器**（P0 必含）
  - 憑證洩露檢測器（10 條規則）
  - 危險 Shell 命令檢測器（12 條規則）
  - 敏感路徑訪問檢測器（9 條規則）

- **Pi Agent 全局檢查**
  - Pi 版本 CVE 檢測（CVE-2026-54326/54327）
  - auth.json 文件權限檢查

- **命令支持**
  - `safety-check` 默認掃描當前目錄
  - `--pi` 只掃描 Pi 全局
  - `--output json` 結構化輸出
  - `--report-fp <rule-id>` 報告誤報
  - `--help` 幫助信息

- **白名單機制（F-014）**
  - 已知誤報模式過濾
  - 置信度分級降級
  - 路徑白名單

- **測試**
  - 3 個惡意樣本（credential_leak, dangerous_shell, sensitive_path）
  - 5 個乾淨樣本（hello-world, data-formatter, git-helper, code-snippet, markdown-table）
  - 自動化測試套件（V-02, V-04, V-06）

- **文檔**
  - README.md（中英對照）
  - PRD v3.0 與 v4.0
  - 討論記錄
  - Phase 0 驗證報告
  - Issue 模板（誤報 + Bug）

### Verified
- ✅ V-02: YAML 解析 - 100% 正確
- ✅ V-03: Pi 版本檢測 - 提取 `0.84.2` 準確
- ✅ V-04: 正則檢測 - **100% 檢出率**（3/3 惡意樣本）
- ✅ V-06: 誤報基線 - **0% 誤報率**（0/5 乾淨樣本）
- ⚠️ V-05: 安裝前攔截 - 降級為手動 URL 掃描（Pi Agent 無 hook API）

### Known Issues
- Pi 0.84.2 在當前環境檢出 CVE-2026-54327（需升級到 0.85.0+）
- auth.json 權限 0o666 不安全（建議改為 600）

## [Unreleased]

### Phase 1 計劃
- F-007~F-010: 殺手場景「安裝前 URL 掃描」
- F-014~F-017: 白名單擴展 + 置信度分級完善
- F-018~F-021: 報告優化 + 端到端測試

詳見 `docs/PRD_v4_聚焦个人开发者版.MD`。