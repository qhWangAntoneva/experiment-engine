# QCA Analysis Tool — Project Status (2026-05-27 Session 3)

> BERT embeddings → fuzzy calibration → QCA truth table → solutions.

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| HEAD | `afa6c77` — fix: mountFromInline 创建空包目录导致 dev 模式 ModuleNotFoundError |
| 分支 | `master` |
| 本地改动 | (无) |
| 远程同步 | `origin/master` ✅ 完全同步 |

## 2. 本轮完成 (Session 3)

| 任务 | 描述 | 状态 |
|------|------|------|
| **Track A: 验证部署源** | 确认 Pages 从 Actions artifact 提供服务，最新代码(ec02dc5)已上线，CSP正确，worker JS包含所有5个包 | **已完成** |
| **Track B: 本地复现崩溃** | 通过 Playwright 在本地复现 30 样本崩溃，捕获完整错误链 | **已完成** |
| **修复 mountFromInline()** | 创建 Vite plugin 提供 `/py/modules.json`，worker 获取 JSON 并写入实际 Python 源文件到 VFS | **已完成** |
| **修复 deploy.yml manifest** | `packages` 数组补充 `"micropip"` 和 `"rich"` | **已完成** |
| **增强 worker 错误可视化** | 在 `pyodide.ts` 的 3 个错误路径添加 `console.error()` | **已完成** |

### 关键发现

1. **部署源正确** — 线上版本已包含所有4个修复（pydantic, CSP, worker error, rich），worker JS asset是有效JS非HTML
2. **崩溃根因** — `mountFromInline()` 仅创建空Python包目录，不写入实际源文件（如 `pyodide_handlers.py`），导致 `ModuleNotFoundError: No module named 'experiment_engine.pyodide_handlers'`
3. **错误不可见** — worker 错误通过 `postMessage` → React state 传递，未调用 `console.error()`，在浏览器控制台中完全不可见
4. **生产环境不受影响** — CI 生成的 `experiment_engine.tar.gz` 在工作流中已排除此问题，仅 dev 模式受影响

### 修复内容

| 文件 | 变更 |
|------|------|
| `scripts/vite-plugin-pyodide-modules.ts` | **新建** — Vite plugin，dev 模式下在 `/py/modules.json` 提供所有 Python 源文件 |
| `vite.config.ts` | 注册 `pyodideModulesPlugin()` |
| `src/services/pyodide.worker.ts` | `mountFromInline()` 改为获取 `/py/modules.json` 并写入实际 Python 文件到 VFS |
| `src/services/pyodide.ts` | 3 个错误路径添加 `console.error()` |
| `.github/workflows/deploy.yml` | manifest `packages` 补充 `micropip`, `rich` |

## 3. 推荐下一步

1. **验证线上** — CI 完成部署后访问 GitHub Pages 确认正常
2. **清理 Playwright 诊断脚本** — `tmp/reproduction_diag*.mjs`、`capture_*.mjs`、`minimal_test.mjs` 可删除
