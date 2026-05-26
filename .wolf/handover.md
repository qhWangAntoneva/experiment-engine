# QCA Analysis Tool — Project Status (2026-05-26)

> QCA Text Analysis Tool: BERT 嵌入 → 模糊校准 → QCA 真值表 → 解。

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| HEAD | `7474dee` — fix: harden default language to English with inlined DEFAULT_LANGUAGE constant |
| 远程 | `origin/master` (已推送) |
| Python 测试 | 532 passed, 1 skipped, 6 xfailed |
| TypeScript build | `npm run build` clean |
| Dev server | `http://127.0.0.1:3000`（必须用 127.0.0.1，不用 localhost） |

## 2. 已完成 P1 功能

P1 全部完成（原计划 12 项）：

- **P1-10** — 校准参数即时预览：Plotly 双直方图 + 汇总统计条，JS 端校准公式镜像 Python `strategies.py`
- **P1-5** — 个案级校准结果展示：排序/筛选/展开的案例隶属度交互表格
- **P1-8 + P1-9** — Privacy 设置页面 + Recent Runs（localStorage）
- **P1-B7** — BERT 模型切换支持：端到端模型选择，替换硬编码 `'Xenova/bert-base-chinese'`
- **P1-B8** — 性能监控面板：Web Worker 耗时、内存占用、嵌入缓存命中率实时展示
- **P1-6** — 项目保存与恢复：一键保存/加载 .qca JSON + localStorage + auto-save hook
- **P1-7** — 参数对比 / A/B 分析：CompareView + ParamDiffTable 并排对比两次分析
- **P1-11** — 中文 Word 报告导出：docx 含图表、QCA 解、真值表、校准统计
- **P1-12** — 多结果变量分析：支持配置多个 outcome 变量批量运行
- **P1-13** — 条件集共享与团队模板：TemplateLibrary + ShareImportModal + ShareLinkButton

**P1 完成度：12/12 (100%)**

## 3. 当前 TODO 状态

| 优先级 | 剩余 | 备注 |
|--------|------|------|
| P0 | **0** | 全部完成 |
| P1 | **0** | 全部完成（12/12） |
| P2 | **21** | P2-20, P2-22 已完成，其余未开始 |
| **合计** | **21** | |

**下一步推荐**（P2 功能，按优先级）：
1. **P2-1** — 模糊集 XY 散点图（隶属度散点）
2. **P2-2** — 必要性/充分性散点图
3. **P2-3** — 一致性/覆盖度条形图
4. **P2-4** — 解路径可视化（Venn 图 / Euler 图）
5. **P2-5** — 真值表热力图
6. **P2-14** — PDF 报告导出（LaTeX 模板增强）
7. **P2-15** — 导出结果至 CSV / Excel
8. **P2-19** — 用户自定义校准函数
9. **P2-21** — 智能原型建议（基于聚类）

## 4. 架构摘要

### 评分管道
```
文本输入 → BertEngine (Transformers.js) → BERT CLS 嵌入
                                               ↓
ConditionDefinition.prototypes → CosineSimilarityEngine → 原始分数 [0,1]
                                               ↓
CalibrationStrategyRegistry → 校准 → 模糊隶属度
                                               ↓
QCA 引擎 → 真值表 → QM 最小化 → 解
```

### 新增文件（P1-6/7/11/12/13 + P1-B7/B8）

| 文件 | 关联功能 |
|------|----------|
| `src/components/PerformancePanel.tsx` | P1-B8 — 性能监控面板 |
| `src/components/CompareView.tsx` | P1-7 — A/B 对比主视图 |
| `src/components/ParamDiffTable.tsx` | P1-7 — 参数差异表格 |
| `src/pages/Compare.tsx` | P1-7 — 对比页面 |
| `src/pages/Compare.css` | P1-7 — 对比页面样式 |
| `src/components/TemplateLibrary.tsx` | P1-13 — 模板库 |
| `src/components/TemplateLibrary.css` | P1-13 — 模板库样式 |
| `src/components/ShareImportModal.tsx` | P1-13 — 分享/导入弹窗 |
| `src/components/ShareLinkButton.tsx` | P1-13 — 分享链接按钮 |
| `src/hooks/useProjectAutoSave.ts` | P1-6 — 自动保存 hook |
| `src/services/project-serialization.ts` | P1-6 — 项目序列化服务 |
| `src/services/templateService.ts` | P1-13 — 模板服务 |
| `src/utils/snapshotStorage.ts` | P1-12 — 快照存储工具 |
| `src/experiment_engine/report/docx_reporter.py` | P1-11 — Word 报告导出 |

### 之前新增文件（P1-5/10）
- `src/components/CalibrationPreview.tsx` — JS 校准公式 + Plotly 预览
- `src/components/CaseMembershipTable.tsx` — 个案隶属度交互表格

### 修改文件（近期）
- `src/pages/Settings.tsx` — 校准预览卡片 + BERT 模型选择
- `src/pages/Dashboard.tsx` — Recent Runs 优化 + 性能面板入口
- `src/pages/DataInput.tsx` — 项目保存/加载入口
- `src/pages/Results.tsx` — 新增 Cases 标签页 + 多结果变量
- `src/hooks/useQCAWorkflow.ts` — 移除硬编码 embedding_model，支持动态模型选择
- `src/services/bert-engine.ts` — 模型切换 + 性能埋点
- `src/services/pyodide.ts` — 多结果变量管道支持
- `src/services/pyodide.worker.ts` — Worker 端模型切换支持
- `src/store/QCAPipelineContext.tsx` — Recent Runs key 统一 + 多结果状态
- `src/i18n/translations.ts` — 新增翻译键（模型选择、模板、对比、报告等）
- `src/types/qca.ts` — 新增类型（模板、快照、模型配置）
- `src/types/index.ts` — 类型导出更新
- `src/experiment_engine/pyodide_handlers.py` — 多结果变量处理
- `src/experiment_engine/report/__init__.py` — docx reporter 导出
- `src/App.tsx` — 新增路由（Compare）
- `src/components/Sidebar.tsx` — 新增导航项（Compare、Templates）

## 5. 活跃问题 / 注意事项

| 项目 | 严重程度 | 备注 |
|------|----------|------|
| **RECENT_RUNS_KEY 重复** | Minor | Dashboard.tsx 和 QCAPipelineContext.tsx 中重复定义，应提取到共享常量 |
| **FIXME-28** | 建议 | `TextCase.outcome` 是 `int`，fsQCA 连续型结果应为 `float` |
| **FIXME-32** | 建议 | domains.py 原型预置为硬编码，用户可能希望在线编辑并持久化 |

## 6. 快速验证命令

```bash
npm run build              # TypeScript + Vite 构建
uv run pytest --tb=no -q   # Python 测试 (532 passed)
uv run ruff check src/     # 应为干净状态
npm run dev                # 启动开发服务器 (127.0.0.1:3000)
```

## 7. 未提交/未跟踪文件

**修改文件 (Modified):**
```
 .wolf/anatomy.md
 .wolf/buglog.json
 .wolf/cerebrum.md
 .wolf/memory.md
 .wolf/token-ledger.json
 TODO.md
 qca_output/qca_report.tex
 qca_output/qca_results.json
 qca_output/robustness_report.json
 src/App.tsx
 src/components/Sidebar.tsx
 src/experiment_engine/pyodide_handlers.py
 src/experiment_engine/report/__init__.py
 src/hooks/useQCAWorkflow.ts
 src/i18n/translations.ts
 src/pages/Dashboard.tsx
 src/pages/DataInput.tsx
 src/pages/Results.tsx
 src/pages/Settings.tsx
 src/services/bert-engine.ts
 src/services/pyodide.ts
 src/services/pyodide.worker.ts
 src/store/QCAPipelineContext.tsx
 src/types/index.ts
 src/types/qca.ts
```

**新增文件 (Untracked):**
```
 src/components/CompareView.tsx          — P1-7 — A/B 对比主视图
 src/components/ParamDiffTable.tsx        — P1-7 — 参数差异表格
 src/components/PerformancePanel.tsx      — P1-B8 — 性能监控面板
 src/components/ShareImportModal.tsx      — P1-13 — 分享/导入弹窗
 src/components/ShareLinkButton.tsx       — P1-13 — 分享链接按钮
 src/components/TemplateLibrary.css       — P1-13 — 模板库样式
 src/components/TemplateLibrary.tsx       — P1-13 — 模板库
 src/experiment_engine/report/docx_reporter.py — P1-11 — Word 报告导出
 src/hooks/useProjectAutoSave.ts          — P1-6 — 自动保存 hook
 src/pages/Compare.css                    — P1-7 — 对比页面样式
 src/pages/Compare.tsx                    — P1-7 — 对比页面
 src/services/project-serialization.ts    — P1-6 — 项目序列化服务
 src/services/templateService.ts          — P1-13 — 模板服务
 src/utils/snapshotStorage.ts             — P1-12 — 快照存储工具
```
