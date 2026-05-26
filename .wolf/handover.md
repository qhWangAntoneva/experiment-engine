# Handover — 2026-05-26 Session (i18n English default + GitHub Pages 部署链路修复)

> 下次 session 打开后：读此文件 → 继续解决部署链路阻塞问题

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| HEAD | `b8fc27e` — fix: switch to Actions-based Pages deployment + add .nojekyll |
| 远程 | `origin/master` (已推送) |
| 测试 | 538 collected, 0 failures |
| TypeScript build | `npm run build` clean |
| Dev server | `http://127.0.0.1:3000` (必须用 127.0.0.1，不用 localhost) |
| Worker 类型 | ES 模块 Worker (`{ type: 'module' }`) |
| 生产部署 | 当前未上线 (部署链路中断) |

## 2. 本 Session 完成的工作

### 2.1 功能：默认英文 + 首页项目描述 (已完成 ✅)

| 文件 | 改动 |
|------|------|
| `src/i18n/translations.ts` | `detectLanguage()` fallback `zh` → `en`；新增 `dashboard.description` 中英文 |
| `src/pages/Dashboard.tsx` | page-header 下方新增描述 `<p>` |
| `src/pages/Dashboard.css` | 新增 `.page-desc` 样式 |
| `index.html` | `<html lang="zh-CN">` → `<html lang="en">` |

设计决策：3 agent team (UI 设计师 + 功能设计师 + 评委) — 采纳方案 B (静态描述，最小改动)。

### 2.2 GitHub Pages 部署链路修复 (未完成 ❌)

#### 发现的三层故障

| 层 | 问题 | 修复 | 状态 |
|----|------|------|------|
| **1. Environment branch_policy** | 只允许 `gh-pages` 分支，workflow 在 `master` 运行被拒 | 删旧策略→新增 `master` 策略 (ID: 50278139) | ✅ |
| **2. Pages build_type** | 是 `"legacy"` (Jekyll 构建 gh-pages 分支)，但 workflow 已迁到 Actions API | `gh api --method PUT ... -f build_type="workflow"` | ✅ |
| **3. 最新 workflow 仍被拒绝** | `b8fc27e` 推送后 workflow 0 jobs, 2 秒内失败 | **未解决** | ❌ |

#### 当前 deploy.yml 配置 (b8fc27e)

```
# 已从 peaceiris/actions-gh-pages@v4 切换到官方 Actions 管道:
# configure-pages@v4 → upload-pages-artifact@v3 → deploy-pages@v4

permissions:
  contents: read
  pages: write
  id-token: write
  administration: write  # configure-pages needs this to enable/configure Pages

environment:
  name: github-pages
  url: ${{ steps.deployment.outputs.page_url }}
```

#### 当前 Environment 配置 (API 实测)

```json
{
  "can_admins_bypass": true,
  "protection_rules": [{"id": 55590232, "type": "branch_policy"}],
  "deployment_branch_policy": {
    "custom_branch_policies": true,
    "protected_branches": false
  }
}
```

Branch policy: 仅 `master` (ID: 50278139) — 已确认正确。

```json
{
  "build_type": "workflow",
  "status": "errored",
  "source": {"branch": "gh-pages", "path": "/"}
}
```

## 3. 关键 Commit 记录

```
b8fc27e fix: switch to Actions-based Pages deployment + add .nojekyll    ← 部署失败
2d68bac fix: update index.html lang attribute to en for default English locale
fd09005 feat: default English locale + project description on dashboard
cf897a3 chore: update .gitignore + add E2E test plan and deploy checklist
b5bc8ca fix: security hardening + dead code removal + algorithm bug fixes
```

## 4. 待解决：为什么 workflow 仍被拒绝？

### 已知事实

- **Workflow `b8fc27e`**: conclusion=failure, jobs=[], 无任何 step 执行
- **Workflow `2d68bac`**: conclusion=success (同环境、同 workflow、同 branch_policy)
- `2d68bac` 是通过 `gh workflow run deploy.yml --ref master` 手动触发的
- `b8fc27e` 是通过 `git push` 自动触发的

### 可能的原因

1. **`gh` CLI 触发 vs `git push` 触发有不同权限上下文**：`gh workflow run` 可能以不同身份运行
2. **`can_admins_bypass: true`**：如果 push 的用户不是 repo admin，branch_policy 仍然生效
3. **Pages `status: "errored"`**：Pages 处于错误状态可能导致新的 deployment 被排入队列但无法执行
4. **环境保护规则可能需要额外配置**：GitHub 有时需要手动在 UI 中审批首次 Actions-based deployment

### 建议排查顺序

1. 检查 GitHub Actions 页面 UI 中 `b8fc27e` 的详细拒绝原因（可能有 UI 专用信息）
2. 尝试 `gh workflow run deploy.yml --ref master` 手动触发（看是否和 `2d68bac` 一样成功）
3. 如果手动触发也失败，考虑彻底移除 `environment` 块
4. 检查 https://github.com/qhWangAntoneva/experiment-engine/settings/environments 是否需要额外配置

## 5. 快速验证命令

```bash
# 确认环境配置
gh api repos/qhWangAntoneva/experiment-engine/environments/github-pages/deployment-branch-policies

# 确认 Pages 状态
gh api repos/qhWangAntoneva/experiment-engine/pages --jq '{build_type, status}'

# 手动触发 workflow
gh workflow run deploy.yml --ref master

# 查看最新 workflow
gh run list --branch master --limit 3 --workflow deploy.yml

# 本地构建
npm run build
```
