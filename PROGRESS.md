# skill-safety-guard 项目进度记录

> 更新：2026-08-17
> 当前版本：v1.5.0（已发布）

## 已完成

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 08-17 | Phase 0 全通过 + 基础 MVP（45 规则）|
| v1.0.0 | 08-17 | 杀手机场景（URL/粘帖/决策）|
| v1.1.0 | 08-17 | Unicode 隐写 + Demo 包 |
| v1.2.0 | 08-17 | 全局 AGENTS.md 检测（critical_paths 16 条）|
| v1.3.0 | 08-17 | AI Agent 全覆蓋 + 包管理器 + 持久化（39 条）|
| v1.4.0 | 08-17 | 编辑器 + Git + 历史 + 数据库 + Rootkit（67 条）|
| v1.5.0 | 08-17 | Freemium + SARIF + 提示词注入 + 扩展审计（142 条）|
| v1.6.0 | 08-17 | MCP 依赖检查 + --all 完整扫描 + 进度显示（158 条）|
| v2.0.0 | 08-17 | Phase 2 全部完成 + 发布推广 |
| v3.0.0 | 08-17 | MCP 注入检测 + 传输安全 + LLM 辅助检测（181 条）|

## 当前能力

- 181 条规则，9 个检测类别
- 杀手机场景：GitHub URL / 粘帖 / 本地扫描
- Freemium：免费 5 次/周，Pro 无限
- 输出：Markdown / JSON / SARIF
- CI：3 OS × 3 Python 版本
- 测试：10 个 fixtures（7 恶意 + 6 干净，部分重叠）

## 待完成

### Phase 2 剩余（v2.0 计划）
- [x] F-025 --all 完整扫描 ✅
- [x] F-026 扫描进度显示 ✅
- [x] F-029~F-032 Skill 依赖检查（MCP 静态分析）✅

### Phase 3 剩余
- [x] F-037 LLM 辅助提示词注入检测（Pro 限定）✅
- [x] F-039/F-040 MCP 注入/传输安全 ✅
- [ ] F-043 性能优化
- [ ] F-044 完整用户文档

### Phase 4（后置）
- [ ] 多框架适配（OpenClaude/OpenCode/Claude Code）
- [ ] MCP 代理网关
- [ ] GitHub Action

### 运维/社区
- [ ] 部署 demo 到 GitHub Pages
- [ ] 社区推广（Twitter/Reddit/V2EX）
- [ ] 收集反馈
- [ ] 规则库持续扩展

## 常用命令

```bash
# 扫描
python scripts/safety-check <path|url>
python scripts/safety-check --pi
python scripts/safety-check --output sarif

# 许可
python scripts/safety-check --generate-pro-key
python scripts/safety-check --activate-pro <key>
python scripts/safety-check --license-status

# 测试
python tests/test_phase0.py
```

## 项目位置

- 工作区：D:/ai/PiAgent/Skill-safety-guard
- GitHub：https://github.com/Wahero/Skill-safety-guard
- Releases：v0.1.0 ~ v1.5.0（6 个）
