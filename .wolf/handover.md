# Handover — 2026-05-26 Session (部署链路修复完成)

> 部署链路已全部修复。下次 session 无需处理部署问题。

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| HEAD | `de01621` — fix: remove invalid administration:write permission from deploy.yml |
| 远程 | `origin/master` (已推送) |
| Python 测试 | 531 passed, 1 skipped, 6 xfailed |
| 前端测试 | 无 vitest 文件（项目用 Python 测试为主） |
| TypeScript build | `npm run build` clean (18.97s) |
| Dev server | `http://127.0.0.1:3000`（必须用 127.0.0.1，不用 localhost） |
| 生产部署 | ✅ 上线 — HTTP 200 |
| Pages 状态 | `"built"` (workflow-based) |

## 2. 本 Session 完成的工作

### 2.1 部署链路修复 ✅

**问题**: push 触发的 deploy workflow 全部失败（0-2s，0 jobs），但手动 `workflow_dispatch` 成功。

**诊断过程**:
| Commit | 部署结果 | 原因 |
|--------|---------|------|
| `cf897a3` | 失败 (2s) | 环境配置未就绪（transient） |
| `fd09005` | 失败 (2s) | 同上 |
| 手动触发 | 成功 (54s) | workflow_dispatch 绕过部分保护 |
| `2d68bac` | 成功 (45s) | 环境已就绪，push 触发正常 |
| `b8fc27e` | 失败 (0s) | **引入了 `administration: write` 非法权限** |

**根因**: `b8fc27e` 在 `.github/workflows/deploy.yml` 的 permissions 块中加入了 `administration: write`，这不是合法的 GitHub Actions 权限 scope。YAML 解析器在 workflow 评估阶段直接拒绝（HTTP 422: `Unexpected value 'administration'`），导致 0 jobs 被创建。

**修复** (`de01621`): 移除 `administration: write`，只保留 3 个合法权限：
- `contents: read`
- `pages: write`
- `id-token: write`

**验证**: push 触发 workflow 50s 内完成，14/14 step 全部通过。Pages status `"built"`，线上 HTTP 200。

### 2.2 Wolf 文件更新

- `buglog.json` — 新增 bug-005
- `cerebrum.md` — Do-Not-Repeat 新增条目（非法 GitHub Actions 权限）
- `memory.md` — 追加 session 记录
- `handover.md` — 本文件

## 3. 关键 Commit 记录

```
de01621 fix: remove invalid administration:write permission from deploy.yml  ← 部署修复（本次）
b8fc27e fix: switch to Actions-based Pages deployment + add .nojekyll        ← 引入 bug
2d68bac fix: update index.html lang attribute to en for default English locale
fd09005 feat: default English locale + project description on dashboard
cf897a3 chore: update .gitignore + add E2E test plan and deploy checklist
b5bc8ca fix: security hardening + dead code removal + algorithm bug fixes
```

## 4. 当前工作树状态

```
M .wolf/buglog.json      — bug-005 已追加，待 commit
M .wolf/cerebrum.md      — Do-Not-Repeat 新增，待 commit
M .wolf/handover.md      — 本文件，待 commit
M .wolf/memory.md        — session 记录已追加，待 commit
M .wolf/token-ledger.json — pre-commit hook 自动修复的 EOF
?? experiment-engine/    — 空目录，可能是旧 worktree 残留
```

## 5. 快速验证命令

```bash
npm run build              # TypeScript + Vite 构建
uv run pytest --tb=no -q   # Python 测试 (531 passed)
npm run dev                # 启动 dev server (127.0.0.1:3000)
gh run list -b master -l 3 --workflow deploy.yml  # 查看部署状态
gh api repos/qhWangAntoneva/experiment-engine/pages --jq '{status,html_url}'  # Pages 状态
```

## 6. 已知注意事项

- **Dev server**: 必须用 `http://127.0.0.1:3000`，不能用 `localhost`（Pyodide worker 跨域问题）
- **Worker 类型**: ES 模块 Worker (`{ type: 'module' }`)
- **Pyodide**: CDN 加载 (v0.26.4)，不 self-host
- **GitHub Actions 权限**: 只有 `contents/pages/id-token` 三个合法 scope。`administration` 不存在——不要在 deploy.yml 中添加
