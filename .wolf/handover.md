# Handover — 2026-05-25 Session (BERT+Prototype 重构)

> 本文件交接给下一 session 的 agent，包含当前状态、已完成工作、剩余工作和关键教训。

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| 远程 | `origin/master` |
| HEAD | `003e46e` — refactor: Phase 1 — model alignment for BERT+Prototype |
| 工作树 | `.wolf/*` 文件未提交 + `src/i18n/translations.ts` 有未暂存变更 |
| 测试 | 577 collected, 561 passed, 16 failed, 6 xfailed |
| Python lint | ruff clean |
| TypeScript build | `npm run build` passes |

---

## 2. 本 session 完成的工作

### BERT+Prototype 架构重构 (新需求)

| 提交 | 阶段 | 说明 |
|------|------|------|
| `c5870a2` | Phase 0 | feat: BERT cosine similarity engine + Transformers.js services (5新文件, 577通过) |
| `003e46e` | Phase 1 | refactor: model alignment — ScoringSource→PROTOTYPE, keywords字段移除, prototype_embeddings新增 (561通过, 16预期失败) |

### 前期 P1 完成项（本 session 之前）

| 提交 | 说明 |
|------|------|
| `d61d96e` | feat: P1-31 — Result 页 raw-prototype 对比视图 |
| `b597547` | fix: reviewer corrections for P1-31 |
| `7b102f9` | feat: P1-1 + P1-2 — 关键词词典导入/导出 + .xlsx 支持 |
| `41e81d2` | feat: P1-3 — QCA 结果自然语言解读 |
| `81cc862`~`200f0a9` | feat: P1-4 — 完整中文界面翻译 |

**已推送**：全部 10 个提交已推送到 origin/master。

---

## 3. BERT+Prototype 重构 — 5 阶段实施计划

### 核心决策
- **废弃关键词识别方案**，Prototype 理论是 QCA 的唯一理论基础
- 架构方案：**Hybrid Transformers.js + Pyodide**（Option D）
- 模型：`bert-base-chinese`（ONNX int8 ~100MB），后续支持模型切换
- 算法：Mean Pooling + Centroid Aggregation + Softmax(τ=5.0)
- 详细规范：`.wolf/bert-prototype-algorithm-spec.md`（640 行完整算法设计）

### 已完成阶段

| 阶段 | 状态 | 提交 | 关键变更 |
|------|------|------|---------|
| **Phase 0** | ✅ 完成 | `c5870a2` | `cosine_similarity.py` (427行) + `bert-engine.ts` (243行) + `bert-cache.ts` (427行) + `bert.ts` (63行) + 52 新测试 |
| **Phase 1** | ✅ 完成 | `003e46e` | `qca.py`: ScoringSource (PROTOTYPE为主, KEYWORD/HYBRID废弃), ConditionDefinition (keywords移除, prototype_embeddings新增); `qca.ts` 同步; `translations.ts` (21关键词字符串移除, BERT字符串新增) |

### 下一 session 必须完成

| 阶段 | 优先级 | 风险 | 说明 |
|------|--------|------|------|
| **Phase 2** | 🔴 P0 | 中 | calibrator.py 重构 — 移除关键词路径，集成 CosineSimilarityEngine |
| **Phase 3** | 🔴 P0 | 中-高 | Worker 协议扩展 — 并行加载 Pyodide+BERT，新消息类型 |
| **Phase 4** | 🔴 P0 | 中 | UI 集成 — QCAPipelineContext, DataInput.tsx, Settings.tsx |
| **Phase 5** | 🟡 P1 | 低 | 清理 — 删除 keyword_dict.py, keyword_io.py, PrototypeSimilarityEngine |

### Phase 2 详细范围（最高优先级）

```
文件修改:
- src/experiment_engine/text_calibration/calibrator.py — 核心重构:
  * 移除 _precompute_kw_context(), ChineseKeywordDictionary 导入
  * _compute_raw_scores() 统一走 CosineSimilarityEngine
  * process/process_with_outcome/calibrate_one 适配嵌入输入
- src/experiment_engine/text_calibration/__init__.py — 更新导出
- src/experiment_engine/pyodide_handlers.py — 新增 embedding handler
- tests/ — 修复 16 个失败测试，新增 cosine pipeline 集成测试

文件不修改:
- src/experiment_engine/qca_engine/* — 完全校准源无关
- src/experiment_engine/text_calibration/strategies.py — 校准策略不变
```

### 新增文件清单（Phase 0 产物）

| 文件 | 行数 | 用途 |
|------|------|------|
| `src/experiment_engine/text_calibration/cosine_similarity.py` | 427 | CosineSimilarityEngine — softmax/diff 公式 + centroid/max 聚合 |
| `src/services/bert-engine.ts` | 243 | BertEngine — Transformers.js pipeline + mean pooling + L2 norm |
| `src/services/bert-cache.ts` | 427 | BertCache — IndexedDB 三层存储（原型/文本/模型元数据） |
| `src/types/bert.ts` | 63 | BERT 类型定义 + Worker 消息协议 |
| `tests/test_cosine_similarity.py` | 1043 | 52 测试，10 个测试类 |
| `.wolf/bert-prototype-algorithm-spec.md` | 640 | 完整算法规范 |

---

## 4. P1 功能需求状态

### 已完成
- [x] P1-31: raw-prototype 对比视图
- [x] P1-1: 关键词词典导入/导出
- [x] P1-2: Excel 文件支持
- [x] P1-3: QCA 结果自然语言解读
- [x] P1-4: 中文界面

### 剩余（BERT 重构完成后再推进）

| 任务 | 工作量 | 来源 |
|------|--------|------|
| P1-5 | 个案级校准结果展示 | M | 客户#P5 |
| P1-6 | 项目保存与恢复 | L | 客户#F1 |
| P1-7 | 参数对比 / A/B 分析 | L | 客户#F2 |
| P1-8 | 隐私声明 | S | 客户#D1 |
| P1-9 | Recent Runs 真实数据 | S | 客户#U1 |
| P1-10 | 校准参数即时预览 | M | 客户#U2 |
| P1-11 | 中文 Word 报告导出 | M | 客户#F4 |
| P1-12 | 多结果变量分析 | L | 客户#F5 |
| P1-13 | 条件集共享与团队模板 | M | 客户#C1 |
| ~~P1-34~~ | ~~预置词典在线编辑器~~ | - | **已废弃（关键词功能移除）** |

---

## 5. 关键教训

### 5.1 新增教训（本 session）

**BERT 架构决策推翻**: cerebrum.md 中此前记录了 "BERT 作为辅助工具不做主引擎" 的决策。用户在本 session 明确推翻了该决策，要求用 BERT+Prototype 完全替代关键词识别。处理方式：
- 在 cerebrum.md Key Learnings 中标注 `🔄 决策已推翻`
- 保留旧记录供参考，新决策写在下方

**Phase 1 模型变更的策略选择**: ScoringSource 枚举不能直接删除 KEYWORD/HYBRID 值（会破坏 8 个文件 + 16 个测试的导入/运行时），而是保留并标记为 deprecated。真正的移除在 Phase 5（清理阶段）执行。这避免了阶段间的大规模连锁错误。

**Pref 让 subagent 并行而不是自己顺序编辑**: 用户明确要求用 subagent 而非手动编辑。Phase 1 的 3 个文件修改应该一开始就派 3 个 agent 并行执行。

### 5.2 前期教训（仍然有效）

**Subagent 虚构完成**: 不要信任 agent 的"完成"声明。始终通过 `git diff --stat` 验证实际变更。

**大任务应拆成多 agent 并行**: L 级任务拆分为多个文件级别的子任务，每个 agent 负责不相交的文件集合。

**慢速 Reviewer 问题**: 前端任务用 `npm run build`，Python 任务用 `uv run pytest` + `ruff check` 作为主要质量门禁。完整 reviewer agent 仅对关键算法任务使用。

**Worktree 隔离陷阱**: 简单任务不用 worktree。agent 如果在 worktree 中工作，检查 worktree 分支上的 actual commits。

---

## 6. 下一 session 推荐开工顺序

1. **Phase 2 — calibrator.py 重构**（最高优先级）
   - 移除关键词预计算逻辑
   - 集成 CosineSimilarityEngine
   - 修复 16 个测试失败
   - 新增 embedding-based calibrate handler
2. **Phase 3 — Worker 协议扩展**
   - pyodide.worker.ts 新增 BERT 消息类型
   - 并行加载 Pyodide + BERT
3. **Phase 4 — UI 集成**
   - QCAPipelineContext + useQCAWorkflow embedding 状态
   - DataInput.tsx 移除关键词 UI
   - Settings.tsx BERT 模型选择器
4. **Phase 5 — 清理**
   - 删除 keyword_dict.py, keyword_io.py, prototype_similarity.py
   - 移除 deprecated 枚举值

> P1 功能需求（P1-5~P1-13）在 BERT 重构完成后再推进。

---

## 7. 环境快速检查清单

```bash
# 确认在 master 分支
git branch && git status --short

# 确认远程同步
git fetch origin && git log origin/master --oneline -5

# 构建验证
npm run build 2>&1 | tail -5
uv run pytest --co -q 2>&1 | tail -3
ruff check src/experiment_engine/ 2>&1 | tail -3
```
