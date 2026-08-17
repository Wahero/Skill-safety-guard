---
name: False Positive Report
about: 報告 skill-safety-guard 的誤報
title: '[False Positive] '
labels: false-positive
---

## 規則信息

- **規則 ID**: <!-- 例如：shell-curl-bash -->
- **規則名稱**: <!-- 例如：curl piped to bash -->

## 誤報場景

### 觸發誤報的代碼片段

```yaml
# 或 markdown / shell / python 代碼
```

### 為什麼這是誤報

<!-- 解釋為什麼該匹配不應該被視為危險 -->

### 預期的正確行為

<!-- 該代碼應該被允許還是被警告？或規則應該調整？ -->

## 環境信息

- skill-safety-guard 版本: <!-- 例如：v0.1.0 -->
- Pi Agent 版本: <!-- 例如：0.84.2 -->
- 操作系統: <!-- 例如：Windows 11 / macOS 14 / Ubuntu 22.04 -->

## 其他補充

<!-- 其他有助於修復誤報的信息 -->