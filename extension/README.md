# safety-guard 擴展（Pi Extension）

skill-safety-guard 的**自動攔截層**——第一道防線。純 TypeScript、零外部依賴，隨套件一起分發。

> 深度掃描（187 規則 / 10 類）仍用 `/safety-check <target>`；本擴展負責「自動 + 實時」的守門。

## 功能

| 攔截點 | 事件 | 行為 |
|--------|------|------|
| **實時危險命令** | `tool_call`（bash）| 命令命中 `dangerous_shell.yaml` 的 12 條危險模式 → 彈確認框，拒絕即攔截；無 UI 環境 critical 直接攔截 |
| **skill 載入前掃描** | `input`（`/skill:<name>`）| 掃描該 skill 目錄（危險 shell + 憑證洩露的精簡規則），D/F 級彈確認攔截，C 級提示 |

## 安裝

### 方式 1：隨套件安裝（推薦）

```bash
pi install git:github.com/Wahero/Skill-safety-guard
```

`package.json` 的 `pi.extensions` 已聲明 `./extension/safety-guard.ts`，安裝後自動載入。

### 方式 2：手動複製

```bash
cp extension/safety-guard.ts ~/.pi/agent/extensions/safety-guard.ts
```

然後在 Pi 中執行 `/reload` 熱載入。

## 驗證

```bash
# 危險命令攔截（在 Pi 對話中讓 agent 執行）
# → 應觸發確認框

# skill 載入掃描
/skill:some-risky-skill
# → 應顯示掃描結果或攔截
```

## 注意

- 本擴展是「精簡版」規則（12 條 shell + 8 條憑證），**不是**完整 187 條規則。完整掃描請用 `/safety-check`。
- 擴展邏輯已包 try/catch，任何異常都不會中斷 Pi。
- 攔截策略：有 UI 時一律「確認後放行」，尊重「誤報率 > 檢出率」原則；無 UI（print/json）時 critical 直接攔截。

## 維護

規則正則與 `rules/dangerous_shell.yaml`、`rules/credentials.yaml` 對齊。修改規則庫時，同步更新本檔的 `SHELL_RULES` / `CRED_RULES` 常量。

> 本檔位於 `extension/`，已列入 `rules/whitelist.yaml`（`*/extension/*`），因為檔內正則與規則庫相同，自掃必然自指命中。
