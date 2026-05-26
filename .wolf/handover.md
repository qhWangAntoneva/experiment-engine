# Handover — 2026-05-26 Session (安全修复 + 架构清理 + 核心算法验证)

> 交接给下一 session 的 agent。6 项已知问题已修复，3 项细节修复，4 项算法 Bug 修复，全部经 reviewer 验收通过。

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| HEAD | `3544606` — fix: Pyodide worker engine load + GitHub Pages deploy readiness |
| 远程 | `origin/master` (已推送) |
| 测试 | **538 collected, 0 failures** (+16 new robustness tests) |
| TypeScript build | `npx tsc --noEmit` clean, `npm run build` clean |
| Dev server | `http://127.0.0.1:3000` (⚠️ 必须用 127.0.0.1，不用 localhost) |
| Worker 类型 | **ES 模块 Worker** (`{ type: 'module' }`) |
| **生产部署** | **https://qhWangAntoneva.github.io/experiment-engine/** |

---

## 2. 本 Session 完成的工作

### 2.1 安全修复 (3 项)

| # | 文件 | 修复 |
|---|------|------|
| SEC-1 | `package.json` | 添加 `overrides: {"protobufjs": "7.5.9"}` 解决 9 个 CVE |
| SEC-2 | `pyodide.worker.ts`, `bert-engine.ts` | 添加 CDN SRI 不可行的 SECURITY NOTE + Pyodide 运行时版本检查 |
| SEC-3 | `index.html` | 添加 CSP meta 标签（含开发模式 HMR 警告注释） |

### 2.2 架构清理 (3 项)

| # | 文件 | 修复 |
|---|------|------|
| ARCH-1 | `src/pyodide/engine.ts` | **删除** — 340 行死代码，零引用 |
| ARCH-2 | `core/__init__.py` | parallel.py 导入用 try/except ImportError 保护 + `__getattr__` 提供清晰错误 |
| ARCH-3 | `pyodide_handlers.py` | QCALaTeXReporter 导入改为惰性加载 + 浏览器端 LaTeX 导出返回清晰错误 |

### 2.3 核心算法验证 (3-Role Agent Team)

| 角色 | 产出 |
|------|------|
| **文本设计师** | 4 个测试数据文件: 标准 15 条、边缘 10 条、小N 5 条、自定义条件集 YAML |
| **运算观察者** | 563 项测试验证: 校准/QM/真值表/数值稳定性全部通过，**发现 1 个 Bug** (keywords 字段缺失) |
| **严厉评委** | 6 项方法论合规审计: 全部合规，**发现 2 个 Bug** (robustness 静默损坏、校准归一化)，1 个缺陷 (无单元测试) |

### 2.4 算法 Bug 修复 (4 项)

| # | 严重性 | 文件 | 修复 |
|---|--------|------|------|
| Bug-1 | **CRITICAL** | `models/qca.py:151` | 添加 `keywords: list[KeywordEntry]` 字段 — 200+ 领域关键词不再被 Pydantic 静默丢弃 |
| Bug-2 | **HIGH** | `robustness.py:33-71` | `_compute_term_membership` 条件名不匹配时添加 `warnings.warn()`（匹配 sufficiency.py FIXME-13） |
| Bug-3 | MEDIUM | `strategies.py:59-72` | min-max 归一化行为添加详细方法论文档 |
| Bug-4 | MEDIUM | `tests/test_robustness.py` | **新建** 16 个单元测试覆盖全部稳健性方法 |

---

## 3. 未提交的变更文件清单

| 文件 | 变更 |
|------|------|
| `package.json` | +overrides: protobufjs@7.5.9 |
| `package-lock.json` | 同步 override |
| `index.html` | CSP meta 标签 + 开发模式 HMR 警告注释 |
| `src/pyodide/engine.ts` | **删除** (ARCH-1) |
| `src/pyodide/types.ts` | 移除死重导出，替换为解释性注释 |
| `src/services/pyodide.worker.ts` | SECURITY NOTE + 运行时 Pyodide 版本检查 |
| `src/services/bert-engine.ts` | SECURITY NOTE |
| `src/experiment_engine/core/__init__.py` | ImportError guard + `__getattr__` |
| `src/experiment_engine/pyodide_handlers.py` | LaTeX 导出惰性导入 + 死代码行移除 |
| `src/experiment_engine/models/qca.py` | +keywords: list[KeywordEntry] 字段 |
| `src/experiment_engine/qca_engine/advanced/robustness.py` | +import warnings + 条件名不匹配警告 |
| `src/experiment_engine/text_calibration/strategies.py` | min-max 归一化方法论文档 |
| `tests/test_robustness.py` | **新建** — 16 个稳健性单元测试 |
| `tmp/test_dataset_*` | 文本设计师产出 — 30 条测试数据 |
| `tmp/test_condition_set.yaml` | 自定义条件集 |
| `.wolf/*` | anatomy, buglog, cerebrum, memory, handover, token-ledger |

---

## 4. 关键教训 (本 session)

### 新教训

- **3-role agent team 对算法审计极其有效**: 文本设计师模拟真实用户、运算观察者逐步追踪计算管道、严厉评委对照方法论标准审计——三者互补，发现了一个 CRITICAL bug（200+ 关键词被静默丢弃）和一个 HIGH bug（robustness 静默数据损坏），这些是代码审查遗漏的。
- **新测试文件必须适配现有 API 约定**: `QCAnalyzerStage` 需要 `setup()` 后才能调用 `analyze()`，测试中直接 new 不 setup 会导致 `NoneType` 错误。写测试前先读现有测试代码了解 API 约定。
- **Pydantic 静默丢弃多余字段是常见陷阱**: `ConditionDefinition(**data)` 当 data 含未定义字段时，Pydantic 默认静默忽略（无 warning）。`build_default_conditions` 传了 `keywords=keywords` 但模型没有这个字段 → 所有关键词丢失。Pydantic v2 的 `model_config = ConfigDict(extra='forbid')` 可以防止此类问题。
- **`__getattr__` 在 Python 模块中仅在属性完全不存在时触发**: 如果 except 块把名字绑定到 `None`（进入 `__dict__`），则 `__getattr__` 永远不会被调用。正确做法是 except 块不绑定名字，让 `__getattr__` 拦截访问。

### 前期（仍然有效）

- Subagent 虚构完成不可信 — 必须 `git diff --stat` 验证
- FIXER 完成后等待 5-10 秒再启动 REVIEWER（文件系统 race condition）
- 并行 agent 修改共享文件导致变更丢失
- 模块 Worker 不支持 `importScripts()`
- Pyodide 中严禁 JS 模板字面量注入 Python 代码
- localhost vs 127.0.0.1 代理陷阱
- UI 掩盖错误比错误本身更糟糕

---

## 5. 环境快速检查

```bash
# 确认在 master 分支
git branch && git log --oneline -1

# 构建验证
npm run build 2>&1 | tail -3
npx tsc --noEmit

# 测试验证 (538 collected)
uv run pytest --co -q 2>&1 | tail -3

# 新稳健性测试
uv run pytest tests/test_robustness.py -v

# 启动 dev server（必须 127.0.0.1！）
npx vite --port 3000 --host 127.0.0.1

# 生产部署
# URL: https://qhWangAntoneva.github.io/experiment-engine/
```
