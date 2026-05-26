# FIXME — QCA Analysis Tool

> 自动生成于 2026-05-24 | 最后更新：2026-05-26 (代码库状态重同步)
> 严重程度：🔴 = 严重/必须修 | 🟡 = 警告/建议修 | 🟢 = 建议/锦上添花
>
> **2026-05-26 重同步说明**：与代码库实际状态完整对账。移除了 6 个 MOOT 条目（引用的文件已删除：keyword_dict.py、prototype_similarity.py，全部关键词相关代码已移除）。8 个 FIXME 已在实际代码中解决并移至已修复列表。剩余 3 个开放条目均为 🟢 建议级别。

---

## 🔴 严重 — 算法错误与数据损坏

### ~~FIXME-1: counterfactual.py — produce_parsimonious_solution 算法错误~~ [已修复 2026-05-24 Phase 1, 提交 c4c6aa2]
### ~~FIXME-2: calibrator.py — 混合 scoring_source 列索引偏移~~ [已修复 2026-05-24 Phase 1, 提交 c4c6aa2]
### ~~FIXME-3: calibrator.py — calibrate_ragin 实现的是分段线性而非 log-odds~~ [已修复 2026-05-24 Phase 1, 提交 c4c6aa2]
### ~~FIXME-4: calibrator.py — match_corpus() 每个条件重复调用~~ [已修复 2026-05-24 Phase 1, 提交 c4c6aa2]
### ~~FIXME-5: pipeline.py — Stage 失败后静默传递损坏数据~~ [已修复 2026-05-24 Phase 2, 提交 9842e11]

### ~~FIXME-23: 全项目 — "prototype = 独立校准模式" 架构基于错误假设~~ [已修复 2026-05-26]

**文件**: `calibrator.py`, `pyodide_handlers.py`, `pyodide.worker.ts`, `DataInput.tsx`, `QCAPipelineContext.tsx`, `qca.ts`
**严重程度**: 🔴 严重
**问题**: 整个 prototype 相关代码将 prototype text 视为独立的校准模式（`ScoringSource.PROTOTYPE`、前端模式选择器、`handle_calibrate_prototype` 专用 handler、`calibrating-prototype` pipeline stage）。用户澄清：raw text 和 prototype text 是同一类型输入，通过相同管道生成 CLI，仅在最后分别输出各自对应的 score 和 QCA result。
**修复**: `handle_calibrate` 已统一，ScoringSource 仅保留 PROTOTYPE（作为唯一 scoring 来源），`handle_calibrate_prototype` 保留为向后兼容 wrapper。前端 DataInput 已改为双输入面板（raw + prototype 并排），QCAPipelineContext 的 prototype 专用 stage 已移除。
**来源**: 需求变更审查, 评审者#2026-05-24

### ~~FIXME-24: 全项目 — csQCA（清晰集 QCA）全链路缺失~~ [已修复 2026-05-26]

**文件**: `models/qca.py` (`CalibrationType`), `strategies.py`, `calibrator.py`, `truth_table.py`, `cli.py`
**严重程度**: 🔴 严重
**问题**: 软件完全不支持 csQCA（清晰集 QCA）。所有校准方法均为模糊集，真值表构建使用模糊逻辑 AND，CLI 无 crisp-set 选项。
**修复**: (1) `QCAVariant` 枚举已存在（`FS_QCA`/`CS_QCA`）；(2) `CRISP_SET` 校准类型已实现；(3) `CrispCalibrationParams` 已定义；(4) `TruthTableBuilder` 支持 fuzzy 和 crisp 双模式（根据 variant 选择配置隶属度和一致性计算）；(5) CLI `--variant=csqca` 全局参数可用；(6) 前端 Settings 页面有 fsQCA/csQCA 选择器。
**来源**: 需求变更审查, 评审者#2026-05-24

---

## 🟡 警告 — 设计缺陷与遗漏

### ~~FIXME-6: robustness.py — solution_coverage 属性不存在~~ [已修复 2026-05-24 Phase 3, 提交 9b58081]

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

### ~~FIXME-25: models/qca.py:192 — `FuzzySetData` 命名太窄~~ [已修复 2026-05-26]

**文件**: `src/experiment_engine/models/qca.py`
**严重程度**: 🟡 警告
**问题**: 类名为 `FuzzySetData` 但已接受 0/1 crisp-set 值（validator 仅检查 `[0,1]` 范围），csQCA 启用后此名称产生语义混淆。该类实际承载的是"校准后的 membership data"（模糊或清晰均可）。
**修复**: 已重命名为 `MembershipData`，保留 `FuzzySetData` 作为 deprecated alias 向后兼容。
**来源**: 需求变更审查, 评审者#2026-05-24

### ~~FIXME-26: models/qca.py:32-38 — `CalibrationType` 混合了校准算法与 QCA variant 的概念~~ [已修复 2026-05-26]

**文件**: `src/experiment_engine/models/qca.py`
**严重程度**: 🟡 警告
**问题**: `CalibrationType` 枚举值 DIRECT/INDIRECT/FUZZY_DIRECT 描述的是**校准算法**，但没有层次区分 fsQCA vs csQCA。csQCA 也可以用 direct 方法（单一阈值二分），算法和 set 类型是正交的两个维度。
**修复**: 已拆分为两层：(1) 顶层 `QCAVariant` 枚举 (`FS_QCA = "fsqca"`, `CS_QCA = "csqca"`)；(2) `CalibrationType` 已重命名为 `CalibrationMethod`（仅表示算法）。`ConditionSet` 有 `qca_variant: QCAVariant` 字段。
**来源**: 需求变更审查, 评审者#2026-05-24

### ~~FIXME-27: models/qca.py:49-77 — `CalibrationParams` 仅支持 fuzzy 三阈值~~ [已修复 2026-05-26]

**文件**: `src/experiment_engine/models/qca.py`
**严重程度**: 🟡 警告
**问题**: `CalibrationParams` 字段 `threshold_full_in`、`threshold_full_out`、`crossover_point` 是模糊集专有的三阈值方案。csQCA crisp 校准只需要一个 `threshold` 值。
**修复**: `CrispCalibrationParams` 已定义（单一阈值字段），与 `FuzzyCalibrationParams` 并存，validator 中互斥验证。
**来源**: 需求变更审查, 评审者#2026-05-24

### ~~FIXME-29: Settings.tsx — 缺少 fsQCA/csQCA 方法选择器~~ [已修复 2026-05-26]

**文件**: `src/pages/Settings.tsx`
**严重程度**: 🟡 警告
**问题**: Settings 页面有"Calibration Method"下拉框（direct/indirect/fuzzy_direct），但没有顶层 fsQCA vs csQCA 选择器。用户无法告知系统应使用模糊集还是清晰集分析。
**修复**: Settings 页面 Calibration Defaults 区域顶部已添加 fsQCA/csQCA 切换控件。选 csQCA 时校准阈值界面自动调整为 crisp 模式。
**来源**: 客户代表#2026-05-24

### ~~FIXME-30: Results.tsx — 无 raw vs prototype 双结果并排对比视图~~ [已修复 2026-05-26]

**文件**: `src/pages/Results.tsx`, `src/store/QCAPipelineContext.tsx`
**严重程度**: 🟡 警告
**问题**: Results 页面仅展示单一 `analysisResult`。raw text 和 prototype text 应各自产出独立的分析结果供并排对比。
**修复**: QCAPipelineContext 已扩展为 `rawAnalysisResult` + `protoAnalysisResult` 双路。Results 页面已实现 raw/prototype/compare 视图，P1-31 实现了 raw-prototype 对比视图。
**来源**: 客户代表#2026-05-24

### ~~FIXME-31: DataInput.tsx:722-749 — 强制 raw/prototype 二选一违反需求~~ [已修复 2026-05-26]

**文件**: `src/pages/DataInput.tsx` (calibrationMode radio button 区域)
**严重程度**: 🟡 警告
**问题**: DataInput 页面的 Calibration Mode 区域使用 radio button 强制用户在 keyword 模式和 prototype 模式之间二选一。需求澄清后，raw text 和 prototype text 应同时可用而非互斥。
**修复**: 已移除互斥 radio button，改为两个并行的输入面板（Raw Text + Prototype Text 双区）。两个面板共享相同的条件集配置。
**来源**: 客户代表#2026-05-24

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

### FIXME-28: models/qca.py:173-186 — `TextCase.outcome` 字段语义过窄

**文件**: `src/experiment_engine/models/qca.py`
**严重程度**: 🟢 建议
**问题**: `TextCase.outcome` 定义为 `int = Field(0, ge=0, le=1)`，字段描述为 "Binary outcome (0 or 1) used directly as crisp-set membership"。但 fsQCA 模式下的 outcome 是连续值（0.0-1.0），当前 validator 拒绝浮点值。raw text 和 prototype text 都可能使用 fsQCA（continuous outcome）或 csQCA（binary outcome），TextCase 的 outcome 字段应支持两种类型。
**修复**: 将 `outcome: int` 改为 `outcome: float`（ge=0.0, le=1.0），字段描述改为 "Outcome membership score (0.0-1.0; use 0/1 for crisp-set, continuous for fuzzy-set)"。或在 fsQCA 模式下使用单独的 `fuzzy_outcome: float` 字段。
**来源**: 需求变更审查, 评审者#2026-05-24

### FIXME-32: domains.py — 原型预置数据硬编码，用户无法在线编辑

**文件**: `src/experiment_engine/text_calibration/domains.py`, `src/pages/DataInput.tsx`
**严重程度**: 🟢 建议
**问题**: 5 个领域的原型（prototype）预置数据硬编码在 `domains.py` 的 `DOMAIN_PRESETS` 字典中。关键词相关代码已移除，此 preset 现仅服务于 prototype 相似度引擎。用户只能通过导入外部 CSV/JSON 文件来"间接修改"原型文本，修改后的原型配置不持久化（刷新即丢失），也不保留用户的自定义编辑。
**用户影响**: 研究者在反复调优原型时需：(1) 导出当前原型 → (2) 用外部编辑器修改 → (3) 重新导入 → (4) 再次校准——每次修改需 4 步操作且离开应用。对于原型相似度方法，快速迭代原型文本是核心体验需求。
**修复**: (1) DataInput 页面添加"Edit Preset Prototypes"按钮，打开 inline 编辑表格（condition + prototype text + weight）；(2) 修改保存到 localStorage；(3) 添加"恢复默认原型"按钮。长期可考虑数据库持久化。(@see TODO P1-34)
**来源**: 客户代表#2026-05-24

### ~~FIXME-33: 产品路线图 — BERT 语义校准无产品定位文档~~ [已解决 2026-05-24]

**文件**: `.wolf/bert-vs-keyword-analysis.md` (新增)
**修复**: 产出完整 BERT-vs-关键词架构分析（~6000 字），回答：BERT 能否完全替代关键词匹配（结论：否），BERT 与关键词的根本区别（理论操作化 vs 统计相似度），Pyodide/WASM 技术可行性（BERT 必须在 JS 侧运行），4 个方案对比，阶段性推荐路径。
**提交**: 本分析

---

## 已移除的 MOOT 条目（2026-05-26 清理）

以下 FIXME 因引用的文件已被删除而移除。全部关键词匹配基础设施（keyword_dict.py、prototype_similarity.py 等）已从代码库中移除，BERT/Prototype 相似度已成为唯一的 ScoringSource。

| FIXME | 描述 | 移除原因 |
|-------|------|----------|
| FIXME-14 | bigram 跨标点误匹配 | `keyword_dict.py` 已删除 |
| FIXME-19 | prototype_similarity.py weight 字段未使用 | `prototype_similarity.py` 已删除，CosineSimilarityEngine 有自己的 weight 系统 |
| FIXME-34 | bigram 切词导致否定词构造被误匹配 | `keyword_dict.py` 已删除 |
| FIXME-35 | ScoringSource 枚举无 BERT 预留 | BERT PROTOTYPE 现为唯一 ScoringSource，此问题不再适用 |
| FIXME-36 | 校准策略假设 raw score 来自关键词匹配分布 | 所有关键词代码已移除 |

---

## 统计

| 严重程度 | 原始 | 已修复 | 新增(需求变更+客户代表+技术顾问) | 已移除(MOOT) | 剩余 |
|----------|------|--------|----------------------|-------------|------|
| 🔴 严重 | 5 (FIXME-1~5) | 5 | 2 (FIXME-23, 24) | 0 | **0** |
| 🟡 警告 | 11 (FIXME-6~16) | 10 (FIXME-6~13, 15, 16) | 8 (FIXME-25, 26, 27, 29, 30, 31, 34, 35) | 3 (FIXME-14, 34, 35) | **0** |
| 🟢 建议 | 6 (FIXME-17~22) | 5 (FIXME-17, 18, 20, 21, 33) | 2 (FIXME-28, 32) | 2 (FIXME-19, 36) | **3** (FIXME-22, 28, 32) |
| **合计** | **22** | **20** | **12** | **5** | **3** |

下一次 session 建议优先处理（均为 🟢 建议级别，无阻塞项）：

1. 🟢 FIXME-22 → `calibrate_indirect` k=10 硬编码（代码质量改进）
2. 🟢 FIXME-28 → `TextCase.outcome` 字段类型从 int 改为 float 以支持 fsQCA 连续 outcome
3. 🟢 FIXME-32 → domains.py 原型预置数据支持在线编辑和 localStorage 持久化
