# Changelog

All notable changes to `skill-safety-guard` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.9.0] - 2026-01-26

### Added
- **多框架配置安全**（10 條規則）：覆蓋 Windsurf、Goose、Devin、Copilot、Roo Code、JetBrains AI、Supermaven 的配置文件寫入檢測
- **CI/CD 安全**（8 條規則）：GitHub Actions（curl|bash、secrets 暴露、腳本注入、不信任 checkout）、GitLab CI、Jenkinsfile、Azure Pipeline
- **Docker / K8s 安全**（10 條規則）：Dockerfile（curl|bash、--privileged、root 用戶、secrets in ARG）、docker-compose（privileged、host 網絡、明文 secrets）、Kubernetes（kubeconfig 證書暴露、privileged 容器、hostPath 掛載）
- `MultiFrameworkDetector`：統一處理多框架 + CI/CD + Docker/K8s 規則的檢測器
- `.github/workflows/pr-audit.yml`：PR 安全審計 workflow，自動掃描 PR 中改動的 SKILL.md 目錄並上報 SARIF

### Changed
- 規則總數：218 → 246（+28）
- 規則類別：11 → 13

---

## [3.8.0] - 2026-01-26

### Added
- **OWASP Top 10 程式碼模式檢測**（18 條規則）：路徑穿越（dotdot/encoded/symlink）、弱哈希（MD5/SHA1）、硬編碼密鑰、弱加密（DES）、弱隨機數、命令注入（os.system/eval/exec）、反序列化（pickle）、SQL 注入、模板注入、SSRF、JS eval、危險 import
- **原生檔案刪除檢測**（14 條規則）：Rust（`std::fs::remove_dir_all`/`remove_file`、`trash::delete_all`）、Python（`os.remove`/`shutil.rmtree`/`pathlib.unlink`/`send2trash`）、Go（`os.Remove`/`os.RemoveAll`）、PowerShell（`Remove-Item`/`del`）、通用系統路徑刪除
- `NativeFileOpsDetector`：檢測非 Shell 上下文中 Rust/Python/Go/PowerShell 的檔案刪除 API
- `OWASPDetector`：檢測 OWASP Top 10 程式碼安全模式
- 每日漏洞庫更新 workflow（`.github/workflows/update-vulns.yml`）：Cron + workflow_dispatch，自動從 OSV.dev 拉取 CVE 並 commit
- **首次調用自動啟動 Web UI**：技能首次執行時自動啟動 Web 界面（移除 `--web` CLI 參數）
- PR 安全審計 workflow（`.github/workflows/pr-audit.yml`）
- 自掃 SAFE（A 級評分）

### Changed
- 移除 `--web`/`--web-port`/`--web-host` CLI 參數，改為首次調用自動啟動
- 報告摘要增加 OWASP 規則計數顯示
- 漏洞庫規則從 JSON 改為 YAML 格式，提升可讀性和可維護性
- 規則總數：201 → 218

---

## [3.7.0] - 2025

### Added
- Pi 擴展攔截（B-001）
- Web 後端實現（C-006）

---

## [3.6.0] - 2025

### Added
- 隱私行為檢測（6 條規則）
- `.mjs` / `.cjs` 文件掃描修復

---

## [3.5.0] - 2025

### Added
- GitHub URL 自動報告
- 誤報識別
- Pi Package 化
- 版本統一

---

## [3.4.x] - 2025

### Added
- 國內漏洞源（CAIVD / AVID）
- 增強狀態顯示

---

## [3.3.0] - 2025

### Added
- 權威漏洞源
- 自動更新頻率

---

## [3.0.0] - 2025

### Added
- LLM 輔助檢測
- MCP 注入深度檢測（181 條規則）

---

## [2.0.0] - 2025

### Added
- Unicode 隱寫檢測
- MCP 基礎掃描
- `--all` 完整掃描

---

## [1.0.0] - 2025

### Added
- Pi 版本漏洞檢測（CVE-2026-54326 / 54327）
- `auth.json` 權限檢查
- 憑證洩露檢測（OpenAI / Anthropic / AWS / GitHub / Slack / Stripe / JWT / PEM）
- 危險 Shell 命令檢測
- 敏感路徑訪問檢測
- Markdown 風險報告
