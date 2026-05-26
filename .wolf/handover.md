# QCA Analysis Tool — Project Status (2026-05-27)

> BERT embeddings → fuzzy calibration → QCA truth table → solutions.

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| HEAD | `594505d` — 30-case pipeline bugs fixed + viz bridge + P2 items |
| 分支 | `master` (已推送) |
| 测试 | 532 passed, 1 skipped, 6 xfailed |
| TS | `npm run build` clean |
| 优先级 | P0=0 P1=0 P2=16 |

## 2. 已解决的问题

### 2.1 CLI --output 不一致 (2026-05-27)
robustness/counterfactuals 现在将 `--output` 作为目录处理，自动拼接文件名。`api.py` 已提取为公共 API 层 (P2-17)。

### 2.2 全部隶属度=0.5 校准Bug (FIXER agent, 2026-05-27)
**根因**: 后端Python无BERT模型（仅浏览器Transformers.js可用），`TextCalibrationStage.process()` 调用时 `text_embeddings=None` → `_precompute_scores` 返回全零 → `DirectCalibration` 对全零归一化产出全部0.5。
**修复**: `calibrator.py` 添加 `_fallback_text_scores()` 方法，用字符三元组Jaccard相似度作为文本级fallback。
**验证**: 所有5域 membership 标准差均 > 0（范围 0.22-0.47），全0.5 Bug确认修复。

## 3. 剩余问题（3个执行Agent正在修复中）

### 3.1 BUG-1 (关键): `run_calibrate()` 忽略 CSV expected_outcome 列
**文件**: `api.py:54`
**现象**: outcome由trigram相似度计算而非真实标签，导致所有域outcome无区分度 → 解为空
**修复方案** (执行 Agent 1): 用pandas读CSV → 按domain过滤 → 用 `process_with_outcome()` 注入真实 outcome 标签
**文件**: `api.py`, `calibrator.py`

### 3.2 BUG-2 (关键): 无 domain 过滤
**文件**: `api.py:54`
**现象**: 全部30条案例输入每个域（应仅6条/域）
**修复方案** (执行 Agent 1): pandas filter `df[df['domain'] == domain_name]`

### 3.3 无可视化输出
**文件**: `viz/` 模块存在但从未被调用。`QCAPlotBuilder` → `MatplotlibRenderer/PlotlyRenderer` 有阻抗不匹配。
**修复方案** (执行 Agent 2): 创建 `viz/viz_bridge.py` 桥接 + 集成到 `run_pipeline.py`

### 3.4 LaTeX报告空段落 + DOCX未集成 + validate脚本格式错误
**文件**: `report/qca_reporter.py`, `report/docx_reporter.py`, `validate_qca_output.py`
**修复方案** (执行 Agent 3): vacuous solution处理 + DOCX导出 + validate增强 + 陈旧文件清理

## 4. 修复方案文档
- `.wolf/plans/technical_advisory_plan.md` — 技术顾问诊断方案
- `.wolf/plans/package_optimization_plan.md` — 包体优化方案

## 5. 待提交文件
`qca_output/*/`（pipeline输出）、`validate_qca_output.py`（helper脚本）、`.wolf/memory.md`（自动生成）。

## 3. 快速验证

```bash
PYTHONIOENCODING=utf-8 uv run python validate_qca_output.py   # 验证所有域
PYTHONIOENCODING=utf-8 uv run pytest --tb=no -q               # 532 passed
npm run dev                                                    # 前端 127.0.0.1:3000
```
