"""MCP 配置安全檢測（F-029~F-032）

靜態分析 MCP 配置，不實際連接 MCP 服務器：
- F-029: 識別 MCP 配置文件並解析
- F-030: 枚舉工具/資源
- F-031: 工具風險分類（SHELL/FILE/DATABASE/NETWORK/SAFE）
- F-032: 生成 MCP 檢查報告（作為 Skill 報告子模塊）
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from .rules_loader import load_rules_file

# MCP 配置文件候選
MCP_CONFIG_FILES = [
    ".mcp.json",
    "mcp.json",
    ".cursor/mcp.json",
    ".github/mcp.json",
    ".config/mcp.json",
]


def find_mcp_configs(directory: Path) -> List[Path]:
    """查找項目中的 MCP 配置文件"""
    configs = []
    for name in MCP_CONFIG_FILES:
        p = directory / name
        if p.exists():
            configs.append(p)
    return configs


def parse_mcp_config(path: Path) -> Optional[Dict]:
    """解析 MCP 配置 JSON"""
    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError, PermissionError):
        return None


def classify_tool(name: str, description: str = "") -> str:
    """根據工具名稱/描述分類（F-031）

    返回：SHELL / FILE / DATABASE / NETWORK / CREDENTIAL / SAFE / UNKNOWN
    """
    text = f"{name} {description}".lower()

    shell_kw = ["exec", "shell", "bash", "zsh", "command", "run_cmd", "system", "terminal", "sh "]
    file_kw = ["write_file", "create_file", "append_file", "delete_file", "remove_file",
               "edit_file", "read_file", "list_files", "open_file", "save", "file"]
    db_kw = ["sql", "db", "database", "query", "postgres", "mysql", "mongo", "redis",
             "select", "insert", "update", "delete"]
    net_kw = ["http", "https", "fetch", "request", "post", "upload", "download",
              "webhook", "api", "send", "network", "url"]
    cred_kw = ["env", "credential", "secret", "token", "api_key", "password", "auth"]

    # 憑證最危險，優先判斷
    if any(k in text for k in cred_kw):
        return "CREDENTIAL"
    if any(k in text for k in shell_kw):
        return "SHELL"
    if any(k in text for k in file_kw):
        return "FILE"
    if any(k in text for k in db_kw):
        return "DATABASE"
    if any(k in text for k in net_kw):
        return "NETWORK"

    if not name:
        return "UNKNOWN"
    return "SAFE"


def extract_servers(config: Dict) -> List[Dict]:
    """提取 MCP 服務器列表"""
    servers = []
    mcp_servers = config.get("mcpServers", {})
    if isinstance(mcp_servers, dict):
        for name, server in mcp_servers.items():
            if isinstance(server, dict):
                servers.append({"name": name, **server})
    return servers


def extract_tools_from_servers(servers: List[Dict]) -> List[Dict]:
    """枚舉 MCP 服務器提供的工具（F-030）

    注意：靜態分析無法列出所有工具（需要連接服務器）。
    這裡提取配置中聲明的工具，以及通過名稱啟發式推斷。
    """
    tools = []
    for server in servers:
        # 配置中聲明的 tools
        declared_tools = server.get("tools", [])
        if isinstance(declared_tools, list):
            for t in declared_tools:
                if isinstance(t, str):
                    tools.append({"server": server["name"], "name": t, "description": ""})
                elif isinstance(t, dict):
                    tools.append({
                        "server": server["name"],
                        "name": t.get("name", ""),
                        "description": t.get("description", ""),
                    })

        # 從 server 命令推斷工具類型
        command = str(server.get("command", ""))
        if command:
            inferred = _infer_tools_from_command(command)
            for t in inferred:
                t["server"] = server["name"]
                tools.append(t)

    return tools


def _infer_tools_from_command(command: str) -> List[Dict]:
    """從服務器命令推斷可能的工具類型"""
    inferred = []
    cmd_lower = command.lower()

    if "git" in cmd_lower:
        inferred.append({"name": "git_*", "description": "Git 操作工具（推斷）"})
    if "sql" in cmd_lower or "db" in cmd_lower or "postgres" in cmd_lower or "mysql" in cmd_lower:
        inferred.append({"name": "db_*", "description": "數據庫操作工具（推斷）"})
    if "search" in cmd_lower or "browse" in cmd_lower:
        inferred.append({"name": "search_*", "description": "搜索/瀏覽工具（推斷）"})
    if "filesystem" in cmd_lower or "file" in cmd_lower:
        inferred.append({"name": "file_*", "description": "文件系統工具（推斷）"})
    if "docker" in cmd_lower:
        inferred.append({"name": "docker_*", "description": "Docker 操作工具（推斷）"})
    if "shell" in cmd_lower or "exec" in cmd_lower:
        inferred.append({"name": "exec_*", "description": "命令執行工具（推斷）"})

    return inferred


def check_mcp_directory(directory: Path, rules: List[Dict], extra_rules: List[Dict] = None) -> Dict:
    """檢查目錄中的 MCP 配置

    參數：
    - rules: 基礎 MCP 規則（mcp.yaml）
    - extra_rules: 額外規則（如 mcp_injection.yaml 的注入模式）

    返回：
    {
        "configs_found": int,
        "servers": [{name, command, args, transport}],
        "tools": [{server, name, classification}],
        "findings": [Finding 兼容 dict],
        "risk_summary": {SHELL: n, FILE: n, ...}
    }
    """
    result = {
        "configs_found": 0,
        "servers": [],
        "tools": [],
        "findings": [],
        "risk_summary": {},
        "transport_check": {},
        "scan_target": str(directory),
    }

    configs = find_mcp_configs(directory)
    result["configs_found"] = len(configs)

    all_rules = list(rules) + list(extra_rules or [])
    compiled_rules = []
    for rule in all_rules:
        try:
            compiled_rules.append((rule, re.compile(rule["pattern"], re.IGNORECASE)))
        except re.error:
            continue

    for config_path in configs:
        config = parse_mcp_config(config_path)
        if not config:
            result["findings"].append({
                "rule_id": "mcp-config-invalid",
                "rule_name": "MCP 配置文件無法解析",
                "severity": "high",
                "confidence": "high",
                "category": "mcp",
                "description": f"MCP 配置 {config_path.name} 不是有效 JSON",
                "remediation": "檢查配置格式",
                "file_path": str(config_path),
                "line_number": 1,
                "matched_text": "",
            })
            continue

        servers = extract_servers(config)
        result["servers"].extend(servers)

        # 對每個 server 的配置字符串做規則掃描（含注入模式）
        config_text = json.dumps(config, ensure_ascii=False)
        for rule, pattern in compiled_rules:
            for match in pattern.finditer(config_text):
                result["findings"].append({
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "severity": rule.get("severity", "medium"),
                    "confidence": rule.get("confidence", "medium"),
                    "category": rule.get("category", "mcp"),
                    "description": rule.get("description", ""),
                    "remediation": rule.get("remediation", ""),
                    "file_path": str(config_path),
                    "line_number": 1,
                    "matched_text": match.group(0)[:80],
                })

        # F-040: 傳輸安全檢查
        transport = _check_transport_security(config, config_path)
        for finding in transport:
            result["findings"].append(finding)
        if transport:
            result["transport_check"][str(config_path)] = len(transport)

        # 枚舉工具並分類
        tools = extract_tools_from_servers(servers)
        for tool in tools:
            classification = classify_tool(tool.get("name", ""), tool.get("description", ""))
            tool["classification"] = classification
            result["tools"].append(tool)
            result["risk_summary"][classification] = result["risk_summary"].get(classification, 0) + 1

    return result


def _check_transport_security(config: Dict, config_path: Path) -> List[Dict]:
    """F-040: MCP 傳輸安全檢查

    檢查：
    - 明文 HTTP（非 HTTPS）
    - 內網地址 / 雲元數據
    - 未加密的 stdio（默認安全，檢查配置）
    - 混合傳輸（部分加密部分明文）
    """
    findings = []

    for name, server in config.get("mcpServers", {}).items():
        if not isinstance(server, dict):
            continue

        url = server.get("url", "")
        transport = server.get("transport", "")

        # 明文 HTTP
        if isinstance(url, str) and url.startswith("http://"):
            findings.append({
                "rule_id": "mcp-transport-http",
                "rule_name": f"服務器 {name} 使用明文 HTTP",
                "severity": "high",
                "confidence": "high",
                "category": "mcp",
                "description": f"MCP 服務器 {name} 使用明文 HTTP（無 TLS 加密）",
                "remediation": "改用 HTTPS 或 stdio",
                "file_path": str(config_path),
                "line_number": 1,
                "matched_text": url[:80],
            })

        # 內網地址 / 雲元數據
        if isinstance(url, str):
            lower = url.lower()
            if any(k in lower for k in ["169.254.169.254", "metadata.google", "100.100.100.200",
                                         "127.0.0.1", "localhost"]):
                findings.append({
                    "rule_id": "mcp-transport-internal",
                    "rule_name": f"服務器 {name} 指向內網/元數據地址",
                    "severity": "critical",
                    "confidence": "high",
                    "category": "mcp",
                    "description": f"MCP 服務器 {name} 連接內網或雲元數據地址（SSRF 風險）",
                    "remediation": "禁止訪問內網/元數據地址",
                    "file_path": str(config_path),
                    "line_number": 1,
                    "matched_text": url[:80],
                })

        # 混合傳輸（HTTP + HTTPS 共存）
        if isinstance(transport, str) and transport.lower() not in ["", "stdio", "sse", "streamable-http", "http"]:
            findings.append({
                "rule_id": "mcp-transport-unknown",
                "rule_name": f"服務器 {name} 使用未知傳輸方式",
                "severity": "low",
                "confidence": "medium",
                "category": "mcp",
                "description": f"傳輸方式 {transport} 不在已知列表（stdio/sse/streamable-http/http）",
                "remediation": "確認傳輸方式安全性",
                "file_path": str(config_path),
                "line_number": 1,
                "matched_text": transport[:80],
            })

    return findings


def format_mcp_report(mcp_result: Dict) -> str:
    """生成 MCP 檢查報告（作為 Skill 報告子模塊）"""
    lines = ["### 🔌 MCP 依賴檢查", ""]
    lines.append(f"- MCP 配置文件: {mcp_result['configs_found']} 個")
    lines.append(f"- MCP 服務器: {len(mcp_result['servers'])} 個")
    lines.append(f"- 工具枚舉: {len(mcp_result['tools'])} 個")

    if mcp_result["risk_summary"]:
        lines.append("")
        lines.append("- 工具風險分類:")
        for cat, count in sorted(mcp_result["risk_summary"].items(), key=lambda x: -x[1]):
            emoji = {
                "CREDENTIAL": "🔴", "SHELL": "🔴", "FILE": "🟠",
                "DATABASE": "🟡", "NETWORK": "🟡", "SAFE": "🟢", "UNKNOWN": "⚪",
            }.get(cat, "⚪")
            lines.append(f"  - {emoji} {cat}: {count}")

    if mcp_result["servers"]:
        lines.append("")
        lines.append("- 服務器列表:")
        for server in mcp_result["servers"]:
            cmd = server.get("command", "?")
            args = " ".join(str(a) for a in server.get("args", []))[:60]
            lines.append(f"  - **{server.get('name', '?')}**: `{cmd} {args}`")

    return "\n".join(lines)