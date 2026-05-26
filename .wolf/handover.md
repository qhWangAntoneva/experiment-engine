# QCA Analysis Tool — Project Status (2026-05-26)

> QCA Text Analysis Tool: BERT 嵌入 → 模糊校准 → QCA 真值表 → 解。

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| HEAD | `60fa11e` — chore: update handover + wolf files for session handoff |
| 远程 | `origin/master` (已推送) |
| Python 测试 | 532 passed, 1 skipped, 6 xfailed |
| TypeScript build | `npm run build` clean |
| Dev server | `http://127.0.0.1:3000`（必须用 127.0.0.1，不用 localhost） |

## 2. 已完成 P1 功能

P1 已完成 5 项：

- **P1-10** — 校准参数即时预览：Plotly 双直方图 + 汇总统计条，JS 端校准公式镜像 Python `strategies.py`
- **P1-5** — 个案级校准结果展示：排序/筛选/展开的案例隶属度交互表格
- **P1-8 + P1-9** — Privacy 设置页面 + Recent Runs（localStorage）
- P1 剩余 7 项：P1-B7/B8 (模型切换+性能监控)、P1-6/7/11/12/13

## 3. 当前 TODO 状态

| 优先级 | 剩余 | 备注 |
|--------|------|------|
| P0 | **0** | 全部完成 |
| P1 | **7** | P1-B7/B8 (模型切换+性能) + P1-6/7/11/12/13 |
| P2 | **21** | P2-20, P2-22 已完成，其余未开始 |
| **合计** | **28** | |

**下一步推荐**（按优先级）：
1. **P1-B7 + P1-B8** — 模型切换支持 + 性能监控面板（已有完整设计方案，约 10 个文件）
2. **P1-6** — 项目保存与恢复（一键保存/加载 .qca JSON + localStorage）
3. **P1-13** — 条件集共享与团队模板
4. **P1-11** — 中文 Word 报告导出（.docx 含图表）
5. **P1-7** — 参数对比 / A/B 分析
6. **P1-12** — 多结果变量分析

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

### 新增文件（近期）
- `src/components/CalibrationPreview.tsx` — JS 校准公式 + Plotly 预览
- `src/components/CaseMembershipTable.tsx` — 个案隶属度交互表格

### 修改文件（近期）
- `src/pages/Settings.tsx` — 校准预览卡片
- `src/pages/Settings.css` — 预览卡片 + 统计条样式
- `src/pages/Results.tsx` — 新增 Cases 标签页
- `src/pages/Results.css` — 案例表格样式
- `src/i18n/translations.ts` — 21 个新 i18n 键

## 5. 活跃问题 / 注意事项

| 项目 | 严重程度 | 备注 |
|------|----------|------|
| **BERT embedding_model 硬编码** | Medium | `useQCAWorkflow.ts:184` 写死 `'Xenova/bert-base-chinese'`，P1-B7 修复 |
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

当前工作树状态：
```
 M .wolf/anatomy.md
 M .wolf/buglog.json
 M .wolf/cerebrum.md
 M .wolf/memory.md
 M .wolf/token-ledger.json
 M src/i18n/translations.ts
?? .wolf/memory-archive.md     — 归档的旧 session 日志
?? experiment-engine/           — 嵌套 git 仓库/旧 worktree，不要 touch
```
