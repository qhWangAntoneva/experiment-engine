# Handover — 2026-05-26 Session (Load Engine Bug Fix)

> 交接给下一 session 的 agent。"加载引擎"按钮闪回 bug 已修复，Dashboard 错误状态可见化，bridge 鲁棒性增强。待浏览器端到端验证。

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| 远程 | `origin/master` (not pushed) |
| HEAD | `eba4e1f` — feat: Phase 4 (UI) — BERT controls in DataInput + model selector in Settings |
| 未提交变更 | 17 files modified (本次 session 修复 + 上轮 E2E 修复) |
| 测试 | 522 collected, 0 failures |
| TypeScript build | `npx tsc --noEmit` clean |
| Dev server | `http://127.0.0.1:3000` (⚠️ 必须用 127.0.0.1，不用 localhost) |
| Worker 类型 | **ES 模块 Worker** (`{ type: 'module' }`) |
| Pyodide 加载方式 | **动态 `import()`** 加载 `pyodide.mjs` (ES 模块版本) |

---

## 2. 本 Session 完成的工作

### 2.1 "加载引擎"按钮闪回 Bug 修复 (P0)

**用户报告**: 点击 Dashboard 的"加载引擎"按钮，按钮短暂显示"加载中..."后立即恢复为"加载引擎"，引擎状态仍显示"未加载"。

**诊断过程 (4-agent expert team)**:
- Architect agent: 分析完整的 `init()` → `createWorker()` → `onmessage` 代码流
- UX Tester agent: 创建 45 项 E2E 测试计划 (6 Phase)
- QA Engineer agent: 设计 9 个优先级排序的边缘用例
- Bug Hunter agent: 定位根因

**根因**: 模块 Worker (`{ type: 'module' }`) 中调用了 `importScripts()` —— 该 API 在模块 Worker 中不存在（HTML 规范），立即抛出 `TypeError`。同时 Dashboard UI 对 `error` 和 `unloaded` 状态显示相同文案（同一个 ternary else 分支），完全掩盖了错误。

**修复（第二轮正确方案）**:

| 文件 | 变更 | 说明 |
|------|------|------|
| `pyodide.worker.ts:204` | `importScripts('...pyodide.js')` → `await import('...pyodide.mjs')` | 动态 import Pyodide ES 模块 |
| `pyodide.worker.ts:205` | 新增 `const { loadPyodide } = pyodideModule;` | 从模块解构 loadPyodide |
| `vite.config.ts:23` | `format: "iife"` → `format: "es"` | 保持 ES 模块 Worker |
| `pyodide.ts:374` | `{ type: 'module' }` | 保持模块 Worker 创建 |

> ⚠️ 第一轮修复尝试了 classic/IIFE worker + `importScripts()` 方案，导致 `Uncaught SyntaxError: Cannot use import statement outside a module`。因为 `pyodide.js` 内部使用了 ES module 语法，`importScripts` 无法加载。**正确方案是保持模块 Worker + 动态 `import()` 加载 `pyodide.mjs`。**

### 2.2 Dashboard 错误状态可见化

| 文件 | 变更 |
|------|------|
| `Dashboard.tsx:31-36` | Metric card value 显式区分 `error` / `unloaded` / `loading` / `ready` |
| `Dashboard.tsx:120-123` | 按钮在 error 状态显示 `step1BtnError` ("重试（错误）")，class 变 `btn-danger` |
| `Dashboard.tsx:125-129` | 新增红色错误横幅，显示 `initState.error` 消息 |
| `Dashboard.css:42-44` | 新增 `.metric-critical` CSS 类（红色左边框） |
| `translations.ts` | 新增 4 个 key: `statusError` / `step1BtnError` (zh + en) |

### 2.3 Bridge 鲁棒性增强

| 文件 | 变更 | 说明 |
|------|------|------|
| `pyodide.ts:384-390` | `init-done`/`init-error` 用 `break` 替代 `return` | 确保 `resolveOne()` 清理 pending request，防止 FIFO corruption |
| `pyodide.ts:96-99` | 新建 Worker 前终止旧 Worker | 防止 zombie worker 累积 |
| `pyodide.ts:103-108` | `createWorker()` 包裹 try-catch | Worker 创建失败时恢复 error 状态（之前 stuck on 'loading'） |
| `pyodide.ts:84,88` | "already loading" 路径 listener 清理 | 修复 listener 泄漏 |

### 2.4 验证结果 (explorer + fixer + reviewer team)

| Agent | 验证项 | 结果 |
|-------|--------|------|
| Explorer | 26 项代码 + 路由测试 | **26 PASS** |
| Fixer | 待命修复 | 无需修复 |
| Reviewer | 21 项独立审计 | **21 PASS** |

所有 5 个路由 (`/`, `/dashboard`, `/input`, `/results`, `/settings`) 返回 HTTP 200。

---

## 3. 修复前后对比

```
修复前:
  点击"加载引擎" → button flash "加载中..." → 立即回到"加载引擎" + "未加载"
  原因: importScripts() TypeError → init-error → UI 掩盖 error 状态

修复后:
  点击"加载引擎" → button 显示"加载中..." + 进度条 → 30-60s → "引擎就绪"
  若失败: button 显示"重试（错误）" + 红色边框 + 错误消息横幅
```

---

## 4. 下一步：浏览器端到端验证（最高优先级）

### 4.1 启动方式

```bash
cd "C:\Users\lenovos\QCA Analysis Tool"
npx vite --port 3000 --host 127.0.0.1
```

浏览器打开 **http://127.0.0.1:3000**（⚠️ 不是 localhost）

### 4.2 验证清单

1. 打开 `http://127.0.0.1:3000/` → 确认重定向到 `/dashboard`
2. 点击「加载引擎」→ 按钮变为"加载中..."并显示进度条 → ~30-60s 后变为"引擎就绪"
3. 侧边栏切换中英文 → 确认所有文本切换（包括新增的 error 状态 key）
4. Dashboard metric card 显示 "就绪" (zh) / "Ready" (en)
5. Navigation → Settings → 修改设置 → 保存 → 刷新 → 确认持久化
6. Settings → 选择 BERT 模型 → 点击加载 → 刷新 → 确认模型选择保持
7. Navigation → DataInput → 粘贴测试语料 CSV → 解析
8. 粘贴 prototype CSV → 解析
9. 点击「Calibrate」→ 确认校准完成 + DistributionPlot 显示
10. 点击「Run Full Pipeline」→ 自动跳转 Results → 查看全部标签页
11. 加载 BERT 模型 → 点击「BERT Embedding 校准」
12. 导出关键词字典（Settings → Export Keyword Dictionary）

### 4.3 错误场景测试

- Chrome DevTools Network tab → 右键 block `cdn.jsdelivr.net` → 点击"加载引擎" → 确认显示红色错误横幅 + "重试（错误）"按钮
- 解除 block → 再次点击 → 确认恢复加载

### 4.4 测试数据

**文本语料 (CSV)**:
```
id, text
case_01, "The government response was very fast and effective"
case_02, "I am extremely dissatisfied with the poor service"
case_03, "建议政府提高办事效率"
case_04, "严重怀疑政策能否执行到位"
case_05, "满意，已解决问题"
```

**Prototype CSV**:
```
编号, 文本内容, 结果
1, 政府第一时间回应了群众诉求, 1
2, 问题处理非常迅速有效, 1
3, 多次投诉仍没有答复, 0
4, 办事人员态度差效率低, 0
```

---

## 5. 变更文件清单

| 文件 | 变更 | 状态 |
|------|------|------|
| `src/services/pyodide.worker.ts` | importScripts → dynamic import() + JSDoc 更新 | unstaged |
| `src/services/pyodide.ts` | init-done/init-error break 替代 return; worker cleanup; createWorker try-catch; listener leak fix | unstaged |
| `vite.config.ts` | worker.format 注释更新 | unstaged |
| `src/pages/Dashboard.tsx` | error 状态可见化 (metric/button/banner) | unstaged |
| `src/pages/Dashboard.css` | .metric-critical CSS class | unstaged |
| `src/i18n/translations.ts` | +4 新 key (statusError/step1BtnError zh+en) + 类型定义 | unstaged |
| `src/hooks/usePyodide.ts` | getInitState → getInitState() (上轮修复) | unstaged |
| `src/pages/DataInput.tsx` | BERT i18n + BERT UI 修复 (上轮) | unstaged |
| `src/pages/Settings.tsx` | BERT model selector + localStorage + exportKeywords (上轮) | unstaged |

---

## 6. 关键教训

### 本次 session

- **模块 Worker 不支持 `importScripts()`**：HTML 规范明确禁止。在模块 Worker 中加载外部脚本必须使用动态 `import()`。
- **Pyodide 提供两种构建**：`pyodide.js` (classic script, 用于 `<script>` 或 classic worker 的 `importScripts`) 和 `pyodide.mjs` (ES 模块, 用于 module worker 的 `import()`)。必须根据 Worker 类型选择正确的构建。
- **`importScripts()` 不能加载 ES 模块脚本**：即使 classic worker 中 `importScripts()` 可用，被加载的脚本也不能包含 `import`/`export` 语句。
- **UI 掩盖错误比错误本身更糟糕**：Dashboard 的 ternary 对 `error` 和 `unloaded` 使用同一个 else 分支，导致用户完全不知道出了什么问题。所有状态枚举必须显式处理。
- **4-agent expert team 有效**：Architect + UX Tester + QA Engineer + Bug Hunter 并行诊断，20 分钟内定位根因并创建完整测试计划。
- **Explorer+Fixer+Reviewer 双层质量门有效**：explorer 验证 26 项 → reviewer 独立审计 21 项 → 发现 2 个次要问题（stale comment + 类型定义 gap）并修复。

### 前期（仍然有效）

- Subagent 虚构完成不可信 — 必须 `git diff --stat` 验证
- L 级任务拆为多 agent 并行，每个负责不相交的文件集合
- 前端质量门禁用 `npm run build`，Python 用 pytest + ruff
- 并行 agent 修改共享文件导致变更丢失（Phase 4/5 事故）
- pre-commit end-of-file-fixer 每次都会 fail 第一次 commit
- localhost vs 127.0.0.1 代理陷阱：Clash 代理拦截 Chrome 的 localhost 请求

---

## 7. 环境快速检查

```bash
# 确认在 master 分支
git branch && git status --short

# 构建验证
npx tsc --noEmit 2>&1
uv run pytest --co -q 2>&1 | tail -3

# 启动 dev server（必须 127.0.0.1！）
npx vite --port 3000 --host 127.0.0.1
```
