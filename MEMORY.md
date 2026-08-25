# MEMORY.md — Skill-safety-guard 專案持久記憶

## 專案狀態（截至 2026-08-26）

- 當前版本：v3.7.0
- Phase 0 ✅ 全部完成 | Phase 1 ✅ 全部完成（8/8，`2aec201` → `18cda06`）
- 剩餘 Phase 2（4 項）+ Phase 3（4 項）待跟進，詳見 `Skill-safety-guard待跟進事項0826.md`
- 今日完成記錄：`memory/2026-08-26.md`

## 關鍵架構決策

### cli.py 拆分（P1-1）
- `cli.py`（417 行）：命令路由 + 參數解析 + `_run_scan` 編排
- `scan_orchestrator.py`：`scan_target` / `resolve_output_file` / `emit_output`
- `commands.py`：`handle_report_fp` / `scan_pi_only` / `format_json_output` / `make_install_decision` / `format_decision_block`
- `web_api.py` import 從 cli 改為 scan_orchestrator + commands

### 檢測器統一框架（P1-2/P1-3）
- `BaseDetector._make_finding()`：統一構建 Finding（截斷 matched_text≤100, context≤200）
- `BaseDetector._detect_lines()`：標準逐行正則檢測
- 8 個檢測器：credentials, shell, paths, unicode, critical_paths, privacy, installed_extensions, prompt_injection
- 掃描迴圈用 `det.category` 屬性，不再覆寫 `det.category = cat`

### Web 安全（P1-6）
- CORS 白名單：localhost/127.0.0.1:8765/3000
- Rate limit：每 IP 每分鐘 5 次 POST（線程安全，超額 429）
- POST body 1MB 上限
- 路徑遍歷防禦：resolve() + normpath 雙重檢查

## 已知坑與技術債

1. **自掃白名單用 path 豁免**：5 個自指誤報用 path 白名單而非 pattern，規則檔案路徑變動需同步更新 `whitelist.yaml`
2. **installed_extensions 目錄掃描排除**：ext-curl-wget 規則對文檔性提及過度敏感，僅在 `--audit-extensions` 時使用
3. **PowerShell 引號轉義**：Windows 下 `--output json` + `Select-Object` 管道反覆失敗，改用獨立 Python + `--output-file` 繞開
4. **edit_file 縮排風險**：替換多行代碼時 `return` 語句錯位會導致 NoneType 錯誤，需逐行確認縮排
5. **license.py 為 demo 層級**：SECRET_KEY 隨原始碼公開，正式部署需改用環境變數或非對稱簽名

## 開發環境

- OS: Windows
- Python: 3.11 (uv cpython-3.11-windows-x86_64)
- PYTHONPATH 需設為 `src`
- PYTHONIOENCODING 需設為 `utf-8`
- Phase 0 測試：`python tests/test_phase0.py`
- 自掃驗證：`python -m skill_safety_guard . --no-pi --output json --output-file tmp.json`

## 文件索引

- 原始規格：`修改建議方案.MD`（22 項，Phase 0-3）
- 待跟進清單：`Skill-safety-guard待跟進事項0826.md`
- 今日完成記錄：`memory/2026-08-26.md`
