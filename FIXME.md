# FIXME — QCA Analysis Tool

> 自动生成于 2026-05-24 | 最后更新：2026-05-24 (四阶段修复完成)
> 严重程度：🔴 = 严重/必须修 | 🟡 = 警告/建议修 | 🟢 = 建议/锦上添花

---

## 🔴 严重 — 算法错误与数据损坏 [全部已修复]

### ~~FIXME-1: counterfactual.py:98-128 — `produce_parsimonious_solution` 算法错误~~ [已修复 2026-05-24 Phase 1]

**文件**: `src/experiment_engine/qca_engine/advanced/counterfactual.py`
**修复**: `produce_parsimonious_solution` 现添加所有 frequency<1.0 行为 don't-care minterm，不经过 `_classify_counterfactual` 过滤。QM 扩展支持 `dont_care_minterms` 参数（见 HACK-5）。对齐 Ragin 2008 标准。
**提交**: c4c6aa2

### ~~FIXME-2: calibrator.py:165-167 — 混合 scoring_source 列索引偏移~~ [已修复 2026-05-24 Phase 1]

**文件**: `src/experiment_engine/text_calibration/calibrator.py`
**修复**: 新增 `_precompute_kw_context()` 构建 `col_idx → kw_col_idx` 映射。`_compute_raw_scores()` 通过可选参数接收映射。
**提交**: c4c6aa2

### ~~FIXME-3: calibrator.py:389-421 — `calibrate_ragin` 实现的是分段线性而非 log-odds~~ [已修复 2026-05-24 Phase 1]

**文件**: `src/experiment_engine/text_calibration/calibrator.py`
**修复**: 用 logistic 公式重写：`exp(deviation)/(1+exp(deviation))`，`deviation = (raw - crossover) * (log_odds_95 / (full_in - crossover))`。添加 np.clip(deviation, -700, 700) 防 overflow。
**提交**: c4c6aa2

### ~~FIXME-4: calibrator.py:140,166 — `match_corpus()` 每个条件重复调用~~ [已修复 2026-05-24 Phase 1]

**文件**: `src/experiment_engine/text_calibration/calibrator.py`
**修复**: `_precompute_kw_context()` 缓存一次 match_corpus 结果。process/process_with_outcome/calibrate_one 全部复用。
**提交**: c4c6aa2

### ~~FIXME-5: pipeline.py:277-286 — Stage 失败后静默传递损坏数据~~ [已修复 2026-05-24 Phase 2]

**文件**: `src/experiment_engine/pipeline.py`, `core/parallel.py`, `models.py`
**修复**: 添加 `fail_fast: bool = True`（默认）。失败时立即中止并返回 `PipelineStatus.FAILED`。`StageResult` 新增 `data_quality` 字段（valid/stale/None）。`PipelineResult` 新增 `failed_stages` 属性和 `fail_fast` 字段。ParallelPipeline 同步更新。
**提交**: 9842e11

---

## 🟡 警告 — 设计缺陷与遗漏

### ~~FIXME-6: robustness.py:92 — `solution_coverage` 属性不存在 → coverage_stability 始终为 0~~ [已修复 2026-05-24 Phase 3]

**文件**: `src/experiment_engine/qca_engine/advanced/robustness.py`
**修复**: 添加 `_compute_solution_coverage()` 通过 fuzzy AND term membership + union + ConsistencyCalculator 计算真实解覆盖度。
**提交**: 9b58081

### ~~FIXME-7: robustness.py:140-179 — `test_calibration_sensitivity` 实际是 membership perturbation~~ [已修复 2026-05-24 Phase 3]

**文件**: `src/experiment_engine/qca_engine/advanced/robustness.py`
**修复**: 重命名为 `test_membership_perturbation`。仅扰动条件列（perturbed[:, :-1]）排除 outcome。保留 `test_calibration_sensitivity` 向后兼容别名。
**提交**: 9b58081

### ~~FIXME-8: robustness.py — 缺失 bootstrap 鲁棒性检验~~ [已修复 2026-05-24 Phase 3]

**文件**: `src/experiment_engine/qca_engine/advanced/robustness.py`
**修复**: 添加 `test_bootstrap(n_iterations=100, sample_fraction=1.0)`：case replacement resampling，truth table + QM per sample，Jaccard similarity + term appearance proportion。
**提交**: 9b58081

### ~~FIXME-9: counterfactual.py:57 — `theoretical_expectation` 字段始终为 None~~ [已修复 2026-05-24 Phase 2]

**文件**: `src/experiment_engine/qca_engine/advanced/counterfactual.py`
**修复**: 在 `analyze()` 循环中从 `directional_expectations` 构建 `theo_exp` 字符串（"+name" 表示预期 present，"-name" 表示预期 absent，多条件用 ", " 连接）。
**提交**: 9842e11

### ~~FIXME-10: qca_reporter.py — LaTeX 特殊字符未转义~~ [已修复 2026-05-24 Phase 3]

**文件**: `src/experiment_engine/report/qca_reporter.py`
**修复**: 添加 `_escape_latex()` 转义 %$#&{}_ → 反斜杠形式、~ → \textasciitilde{}。添加 `_escape_latex_formula()` 转换 ~*+ → \neg \land \lor。所有用户文本插入点均已应用转义。
**提交**: 9b58081

### ~~FIXME-11: qca_reporter.py:217 — `_robustness_section` 空列表 IndexError~~ [已修复 2026-05-24 Phase 3]

**文件**: `src/experiment_engine/report/qca_reporter.py`
**修复**: 添加 `if t.solution_stability:` 守卫，空列表时 stability_range = "N/A"。
**提交**: 9b58081

### ~~FIXME-12: robustness.py:111-112 — 默认频率阈值对小 N 不合理~~ [已修复 2026-05-24 Phase 3]

**文件**: `src/experiment_engine/qca_engine/advanced/robustness.py`
**修复**: N<20 使用比例阈值 [0.05\*N, 0.10\*N, 0.15\*N, 0.25\*N]；N>=20 使用绝对阈值 [1.0, 2.0, 3.0, 5.0]。
**提交**: 9b58081

### ~~FIXME-13: sufficiency.py:135-137 — 条件名不匹配时静默跳过~~ [已修复 2026-05-24 Phase 2]

**文件**: `src/experiment_engine/qca_engine/sufficiency.py`
**修复**: 否定/非否定分支均添加 `warnings.warn()` 输出 warning（含 stacklevel=2 指向调用方），显示不匹配的条件名和可用列名。
**提交**: 9842e11

### FIXME-14: keyword_dict.py:83-96 — bigram 跨标点误匹配

**文件**: `src/experiment_engine/text_calibration/keyword_dict.py`
**严重程度**: 🟡 警告
**问题**: 文本 "他对产品不满，意在投诉" clean_text 后变为 "他对产品不满意在投诉"，搜索 "不满意" bigram `["不满", "满意"]` 可能错误匹配（原本不相邻的词因标点移除而相邻）。
**修复**: 在 tokenize 时保留标点位置信息（插入句子边界标记），或使用带位置验证的匹配方式。考虑到无 jieba 约束，当前方案可接受但需注意。
**来源**: 评审者#15

### ~~FIXME-15: pyodide.worker.ts — 10 个 handler 大量重复代码~~ [已修复 2026-05-24 Phase 4]

**文件**: `src/services/pyodide.worker.ts`, `src/experiment_engine/pyodide_handlers.py` (新增)
**修复**: 提取 7 个 handler 函数到 `pyodide_handlers.py` (333 行)。Worker 添加通用 `runHandler()` 模板。Worker 从 659 行缩减到 464 行 (-30%)。同步修复 2 个隐蔽 bug（_fuzzy_data 累积变量错误 + QCAReporter→QCALaTeXReporter 类名错误）。
**提交**: d08786c

### FIXME-16: models.py — 上帝对象 ✅ [已修复 2026-05-24]

**文件**: `src/experiment_engine/models/`
**严重程度**: 🟡 警告
**问题**: 9500 token 单文件包含框架层模型（StageStatus/PipelineResult 等）和 QCA 领域模型（ConditionSet/FuzzySetData/TruthTable 等），违反单一职责原则。
**修复**: 拆分为 `models/framework.py` (15.5 KB, pipeline-generic) + `models/qca.py` (18.5 KB, QCA domain) + `models/training.py` (1.9 KB, training samples) + `models/__init__.py` (重导出 34 个公共符号，保持向后兼容)。全部 465 测试通过，ruff 干净，npm build 通过。
**来源**: 技术顾问#4

---

## 🟢 建议 — 代码质量改进

### ~~FIXME-17: counterfactual.py:140 — 死代码~~ [已修复 2026-05-24 Phase 1]

**文件**: `src/experiment_engine/qca_engine/advanced/counterfactual.py`
**修复**: 删除 `set(directional_expectations.keys())`。
**提交**: c4c6aa2

### ~~FIXME-18: minimization.py:43-44 — 死代码~~ [已修复 2026-05-24 Phase 1]

**文件**: `src/experiment_engine/qca_engine/minimization.py`
**修复**: 删除 `len(minterms[0])` 和 `list(range(len(minterms)))`。
**提交**: c4c6aa2

### FIXME-19: prototype_similarity.py — weight 字段未使用

**文件**: `src/experiment_engine/text_calibration/prototype_similarity.py`
**严重程度**: 🟢 建议
**问题**: `ConceptPrototype.weight` 字段已定义但 `compute_similarities()` 未使用，所有原型平等对待。
**修复**: 在 `_max_similarity` 中使用加权 Jaccard 或加权平均。（见 TODO P2-19）
**来源**: 评审者#16

### ~~FIXME-20: calibrator.py:74-121 — process/process_with_outcome 大量重复代码~~ [已修复 2026-05-24 Phase 1]

**文件**: `src/experiment_engine/text_calibration/calibrator.py`
**修复**: 抽取公共逻辑为 `_process_core(texts, kw_matrix, col_to_kw, outcome_provider_fn)`。
**提交**: c4c6aa2

### ~~FIXME-21: minimization.py:82 — hash-based identity 不可靠~~ [已修复 2026-05-24 Phase 3]

**文件**: `src/experiment_engine/qca_engine/minimization.py`
**修复**: 用 `itertools.count()` 顺序 ID 替换 `hash()`。数据结构从 (pattern, coverage) 改为 (id, pattern, coverage)。
**提交**: 9b58081

### FIXME-22: calibrator.py:369 — k=10 硬编码

**文件**: `src/experiment_engine/text_calibration/calibrator.py`
**严重程度**: 🟢 建议
**问题**: `calibrate_indirect` logistic 变换 steepness factor k=10 硬编码，不可配置。
**修复**: 将 k 作为 `CalibrationParams` 可选字段。（见 TODO P2-20）
**来源**: 评审者#19

---

## 统计

| 严重程度 | 原始 | 已修复 | 剩余 |
|----------|------|--------|------|
| 🔴 严重 | 6 | 6 | 0 |
| 🟡 警告 | 10 | 9 | 1 (FIXME-14) |
| 🟢 建议 | 6 | 4 | 2 (FIXME-19, FIXME-22) |
| **合计** | **22** | **19** | **3** |

下一次 session 建议优先处理：
1. FIXME-14 → bigram 跨标点误匹配（唯一剩余的算法相关 FIXME）
2. FIXME-19 → prototype weight 启用
3. FIXME-22 → k=10 可配置化
