# Handover — 2026-05-25 Session (BERT+Prototype Phase 3-5 完成)

> 交接给下一 session 的 agent。BERT+Prototype 重构全部 5 阶段完成后，代码与 Web 端的对接是下一步。

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| 远程 | `origin/master` |
| HEAD | `b95d9fe` — feat: Phase 3+4 — BERT worker protocol + UI integration |
| 工作树 | clean |
| 测试 | 515 passed, 1 skipped, 6 xfailed, 0 failures |
| Python lint | ruff clean |
| TypeScript build | `npm run build` clean (28s) |

---

## 2. BERT+Prototype 重构 — 全部 5 阶段完成

| 阶段 | 提交 | 状态 |
|------|------|------|
| Phase 0 | `c5870a2` | ✅ BERT cosine similarity engine + Transformers.js |
| Phase 1 | `003e46e` | ✅ 模型对齐 — PROTOTYPE + 废弃关键词字段 |
| Phase 2 | `c1b8fa1` | ✅ calibrator.py 集成 CosineSimilarityEngine |
| Phase 3 | `b95d9fe` | ✅ Worker 协议 — BERT 消息类型 + BertEngine 集成 |
| Phase 4 | `b95d9fe` | ⚠️ 部分完成 — QCAPipelineContext BERT 状态已加，但 hook/页面未对接 |
| Phase 5 | `b95d9fe` | ✅ 清理 — 删除 keyword_dict/keyword_io/prototype_similarity + 废弃枚举值 |

Phase 3/4/5 合并为单次提交 `b95d9fe`（并行 agent 导致变更交叉）。

---

## 3. 当前各层完成度（代码→Web 对接差距）

```
┌──────────────────────────────────────────────────────────┐
│  Python 后端 (pyodide_handlers.py)                       │
│  handle_embed_calibrate — ✅ 完成                          │
│  CosineSimilarityEngine + calibration 全部就绪             │
├──────────────────────────────────────────────────────────┤
│  Worker (pyodide.worker.ts)                              │
│  initBert/embedCalibrate/computeEmbeddings — ✅ 完成       │
│  BertEngine 集成 + 5 个消息类型全部实现                     │
├──────────────────────────────────────────────────────────┤
│  Bridge (pyodide.ts)                                     │
│  initBert/embedCalibrate/computeEmbeddings — ✅ 完成       │
│  bert-init-progress 拦截修复                               │
├──────────────────────────────────────────────────────────┤
│  Context (QCAPipelineContext.tsx)                         │
│  bertStatus/bertEmbeddingsReady/BERT stages — ✅ 完成      │
│  startBertLoading/finishBertLoading/setBertStatus         │
├──────────────────────────────────────────────────────────┤
│  Hook (useQCAWorkflow.ts)  ← 🔴 缺失                      │
│  无 initBert()、无 runEmbedCalibrate()                     │
│  需要桥接 context + bridge 的 BERT 方法                    │
├──────────────────────────────────────────────────────────┤
│  Pages (DataInput.tsx, Settings.tsx)  ← 🔴 缺失           │
│  无 BERT 加载按钮、无 embed 校准触发、无模型选择器           │
│  仍有 FIXME-BERT 残留注释（需清理）                        │
└──────────────────────────────────────────────────────────┘
```

---

## 4. 下一步：代码与 Web 端对接（最高优先级）

### 4.1 `useQCAWorkflow.ts` — 添加 BERT 方法

需要添加两个方法到 hook 的 interface 和实现：

```typescript
// 接口新增
initBert: (modelName?: string) => Promise<void>;
runEmbedCalibrate: (opts: {
  texts: TextCorpusEntry[];
  conditionSet: ConditionSet;
}) => Promise<void>;
```

**`initBert` 实现逻辑**：
1. `ensureReady()` 确保 Pyodide 就绪
2. `startBertLoading()` → pipeline context
3. `await bridge.initBert(modelName)` → worker 加载 Transformers.js BERT
4. `finishBertLoading()` → pipeline context
5. 错误时 `setBertStatus('error', msg)`

**`runEmbedCalibrate` 实现逻辑**：
1. `getBertStatus()` 检查 BERT 已加载
2. `startEmbedding()` → pipeline context
3. 为每个 condition 构建 `prototypeTextsByCondition: Record<string, string[]>`
4. `await bridge.computePrototypeEmbeddings(prototypeTextsByCondition)` → 获取原型嵌入
5. 将 `prototype_embeddings` 附加到 conditionSet
6. `await bridge.computeEmbeddings(texts)` → 获取文本嵌入
7. 构造 `EmbedCalibrateTextEntry[]`（含 embedding 字段）
8. `await bridge.embedCalibrate(textsWithEmbeds, enrichedConditionSet)`
9. `finishCalibration(result.fuzzyData)`

**关键依赖**：
- `bridge.initBert()` / `bridge.embedCalibrate()` / `bridge.computeEmbeddings()` / `bridge.computePrototypeEmbeddings()` / `bridge.getBertStatus()` — 全部存在于 `pyodide.ts`
- `startBertLoading` / `finishBertLoading` / `startEmbedding` / `finishEmbedding` / `setBertStatus` — 全部存在于 `QCAPipelineContext`
- `EmbedCalibrateTextEntry` — 来自 `../types/qca`

### 4.2 `DataInput.tsx` — BERT 校准 UI

**清理 FIXME-BERT 残留**（共 6 处注释）：
- 移除关键词导入/导出卡片（`FIXME-BERT: Section 0`）
- 移除 `(c as any).keywords?.length` 等引用
- 更新 YAML 模板中的 `keywords:` 示例为 `prototypes:` 示例

**添加 BERT 控制区域**：
1. 「加载 BERT 模型」按钮 — 调用 `initBert()`，显示下载进度
2. BERT 状态指示器 — 显示 unloaded/loading/ready/error
3. 「BERT Embedding 校准」按钮 — 调用 `runEmbedCalibrate()`，显示嵌入计算进度
4. 已有 `isRunning` 状态的扩展，增加 `isBertLoading` / `isEmbedding` 状态

### 4.3 `Settings.tsx` — BERT 模型选择器

在「Engine Status」区域添加：
- BERT 模型下拉选择（默认 `Xenova/bert-base-chinese`）
- 显示当前 BERT 加载状态（从 `pipelineState.bertStatus` 读取）
- 模型信息（维度、大小等）

### 4.4 端到端测试

完成后在浏览器中验证：
1. 打开 DataInput 页面 → 加载 BERT 模型 → 观察进度条
2. 上传文本语料 + 定义条件集（含 prototype 文本）
3. 点击「BERT Embedding 校准」→ 嵌入计算 → 校准完成
4. 查看 Results 页 → fuzzy membership 数据正确

---

## 5. 新增/变更文件清单

### Phase 0 产物（前期）
| 文件 | 用途 |
|------|------|
| `src/experiment_engine/text_calibration/cosine_similarity.py` | CosineSimilarityEngine |
| `src/services/bert-engine.ts` | Transformers.js pipeline |
| `src/services/bert-cache.ts` | IndexedDB 缓存 |
| `src/types/bert.ts` | BERT 类型定义 |
| `tests/test_cosine_similarity.py` | cosine similarity 测试 |

### Phase 3-5 产物（本次）
| 文件 | 用途 |
|------|------|
| `src/services/pyodide.worker.ts` | +5 BERT handler + BertEngine 集成 |
| `src/services/pyodide.ts` | +5 BERT bridge 方法 + progress fix |
| `src/types/qca.ts` | +EmbedCalibrateTextEntry + BERT 消息类型 |
| `src/store/QCAPipelineContext.tsx` | +BERT 状态管理 |

### 已删除文件（Phase 5）
- `keyword_dict.py`, `keyword_io.py`, `prototype_similarity.py`
- `test_keyword_io.py`, `test_prototype_similarity.py`

---

## 6. 关键教训

### 新增（本 session）

**并行 agent 写同一文件导致 UI 层变更丢失**: Phase 4 agent（UI 集成）和 Phase 5 agent（清理）并行运行，都修改了 `useQCAWorkflow.ts`/`DataInput.tsx`/`Settings.tsx`。Phase 5 的删除操作覆盖了 Phase 4 的添加操作，导致 BERT UI 代码全部丢失。教训：有共享文件依赖的 agent 必须串行执行，或用 worktree 隔离后手动 merge。

**agent "完成"声明必须用 git diff --stat 验证**: Phase 4 agent 报告完成，但 `useQCAWorkflow.ts` 中无任何 BERT 方法，DataInput.tsx 中无 BERT UI。未严格验证 agent 更改导致漏检。

**pre-commit end-of-file-fixer 会导致首次 commit 失败**: Windows 下 agent 编辑的文件可能缺少尾随换行符。commit 前需先运行一次 hooks 或接受首次失败后 re-add。

### 前期（仍然有效）

- Subagent 虚构完成不可信 — 必须 `git diff --stat` 验证
- L 级任务拆为多 agent 并行，每个负责不相交的文件集合
- 前端质量门禁用 `npm run build`，Python 用 pytest + ruff
- 简单任务不用 worktree 隔离

---

## 7. 环境快速检查

```bash
# 确认在 master 分支
git branch && git status --short

# 确认远程同步
git fetch origin && git log origin/master --oneline -5

# 构建验证
npm run build 2>&1 | tail -3
uv run pytest --co -q 2>&1 | tail -3
ruff check src/experiment_engine/ 2>&1 | tail -3
```
