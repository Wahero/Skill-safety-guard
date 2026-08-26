// skill-safety-guard 擴展：安裝前自動攔截 + 實時危險命令攔截
//
// 對齊 src/skill_safety_guard 規則庫的精簡版（第一道防線）：
//  1) tool_call 攔截：bash 命令命中危險模式 → 攔截/確認（對應 rules/dangerous_shell.yaml）
//  2) input 攔截：用戶輸入 /skill:<name> → 載入前輕量掃描該 skill 目錄 → 高風險則攔截
//
// 深度掃描（187 條規則 / 10 類）仍用 /safety-check <target>；本擴展是「自動 + 零依賴」的守門。
// 安裝：複製本檔到 ~/.pi/agent/extensions/safety-guard.ts，或 `pi install git:github.com/Wahero/Skill-safety-guard`
//
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { isToolCallEventType } from "@earendil-works/pi-coding-agent";
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";

// ---------------------------------------------------------------------------
// 危險 Shell 規則（對齊 rules/dangerous_shell.yaml，正則與 YAML 一致）
// ---------------------------------------------------------------------------
interface Rule {
  id: string;
  name: string;
  pattern: RegExp;
  severity: "critical" | "high" | "medium";
}

const SHELL_RULES: Rule[] = [
  { id: "shell-curl-bash", name: "curl piped to bash", severity: "critical",
    pattern: new RegExp("curl\\s+[^|]*\\|\\s*(sudo\\s+)?(ba)?sh|curl\\s+[^|]*>\\s*/tmp/[^&]+&&\\s*(sudo\\s+)?(ba)?sh") },
  { id: "shell-wget-sh", name: "wget piped to sh", severity: "critical",
    pattern: new RegExp("wget\\s+[^|]*\\|\\s*(sudo\\s+)?sh|wget\\s+[^|]*&&\\s*(sudo\\s+)?sh") },
  { id: "shell-reverse-tcp", name: "Reverse Shell (bash)", severity: "critical",
    pattern: new RegExp("bash\\s+-i\\s+>&\\s*/dev/tcp/|/dev/tcp/[0-9.]+/\\d+|\\(\\s*bash\\s*\\)\\s*>\\s*/dev/tcp/") },
  { id: "shell-reverse-nc", name: "Reverse Shell (netcat)", severity: "critical",
    pattern: new RegExp("nc\\s+-[a-z]*e\\s*/bin/(ba)?sh|ncat\\s+-[a-z]*e\\s*/bin/(ba)?sh|rm\\s*/tmp/\\w+;\\s*mkfifo|mkfifo\\s+/tmp/[^;]+;\\s*") },
  { id: "shell-rm-rf-root", name: "rm -rf on critical path", severity: "critical",
    pattern: new RegExp("rm\\s+-[rRfF]+\\s+/\\s*$|rm\\s+-[rRfF]+\\s+/\\*|rm\\s+-[rRfF]+\\s+~/?(\\s|$)|rm\\s+-[rRfF]+\\s+--no-preserve-root\\s+/") },
  { id: "shell-dd-disk", name: "dd disk wipe", severity: "critical",
    pattern: new RegExp("dd\\s+if=/dev/(zero|urandom)\\s+of=/dev/(sd|hd|nvme|vd)[a-z]\\b") },
  { id: "shell-fork-bomb", name: "Fork Bomb", severity: "critical",
    pattern: new RegExp(":\\(\\)\\s*\\{\\s*:\\|:&\\s*\\}\\s*;:\\s*") },
  { id: "shell-base64-pipe-exec", name: "Base64-decoded execution", severity: "critical",
    pattern: new RegExp("base64\\s+-d[^|]*\\|\\s*(ba)?sh|base64\\s+--decode[^|]*\\|\\s*(ba)?sh|\\|\\s*base64\\s+-d") },
  { id: "shell-disable-firewall", name: "Disable firewall", severity: "critical",
    pattern: new RegExp("iptables\\s+-F|ufw\\s+disable|systemctl\\s+stop\\s+firewalld|netsh\\s+advfirewall\\s+set\\s+allprofiles\\s+state\\s+off") },
  { id: "shell-curl-env", name: "exfiltrate env via curl", severity: "critical",
    pattern: new RegExp("curl\\s+[^|]*\\$\\(env\\)|curl\\s+[^|]*\\$?(PATH|HOME|USER|AWS_|GITHUB_)|env\\s*\\|\\s*curl") },
  { id: "shell-history-clear", name: "Clear bash history", severity: "high",
    pattern: new RegExp("history\\s+-c.*&&\\s*rm\\s+~/.bash_history|unset\\s+HISTFILE.*&&\\s*exit") },
  { id: "shell-chmod-777", name: "chmod 777", severity: "high",
    pattern: new RegExp("chmod\\s+(-R\\s+)?777\\s+/|chmod\\s+(-R\\s+)?777\\s+~") },
];

// 憑證規則（對齊 rules/credentials.yaml 的精簡版）
const CRED_RULES: Rule[] = [
  { id: "cred-openai", name: "OpenAI API Key", severity: "high",
    pattern: new RegExp("sk-[A-Za-z0-9]{20,}T3BlbkFJ[A-Za-z0-9]{20,}|sk-proj-[A-Za-z0-9_-]{40,}|sk-[A-Za-z0-9]{40,}") },
  { id: "cred-anthropic", name: "Anthropic API Key", severity: "high",
    pattern: new RegExp("sk-ant-[A-Za-z0-9-]{40,}") },
  { id: "cred-aws-access-key", name: "AWS Access Key ID", severity: "high",
    pattern: new RegExp("AKIA[0-9A-Z]{16}") },
  { id: "cred-github-token", name: "GitHub PAT", severity: "high",
    pattern: new RegExp("ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82}") },
  { id: "cred-slack", name: "Slack Token", severity: "high",
    pattern: new RegExp("xox[baprs]-[0-9a-zA-Z]{10,48}") },
  { id: "cred-stripe", name: "Stripe API Key", severity: "high",
    pattern: new RegExp("sk_live_[0-9a-zA-Z]{24,}|pk_live_[0-9a-zA-Z]{24,}|rk_live_[0-9a-zA-Z]{24,}") },
  { id: "cred-google-api", name: "Google API Key", severity: "high",
    pattern: new RegExp("AIza[0-9A-Za-z_-]{35}") },
  { id: "cred-private-key", name: "PEM Private Key", severity: "high",
    pattern: new RegExp("-----BEGIN (RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----") },
];

// ---------------------------------------------------------------------------
// 輕量掃描（純 TS，無 subprocess 依賴）
// ---------------------------------------------------------------------------
const TEXT_EXT = /\.(md|txt|py|js|ts|mjs|cjs|jsx|tsx|sh|bash|zsh|yaml|yml|json|toml|env|ini|conf|cfg|sql|html|css|rb|go|rs|java|c|h|cpp|php|swift|kt|pl|lua|r)$/i;
const MAX_FILES = 200;
const MAX_BYTES = 512 * 1024; // 512KB / file

interface Hit {
  id: string;
  name: string;
  severity: "critical" | "high" | "medium";
  file: string;
}

function scanContent(content: string, file: string, rules: Rule[]): Hit[] {
  const hits: Hit[] = [];
  for (const r of rules) {
    if (r.pattern.test(content)) {
      hits.push({ id: r.id, name: r.name, severity: r.severity, file });
    }
  }
  return hits;
}

function scanSkillDir(dir: string): { total: number; grade: string; verdict: string; hits: Hit[] } | null {
  if (!existsSync(dir)) return null;
  const allHits: Hit[] = [];

  // 只掃描入口檔 + 根層安裝腳本（不遞迴，避免文檔/規則定義/測試樣本誤報）
  const scanFiles: string[] = ["SKILL.md"];
  const rootPatterns = [/\.sh$/i, /^install/i, /^setup/i, /^postinstall/i, /^Makefile$/i, /^Dockerfile$/i, /\.ps1$/i];
  try {
    for (const name of readdirSync(dir)) {
      if (name === ".git" || name === "node_modules") continue;
      const p = join(dir, name);
      try {
        const st = statSync(p);
        if (st.isFile() && rootPatterns.some((r) => r.test(name))) {
          scanFiles.push(name);
        }
      } catch {
        // ignore
      }
    }
  } catch {
    return null;
  }

  for (const name of scanFiles) {
    const p = join(dir, name);
    try {
      const st = statSync(p);
      if (!st.isFile() || st.size > MAX_BYTES) continue;
      const content = readFileSync(p, "utf-8");
      allHits.push(...scanContent(content, p, SHELL_RULES));
      allHits.push(...scanContent(content, p, CRED_RULES));
    } catch {
      // ignore
    }
  }

  const critical = allHits.filter((h) => h.severity === "critical").length;
  const high = allHits.filter((h) => h.severity === "high").length;
  let grade = "A";
  let verdict = "SAFE";
  if (critical > 0) { grade = "F"; verdict = "DANGER"; }
  else if (high > 0) { grade = "D"; verdict = "CAUTION"; }
  else if (allHits.length > 0) { grade = "C"; verdict = "CAUTION"; }

  return { total: allHits.length, grade, verdict, hits: allHits.slice(0, 20) };
}

// ---------------------------------------------------------------------------
// 擴展入口
// ---------------------------------------------------------------------------
export default function (pi: ExtensionAPI) {
  // 1) 實時攔截危險 bash 命令
  pi.on("tool_call", async (event, ctx) => {
    if (!isToolCallEventType("bash", event)) return;
    const cmd = event.input.command ?? "";
    if (!cmd) return;

    let hits: Hit[] = [];
    try {
      hits = scanContent(cmd, "<command>", SHELL_RULES);
    } catch {
      return;
    }
    if (hits.length === 0) return;

    const names = hits.map((h) => h.id).join(", ");
    const hasCritical = hits.some((h) => h.severity === "critical");
    const title = "🛡️ skill-safety-guard 攔截";
    const body = `偵測到危險命令（${names}）\n\n${cmd.slice(0, 200)}${hasCritical ? "\n\n⚠️ 此為高風險命令，建議拒絕執行。" : ""}`;

    if (ctx.hasUI) {
      let ok = false;
      try {
        ok = await ctx.ui.confirm(title, body);
      } catch {
        ok = false;
      }
      if (!ok) {
        return { block: true, reason: `Blocked by skill-safety-guard: ${names}` };
      }
    } else if (hasCritical) {
      // 無 UI 環境（print/json）：critical 直接攔截
      return { block: true, reason: `Blocked by skill-safety-guard: ${names}` };
    }
  });

  // 2) skill 載入前掃描（/skill:<name>）
  pi.on("input", async (event, ctx) => {
    if (event.source === "extension") return;
    const m = /^\/skill:(\S+)/.exec(event.text.trim());
    if (!m) return;

    const name = m[1].replace(/[\\/]/g, ""); // 防路徑穿越
    if (!name) return;

    // 常見 skill 安裝位置
    const candidates = [
      join(homedir(), ".pi", "agent", "skills", name),
      join(homedir(), ".agents", "skills", name),
      join(homedir(), ".pi", "agent", "git", name),
    ];
    const target = candidates.find((d) => existsSync(d));
    if (!target) return; // 找不到 → 交給 Pi 正常處理

    const result = scanSkillDir(target);
    if (!result || result.total === 0) return;

    const title = "🛡️ skill-safety-guard 掃描";
    const body = `載入前掃描「${name}」：${result.verdict}（${result.grade} 級，${result.total} 個發現）\n\n` +
      result.hits.slice(0, 8).map((h) => `• [${h.severity}] ${h.id}`).join("\n") +
      (result.hits.length > 8 ? `\n… 共 ${result.hits.length} 條` : "");

    if (result.grade === "F" || result.grade === "D") {
      if (ctx.hasUI) {
        let ok = false;
        try {
          ok = await ctx.ui.confirm(title, `${body}\n\n⚠️ 高風險，仍要載入此 skill？`);
        } catch {
          ok = false;
        }
        if (!ok) {
          ctx.ui.notify(`已攔截載入「${name}」（${result.grade} 級）`, "error");
          return { action: "handled" };
        }
      } else {
        ctx.ui.notify(`已攔截載入「${name}」（${result.grade} 級）`, "error");
        return { action: "handled" };
      }
    } else if (ctx.hasUI) {
      ctx.ui.notify(`${name}：${result.verdict}（${result.grade} 級，${result.total} 發現）`, "info");
    }
    return;
  });
}
