# FIXME — QCA Analysis Tool

> 自动生成于 2026-05-24 | 来源：评审者代码审查 + 技术顾问架构审查
> 严重程度：🔴 = 严重/必须修 | 🟡 = 警告/建议修 | 🟢 = 建议/锦上添花

---

## 🔴 严重 — 算法错误与数据损坏

### FIXME-1: counterfactual.py:98-128 — `produce_parsimonious_solution` 算法错误

**文件**: `src/experiment_engine/qca_engine/advanced/counterfactual.py`
**严重程度**: 🔴 严重
**问题**: 精简解 (parsimonious solution) 应包含**全部逻辑余项**作为 don't-care 行参与最小化，当前仅添加 easy counterfactuals，行为与 intermediate solution 完全相同。标准 QCA (Ragin 2008) 中精简解不区分 easy/hard。
**修复**: `produce_parsimonious_solution` 应添加所有 frequency<1.0 的行，不经过 `_classify_counterfactual` 过滤。同时需扩展 QM 实现支持 don't-care minterm。
**影响**: 精简解输出在逻辑余项较多时与文献标准结果不一致，论文投稿可能被审稿人质疑。
**来源**: 评审者#1

### FIXME-2: calibrator.py:165-167 — 混合 scoring_source 列索引偏移

**文件**: `src/experiment_engine/text_calibration/calibrator.py`
**严重程度**: 🔴 严重
**问题**: `_compute_raw_scores()` 的 KEYWORD 分支用 `col_idx`（全局位置）直接索引 `match_corpus()` 返回矩阵（仅含 KEYWORD/HYBRID 条件的列）。当 PROTOTYPE 条件与 KEYWORD 条件交错排列时索引偏移。
**复现**: 条件 `[A(KEYWORD), B(PROTOTYPE), C(KEYWORD)]`，outcome 是 KEYWORD。处理 C 时 `col_idx=2` 但 kw 矩阵第 2 列是 B。
**修复**: 预先构建 `col_idx → kw_col_idx` 映射。
**来源**: 评审者#2

### FIXME-3: calibrator.py:389-421 — `calibrate_ragin` 实现的是分段线性而非 log-odds

**文件**: `src/experiment_engine/text_calibration/calibrator.py`
**严重程度**: 🔴 严重
**问题**: docstring 声称实现 "Ragin's fuzzy direct method: log-odds of raw scores relative to anchors"，但实际代码是分段线性插值（与 `calibrate_direct` 仅 floor/ceiling 改为 0.05/0.95）。正确的 Ragin 方法应使用 logistic 变换。
**修复**: 用 logistic 公式重写：`log_odds = ln(m/(1-m))`, `deviation = (raw - crossover) * (log_odds_95 / (full_in - crossover))`, `membership = exp(deviation)/(1 + exp(deviation))`。
**来源**: 评审者#3

### FIXME-4: calibrator.py:140,166 — `match_corpus()` 每个条件重复调用

**文件**: `src/experiment_engine/text_calibration/calibrator.py`
**严重程度**: 🔴 严重（性能）
**问题**: `_compute_raw_scores` 中每个 KEYWORD/HYBRID 条件都调 `self._dict.match_corpus(texts)`，导致 O(n_conditions × n_texts × n_keywords) 冗余计算。WASM 下 150 条文本 × 6 条件 = 900 次匹配。
**修复**: `process()` 开头调用一次 `match_corpus()`，缓存结果矩阵。
**来源**: 评审者#4

### FIXME-5: pipeline.py:277-286 — Stage 失败后静默传递损坏数据

**文件**: `src/experiment_engine/pipeline.py`
**严重程度**: 🔴 严重
**问题**: Stage 失败后 `Pipeline.process()` 将"上次正常数据"传给下游。若 `TextCalibrationStage` 失败，`QCAnalyzerStage` 会收到原始文本数据。`PipelineResult.status` 仅设为 `PARTIAL`，调用方无法区分"部分失败"与"全流程失效"。
**修复**: 添加 `fail_fast: bool` 配置项（默认 True），失败时立即中止并返回 `PipelineStatus.FAILED`。在 `StageResult` 中添加 `data_quality` 字段。
**来源**: 技术顾问#6

---

## 🟡 警告 — 设计缺陷与遗漏

### FIXME-6: robustness.py:92 — `solution_coverage` 属性不存在 → coverage_stability 始终为 0

**文件**: `src/experiment_engine/qca_engine/advanced/robustness.py`
**严重程度**: 🟡 警告
**问题**: `hasattr(tt, "solution_coverage")` 始终为 False（`TruthTable` 模型无此字段），导致 coverage_stability 数组全为 0.0，该列无意义。
**修复**: 应 run minimization + sufficiency 计算真实 coverage，而非从 truth table 对象取不存在的属性。
**来源**: 评审者#9

### FIXME-7: robustness.py:140-179 — `test_calibration_sensitivity` 实际是 membership perturbation

**文件**: `src/experiment_engine/qca_engine/advanced/robustness.py`
**严重程度**: 🟡 警告
**问题**: 方法对所有 membership 列（包括 outcome）施加统一的 additive perturbation，与校准参数（threshold_full_in/out/crossover）的敏感性完全不同。扰动 outcome 列混入了 outcome sensitivity 效应。
**修复**: 应扰动 calibration_params 的阈值参数，重新运行 calibration，再比较解的稳定性。
**来源**: 评审者#8

### FIXME-8: robustness.py — 缺失 bootstrap 鲁棒性检验

**文件**: `src/experiment_engine/qca_engine/advanced/robustness.py`
**严重程度**: 🟡 警告
**问题**: docstring 提到 "bootstrap resampling"，但 `run_all()` 仅含 3 个敏感性检验，无任何 resampling-based 方法。
**修复**: 添加 `test_bootstrap()` 方法，带放回案例重抽样，比较不同 bootstrap sample 的解稳定性。
**来源**: 评审者#10

### FIXME-9: counterfactual.py:57 — `theoretical_expectation` 字段始终为 None

**文件**: `src/experiment_engine/qca_engine/advanced/counterfactual.py`
**严重程度**: 🟡 警告
**问题**: `theo_exp` 初始化为 `None` 后从未赋值，导致 `CounterfactualClassification.theoretical_expectation` 对观察到的行永远是 None。
**修复**: 从 `directional_expectations` 中查找理论期望并赋值。
**来源**: 评审者#7

### FIXME-10: qca_reporter.py — LaTeX 特殊字符未转义

**文件**: `src/experiment_engine/report/qca_reporter.py`
**严重程度**: 🟡 警告
**问题**: `r.config_label` 含 `*`、`~` 字符直接插入 LaTeX。`~` 在 LaTeX 中是 non-breaking space。条件名若含 `_`、`%`、`$` 导致编译失败。
**修复**: 添加 LaTeX 转义函数：`*` → `\land`，`~` → `\neg`，`+` → `\lor`，特殊字符用 `\text{}` 包裹。
**来源**: 评审者#12

### FIXME-11: qca_reporter.py:217 — `_robustness_section` 空列表 IndexError

**文件**: `src/experiment_engine/report/qca_reporter.py`
**严重程度**: 🟡 警告
**问题**: `t.solution_stability[0]` 和 `t.solution_stability[-1]` 在列表为空时直接崩溃。
**修复**: 添加 `if t.solution_stability:` 守卫。
**来源**: 评审者#13

### FIXME-12: robustness.py:111-112 — 默认频率阈值对小 N 不合理

**文件**: `src/experiment_engine/qca_engine/advanced/robustness.py`
**严重程度**: 🟡 警告
**问题**: `test_frequency_sensitivity` 默认阈值 `[1.0, 2.0, 3.0, 5.0]`。fuzzy-set QCA 中频率是 membership 的和，对于 N<10 的分析可能排除所有行。
**修复**: 根据 `baseline.fuzzy_data.n_cases` 自适应调整阈值范围。
**来源**: 评审者#14

### FIXME-13: sufficiency.py:135-137 — 条件名不匹配时静默跳过

**文件**: `src/experiment_engine/qca_engine/sufficiency.py`
**严重程度**: 🟡 警告
**问题**: `_compute_term_membership` 中 condition name 不匹配时 `pass`（静默视为 1.0），隐藏 term label 与 condition_matrix 列名不匹配的 bug。
**修复**: 至少 print warning，或 raise KeyError 附上不匹配的条件名。
**来源**: 评审者#11

### FIXME-14: keyword_dict.py:83-96 — bigram 跨标点误匹配

**文件**: `src/experiment_engine/text_calibration/keyword_dict.py`
**严重程度**: 🟡 警告
**问题**: 文本 "他对产品不满，意在投诉" clean_text 后变为 "他对产品不满意在投诉"，搜索 "不满意" bigram `["不满", "满意"]` 可能错误匹配（原本不相邻的词因标点移除而相邻）。
**修复**: 在 tokenize 时保留标点位置信息（插入句子边界标记），或使用带位置验证的匹配方式。考虑到无 jieba 约束，当前方案可接受但需注意。
**来源**: 评审者#15

### FIXME-15: pyodide.worker.ts — 10 个 handler 大量重复代码

**文件**: `src/services/pyodide.worker.ts`
**严重程度**: 🔴 严重
**问题**: 每个 handler 重复 `ensureReady() → JSON.stringify → FS.writeFile → runPythonAsync(40行字符串) → JSON.parse → respond()` 模式，内嵌 Python 代码无法被 pytest/linter 覆盖。
**修复**: 提取为 `pyodide_handlers.py` 独立函数，worker handler 简化为通用模板。
**来源**: 技术顾问#2

### FIXME-16: models.py — 上帝对象

**文件**: `src/experiment_engine/models.py`
**严重程度**: 🟡 警告
**问题**: 9500 token 单文件包含框架层模型（StageStatus/PipelineResult 等）和 QCA 领域模型（ConditionSet/FuzzySetData/TruthTable 等），违反单一职责原则。
**修复**: 拆分为 models/framework.py、models/qca.py、models/training.py。
**来源**: 技术顾问#4

---

## 🟢 建议 — 代码质量改进

### FIXME-17: counterfactual.py:140 — 死代码

**文件**: `src/experiment_engine/qca_engine/advanced/counterfactual.py`
**严重程度**: 🟢 建议
**问题**: `set(directional_expectations.keys())` 创建 set 后丢弃。
**修复**: 删除该行。
**来源**: 评审者#5

### FIXME-18: minimization.py:43-44 — 死代码

**文件**: `src/experiment_engine/qca_engine/minimization.py`
**严重程度**: 🟢 建议
**问题**: `len(minterms[0])` 和 `list(range(len(minterms)))` 表达式求值后结果被丢弃。
**修复**: 删除这两行。
**来源**: 评审者#6

### FIXME-19: prototype_similarity.py — weight 字段未使用

**文件**: `src/experiment_engine/text_calibration/prototype_similarity.py`
**严重程度**: 🟢 建议
**问题**: `ConceptPrototype.weight` 字段已定义但 `compute_similarities()` 未使用，所有原型平等对待。
**修复**: 在 `_max_similarity` 中使用加权 Jaccard 或加权平均。
**来源**: 评审者#16

### FIXME-20: calibrator.py:74-121 — process/process_with_outcome 大量重复代码

**文件**: `src/experiment_engine/text_calibration/calibrator.py`
**严重程度**: 🟢 建议
**问题**: 两个方法 ~60 行高度重复，仅在 outcome 列赋值方式不同。
**修复**: 抽取公共逻辑为 `_process_core(texts, outcome_provider_fn)`。
**来源**: 评审者#17

### FIXME-21: minimization.py:82 — hash-based identity 不可靠

**文件**: `src/experiment_engine/qca_engine/minimization.py`
**严重程度**: 🟢 建议
**问题**: 使用 `hash((imp1, tuple(cov1)))` 追踪 implicant 身份，存在理论碰撞风险和 PYTHONHASHSEED 跨进程不稳定。
**修复**: 用 `id()` 或全局递增 ID 表示 implicant 身份。
**来源**: 评审者#18

### FIXME-22: calibrator.py:369 — k=10 硬编码

**文件**: `src/experiment_engine/text_calibration/calibrator.py`
**严重程度**: 🟢 建议
**问题**: `calibrate_indirect` logistic 变换 steepness factor k=10 硬编码，不可配置。
**修复**: 将 k 作为 `CalibrationParams` 可选字段或注释选择依据。
**来源**: 评审者#19

---

## 统计

| 严重程度 | 数量 |
|----------|------|
| 🔴 严重 | 6 |
| 🟡 警告 | 10 |
| 🟢 建议 | 6 |
| **合计** | **22** |
