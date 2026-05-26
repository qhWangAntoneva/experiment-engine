# Handover — 2026-05-26 Session #2 (P1-10 + P1-5)

> 本轮完成 2 项 P1 功能需求 + subagent 并行工作流验证。Phase 3 (P1-B7/B8) 方案已设计，待下一 session 实现。
> 工作模式：主 session 仅做汇总/commit，规划→Plan agent，执行→Fixer agent，审查→Reviewer agent。

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| HEAD | `1379154` — feat: P1-5 — case-level calibration display with interactive table |
| 远程 | `origin/master` (已推送) |
| Python 测试 | 532 passed, 1 skipped, 6 xfailed |
| TypeScript build | `npm run build` clean |
| Dev server | `http://127.0.0.1:3000`（必须用 127.0.0.1，不用 localhost） |

## 2. 本 Session 完成的工作

### 2.1 P1-10 — 校准参数即时预览 (98afe2d)

**新建** `src/components/CalibrationPreview.tsx`：JS 端校准公式（direct/indirect/ragin/crisp）完全镜像 Python `strategies.py`。3 种合成样本分布（正态/均匀/双峰）供预览。Plotly 双直方图（原始分数 + 校准后隶属度）80ms 防抖。汇总统计条（平均隶属度、%完全不属于、%完全属于、%交叉点）。

**修改** `src/pages/Settings.tsx`：Calibration Defaults 区域下方插入 CalibrationPreview 卡片。参数变化实时反映。

**额外修复**：TODO.md 补打 P1-8/P1-9 完成勾（上轮遗漏），更新统计 P1 11→8。

### 2.2 P1-5 — 个案级校准结果展示 (1379154)

**新建** `src/components/CaseMembershipTable.tsx`：排序/筛选/展开功能完整的案例隶属度表格。列：Case ID + 文本预览(80字符省略) + 各条件隶属度分数(颜色渐变红→黄→绿) + 结果分数。文本搜索 + 条件范围筛选（min/max inputs）。点击行展开显示完整原文。

**修改** `src/pages/Results.tsx`：新增 "Cases" 标签页（位置 #2，Solutions 和 Truth Table 之间）。数据来自 `state.fuzzyData`/`state.prototypeFuzzyData`，无需 QCA 分析完成即可看到案例数据。viewMode 切换自动切换数据源。

**Reviewer 发现并修复的 Bug**：
- 颜色渐变蓝通道在 score=0.5 处不连续（修正为 const b=80）
- 3 处硬编码 "(no text)" 改为 i18n `t('results.caseNoText')`

### 2.3 Phase 3 (P1-B7/B8) 方案设计

Plan agent 已完成完整设计（未实现）。概要：

**P1-B7 模型切换支持**：
- 修复 `useQCAWorkflow.ts:184` 的 `embedding_model` 硬编码为 `'Xenova/bert-base-chinese'` 的 bug
- 模型切换时自动清除旧的 `prototype_embeddings`（标记为 null）
- `QCAPipelineContext` 新增 `bertModelName` 状态追踪
- Settings 页显示 "嵌入已失效" 警告

**P1-B8 性能监控面板**：
- `BertEngine` 新增 6 个性能计数器（`performance.now()` 打点）
- Worker 新增 `get_bert_stats` 消息处理
- Settings 页新增可折叠性能面板（模型加载耗时、平均推理耗时、缓存命中率等 7 项指标）
- `PyodideBridge` 新增 `getBertStats()` 方法

涉及约 10 个文件，详见下轮 session 的 Plan agent 输出。

## 3. 关键提交记录

```
1379154 feat: P1-5 — case-level calibration display with interactive table  ← 本次
98afe2d feat: P1-10 — calibration parameter instant preview with Plotly    ← 本次
271d45b feat: P2-20 + P2-22 — k configurable + --variant for train/robustness
1186356 feat: P1-8 + P1-9 — Privacy section + Recent Runs from localStorage
ba36d86 fix: add trailing newline to writeJSON output in shared.js
```

## 4. 当前 TODO 状态

| 优先级 | 剩余 | 备注 |
|--------|------|------|
| P0 | **0** | 全部完成 |
| P1 | **7** | P1-B7/B8 (模型切换+性能) + P1-6/7/11/12/13 (功能需求) |
| P2 | **21** | 全部未开始 (P2-20, P2-22 除外) |
| **合计** | **28** | ↓ 从 34 |

**下一步推荐**（按优先级）：
1. **P1-B7 + P1-B8** — 模型切换支持 + 性能监控面板（方案已完成，约 10 文件，可直接实现）
2. **P1-6** — 项目保存与恢复（L，一键保存/加载 .qca JSON + localStorage）
3. **P1-13** — 条件集共享与团队模板（M，分享链接 + 模板库）
4. **P1-11** — 中文 Word 报告导出（M，.docx 含图表）
5. **P1-7** — 参数对比 / A/B 分析（L，两组参数并排对比）
6. **P1-12** — 多结果变量分析（L，Web 界面多 outcome 支持）

## 5. 架构变更摘要

### 新增文件
- `src/components/CalibrationPreview.tsx` — JS 校准公式 + Plotly 预览（~230 tok）
- `src/components/CaseMembershipTable.tsx` — 个案隶属度交互表格（~360 tok）

### 修改文件
- `src/pages/Settings.tsx` — 校准预览卡片 + useMemo 参数计算
- `src/pages/Settings.css` — 预览卡片 + 统计条样式
- `src/pages/Results.tsx` — 新增 Cases 标签页，activeTab 扩展
- `src/pages/Results.css` — 案例表格全套样式（~120 行）
- `src/i18n/translations.ts` — 21 个新 i18n 键（preview + cases）

### 评分管道（无变化）
```
文本输入 → BertEngine (Transformers.js) → BERT CLS 嵌入
                                               ↓
ConditionDefinition.prototypes → CosineSimilarityEngine → 原始分数 [0,1]
                                               ↓
CalibrationStrategyRegistry → 校准 → 模糊隶属度
                                               ↓
QCA 引擎 → 真值表 → QM 最小化 → 解
```

## 6. 活跃问题 / 注意事项

| 项目 | 严重程度 | 备注 |
|------|----------|------|
| **BERT embedding_model 硬编码** | Medium | `useQCAWorkflow.ts:184` 写死 `'Xenova/bert-base-chinese'`，P1-B7 修复 |
| **RECENT_RUNS_KEY 重复** | Minor | Dashboard.tsx 和 QCAPipelineContext.tsx 中重复定义，应提取到共享常量 |
| **FIXME-28** | 建议 | `TextCase.outcome` 是 `int`，fsQCA 连续型结果应为 `float` |
| **FIXME-32** | 建议 | domains.py 原型预置为硬编码，用户可能希望在线编辑并持久化 |
| **P1-B7/B8 方案就绪** | Info | Plan agent 已设计完整方案，下一 session 可直接实现 |

## 7. 快速验证命令

```bash
npm run build              # TypeScript + Vite 构建
uv run pytest --tb=no -q   # Python 测试 (532 passed)
uv run ruff check src/     # 应为干净状态
npm run dev                # 启动开发服务器 (127.0.0.1:3000)
```

## 8. Subagent 工作流经验

本轮验证了 subagent 并行工作流：
- **Plan agent** 负责设计（P1-5 方案 + P1-B7/B8 方案）
- **Fixer agent** 负责实现（~4 文件创建/修改，build 验证）
- **Reviewer agent** 负责审查（发现 2 个需要修复的 bug）
- **主 session** 仅做汇总、小修复（2 行 bug fix）、commit/push

**经验**：
- Fixer agent 会创建 untracked 文件但不会 git add → 主 session 需自行 stage
- Reviewer agent 发现的 bug 可由主 session 快速修复（避免再派 agent 的耗时）
- 并行 Plan agent + Fixer agent 有效节省时间（Phase 3 方案在 P1-5 实现期间完成）

## 9. 未跟踪文件

```
?? .wolf/memory-archive.md     — 归档的旧 session 日志
?? experiment-engine/           — 嵌套 git 仓库/旧 worktree。不要 touch。
```
