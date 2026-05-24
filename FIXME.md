# FIXME — QCA Analysis Tool

> 自动生成于 2026-05-24 | 最后更新：2026-05-24 (BERT-vs-关键词分析)
> 严重程度：🔴 = 严重/必须修 | 🟡 = 警告/建议修 | 🟢 = 建议/锦上添花

---

## 🔴 严重 — 算法错误与数据损坏

### FIXME-23: 全项目 — "prototype = 独立校准模式" 架构基于错误假设 [NEW 需求变更]

**文件**: `calibrator.py`, `pyodide_handlers.py`, `pyodide.worker.ts`, `DataInput.tsx`, `QCAPipelineContext.tsx`, `qca.ts`
**严重程度**: 🔴 严重
**问题**: 整个 prototype 相关代码将 prototype text 视为独立的校准模式（`ScoringSource.PROTOTYPE`、前端模式选择器、`handle_calibrate_prototype` 专用 handler、`calibrating-prototype` pipeline stage）。用户澄清：raw text 和 prototype text 是同一类型输入，通过相同管道生成 CLI，仅在最后分别输出各自对应的 score 和 QCA result。

**影响范围**:
- `ScoringSource.PROTOTYPE` 枚举值 — 不应存在，prototype 相似度应是所有条件可选的 scoring 方法，非管道级模式
- `calibrator.py:_compute_raw_scores()` PROTOTYPE/HYBRID 分支 — 应重构为统一 scoring
- `pyodide_handlers.py:handle_calibrate_prototype()` — 应与 `handle_calibrate()` 合并
- `pyodide.worker.ts:handleCalibratePrototype()` — 应删除独立 handler
- `DataInput.tsx` 模式选择器 + prototype 专用 UI — 应改为双输入区（raw + prototype 并排）
- `QCAPipelineContext.tsx` prototype 专用 stage/action — 应删除
- `pyodide.ts:calibratePrototype()` — 应统一到 calibrate()

**修复**: 消除 ScoringSource.PROTOTYPE 概念。PrototypeSimilarityEngine 作为所有条件可选使用的文本相似度计算的底层引擎保留。管道对 raw text 和 prototype text 各执行一次完整的 calibrate→analyze，结果分别输出供对比。
**来源**: 需求变更审查, 评审者#2026-05-24

### FIXME-24: 全项目 — csQCA（清晰集 QCA）全链路缺失 [NEW 需求变更]

**文件**: `models/qca.py` (CalibrationType), `strategies.py`, `calibrator.py`, `truth_table.py`, `cli.py`
**严重程度**: 🔴 严重
**问题**: 软件完全不支持 csQCA（清晰集 QCA）。当前所有校准方法均为模糊集（direct/indirect/fuzzy_direct/passthrough），真值表构建使用 `min(membership, 1-membership)` 的模糊逻辑 AND，CLI 无任何 crisp-set 选项。

**缺失清单**:
1. `CalibrationType` 枚举无 `CRISP_SET` 值 — models/qca.py:32-38
2. `CalibrationParams` 仅有 fuzzy 三阈值 (full_in/crossover/full_out) — 无 crisp 单阈值字段 — models/qca.py:49-77
3. `strategies.py` 无 `CrispCalibration` 策略类 — strategies.py:266 仅注册 4 个 fuzzy 策略
4. `TruthTableBuilder._compute_config_membership()` 仅实现 fuzzy AND — truth_table.py:96-112
5. `TruthTableBuilder._compute_consistency()` 使用 fuzzy subset consistency — truth_table.py:114-121 (crisp 应计数严格子集比例)
6. `cli.py` 无 `--variant csqca` 选项 — 9 个命令都硬编码为 fuzzy-set
7. `analyzer.py:analyze()` 参数名和 docstring 全部写 "fuzzy" — analyzer.py:86-90

**修复**: 全链路实现：(1) models: 新增 `CRISP_SET` CalibrationType, `CrispCalibrationParams`；(2) strategies: 新增 `CrispCalibration`；(3) truth_table: 根据 variant 选择 fuzzy/crisp 配置隶属度和一致性计算（可使用策略模式或 if/else 门控）；(4) CLI: `--variant=csqca` 全局参数；(5) 前端: Settings 页新增 QCA Variant 选择。
**来源**: 需求变更审查, 评审者#2026-05-24

### ~~FIXME-1: counterfactual.py — produce_parsimonious_solution 算法错误~~ [已修复 2026-05-24 Phase 1, 提交 c4c6aa2]
### ~~FIXME-2: calibrator.py — 混合 scoring_source 列索引偏移~~ [已修复 2026-05-24 Phase 1, 提交 c4c6aa2]
### ~~FIXME-3: calibrator.py — calibrate_ragin 实现的是分段线性而非 log-odds~~ [已修复 2026-05-24 Phase 1, 提交 c4c6aa2]
### ~~FIXME-4: calibrator.py — match_corpus() 每个条件重复调用~~ [已修复 2026-05-24 Phase 1, 提交 c4c6aa2]
### ~~FIXME-5: pipeline.py — Stage 失败后静默传递损坏数据~~ [已修复 2026-05-24 Phase 2, 提交 9842e11]

---

## 🟡 警告 — 设计缺陷与遗漏

### FIXME-25: models/qca.py:192 — `FuzzySetData` 命名太窄 [NEW 需求变更]

**文件**: `src/experiment_engine/models/qca.py`
**严重程度**: 🟡 警告
**问题**: 类名为 `FuzzySetData` 但已接受 0/1 crisp-set 值（validator 仅检查 `[0,1]` 范围），csQCA 启用后此名称产生语义混淆。该类实际承载的是"校准后的 membership data"（模糊或清晰均可）。
**修复**: 重命名为 `MembershipData` 或 `QCAMembershipData`。保留 `FuzzySetData` 作为 deprecated alias 向后兼容。影响范围：qca.py (类定义), analyzer.py (类型注解), truth_table.py (参数类型), pyodide_handlers.py (导入), test_qca_core.py (85+ 处引用), test_prototype_similarity.py, types/qca.ts (FuzzySetDataJSON), pyodide.ts, pyodide.worker.ts。
**来源**: 需求变更审查, 评审者#2026-05-24

### FIXME-26: models/qca.py:32-38 — `CalibrationType` 混合了校准算法与 QCA variant 的概念 [NEW 需求变更]

**文件**: `src/experiment_engine/models/qca.py`
**严重程度**: 🟡 警告
**问题**: `CalibrationType` 枚举值 DIRECT/INDIRECT/FUZZY_DIRECT 描述的是**校准算法**，但没有层次区分 fsQCA vs csQCA。实际上，csQCA 也可以用 direct 方法（单一阈值二分），所以算法和 set 类型是正交的两个维度。当前扁平化的枚举无法表达"csQCA + direct calibration"的组合。
**修复**: 拆分为两层：(1) 新增顶层 `QCAVariant` 枚举 (`FS_QCA = "fsqca"`, `CS_QCA = "csqca"`)；(2) 重命名 `CalibrationType` → `CalibrationMethod`（仅表示算法）。`ConditionSet` 新增 `qca_variant: QCAVariant` 字段。
**来源**: 需求变更审查, 评审者#2026-05-24

### FIXME-27: models/qca.py:49-77 — `CalibrationParams` 仅支持 fuzzy 三阈值 [NEW 需求变更]

**文件**: `src/experiment_engine/models/qca.py`
**严重程度**: 🟡 警告
**问题**: `CalibrationParams` 字段 `threshold_full_in`、`threshold_full_out`、`crossover_point` 是模糊集专有的三阈值方案。csQCA crisp 校准只需要一个 `threshold` 值（raw score >= threshold → 1, else → 0）。当前设计无法表达 crisp 参数。
**修复**: 定义为 Union type 或拆分为 `FuzzyCalibrationParams` + `CrispCalibrationParams`（均继承 base），或在 `CalibrationParams` 中新增可选 `crisp_threshold` 字段并在 validator 中互斥验证。
**来源**: 需求变更审查, 评审者#2026-05-24

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

### FIXME-28: models/qca.py:173-186 — `TextCase.outcome` 字段语义过窄 [NEW 需求变更]

**文件**: `src/experiment_engine/models/qca.py`
**严重程度**: 🟢 建议
**问题**: `TextCase.outcome` 定义为 `int = Field(0, ge=0, le=1)`，字段描述为 "Binary outcome (0 or 1) used directly as crisp-set membership"。但 fsQCA 模式下的 outcome 是连续值（0.0-1.0），当前 validator 拒绝浮点值。需求变更后，raw text 和 prototype text 都可能使用 fsQCA（continuous outcome）或 csQCA（binary outcome），TextCase 的 outcome 字段应支持两种类型。
**修复**: 将 `outcome: int` 改为 `outcome: float`（ge=0.0, le=1.0），字段描述改为 "Outcome membership score (0.0-1.0; use 0/1 for crisp-set, continuous for fuzzy-set)"。或在 faQCA 模式下使用单独的 `fuzzy_outcome: float` 字段。
**来源**: 需求变更审查, 评审者#2026-05-24

### FIXME-29: Settings.tsx — 缺少 fsQCA/csQCA 方法选择器 [NEW 客户代表]

**文件**: `src/pages/Settings.tsx`
**严重程度**: 🟡 警告
**问题**: Settings 页面有"Calibration Method"下拉框（direct/indirect/fuzzy_direct），但没有顶层 fsQCA vs csQCA 选择器。用户无法告知系统应使用模糊集还是清晰集分析。csQCA 需求变更后，此选择器是决定校准参数界面和结果解读方式的关键入口，缺失意味着 csQCA 无法从前端启用。
**用户影响**: 研究者如果需要在同一工具中对比 fsQCA 和 csQCA 的结果（如：先模糊集分析发现解的稳定性，再清晰集验证关键变量），当前必须手动修改所有条件的校准类型，无法一键切换。
**修复**: 在 Settings 页面 Calibration Defaults 区域顶部添加 radio button 组：fsQCA / csQCA。选 csQCA 时：(1) 校准阈值设定（full_in/full_out/crossover）灰显并固定值；(2) Calibration Method 下拉框限制为 crisp 选项；(3) 频率阈值提示文案从"隶属度"改为"案例数"。(@see TODO P1-4)
**来源**: 客户代表#2026-05-24

### FIXME-30: Results.tsx — 无 raw vs prototype 双结果并排对比视图 [NEW 客户代表]

**文件**: `src/pages/Results.tsx`, `src/store/QCAPipelineContext.tsx`
**严重程度**: 🟡 警告
**问题**: Results 页面仅展示单一 `analysisResult`。需求澄清后，raw text 和 prototype text 应各自产出独立的分析结果（两套 membership data、两个 TruthTable、两组 QCASolutions），用户需要并排对比。当前 `QCAPipelineState` 仅存一份 `fuzzyData` 和 `analysisResult`，无法承载双路结果。
**用户影响**: 研究者完成 raw + prototype 双路分析后，只能看到其中一组结果，无法对比"原型文本校准的解"与"真实公民反馈文本校准的解"是否一致——而这正是原型输入的核心使用场景。
**修复**: (1) QCAPipelineContext 扩展为 `rawAnalysisResult` + `protoAnalysisResult` 双路；(2) Results 页面添加 tab 切换（Raw / Prototype / Compare）；(3) Compare tab 以并排表格展示差异（真值表行差异、解项差异、N/S metrics 差异）。(@see TODO P1-2, P1-3)
**来源**: 客户代表#2026-05-24

### FIXME-31: DataInput.tsx:722-749 — 强制 raw/prototype 二选一违反需求 [NEW 客户代表]

**文件**: `src/pages/DataInput.tsx` (calibrationMode radio button 区域)
**严重程度**: 🟡 警告
**问题**: DataInput 页面的 Calibration Mode 区域使用 radio button 强制用户在 keyword 模式和 prototype 模式之间二选一。需求澄清后，raw text 和 prototype text 是同一类型输入，应同时可用而非互斥。当前 UI 直接阻碍了用户的核心工作流（同时上传两批文本并对比结果）。
**用户影响**: 用户被强制选择"只输入 raw text"或"只输入 prototype text"，无法同时输入两者并运行对比分析，产品无法满足"对比理论期望与实际数据"这一核心使用场景。
**修复**: 将 radio button 切换改为两个并行的输入面板（双 tab 或上下分区）："Raw Text"面板（上传/粘贴公民反馈原文）+ "Prototype Text"面板（上传/粘贴原型文本）。两个面板共享相同的条件集/词典配置。移除 calibrationMode 状态，移除 prototype 专用的 parsePrototypeCSV/handleProtoFileUpload/handleProtoDrop。(@see TODO P1-1)
**来源**: 客户代表#2026-05-24

### FIXME-32: domains.py — 预置词典硬编码，用户无法在线编辑 [NEW 客户代表]

**文件**: `src/experiment_engine/text_calibration/domains.py`, `src/pages/DataInput.tsx`
**严重程度**: 🟢 建议
**问题**: 5 个领域的 200+ 关键词硬编码在 `domains.py` 的 `DOMAIN_PRESETS` 字典中。用户只能通过导入外部 CSV/JSON 词典文件来"间接修改"关键词集，修改后的词典不持久化（刷新即丢失），也不保留用户的自定义编辑。
**用户影响**: 研究者在反复调优词典时需：(1) 导出当前词典 → (2) 用外部编辑器修改 → (3) 重新导入 → (4) 再次校准——每次修改需 4 步操作且离开应用。对于高可解释性要求的关键词匹配方法，快速迭代词典是核心体验需求。
**修复**: (1) DataInput 页面添加"Edit Preset Dictionary"按钮，打开 inline 编辑表格（condition + keyword + weight + scope）；(2) 修改保存到 localStorage；(3) 添加"恢复默认词典"按钮。长期可考虑数据库持久化。(@see TODO P1-34, HACK-13)
**来源**: 客户代表#2026-05-24

### ~~FIXME-33: 产品路线图 — BERT 语义校准无产品定位文档~~ [已解决 2026-05-24]

**文件**: `.wolf/bert-vs-keyword-analysis.md` (新增)
**修复**: 产出完整 BERT-vs-关键词架构分析（~6000 字），回答：BERT 能否完全替代关键词匹配（结论：否），BERT 与关键词的根本区别（理论操作化 vs 统计相似度），Pyodide/WASM 技术可行性（BERT 必须在 JS 侧运行），4 个方案对比，阶段性推荐路径。
**提交**: 本分析

### FIXME-34: keyword_dict.py — bigram 切词导致否定词构造被误匹配到反向条件 [NEW 技术顾问分析]

**文件**: `src/experiment_engine/text_calibration/keyword_dict.py:32-58`
**严重程度**: 🟡 警告
**问题**: 文本"我对政府服务不满意"经 bigram 分词后为["我对", "对政", "政府", "府服", "服务", "务不", "不满", "满意"]。其中"满意"是一个独立 bigram，可以被 trust 领域的"满意"关键词（权重 0.6）匹配，导致同一条文本在 dissatisfaction 和 trust 两个互斥条件上都获得正分。这是 bigram 分词的固有限制——它无法识别"不满" 对 "满意" 的否定修饰关系。

此问题与 FIXME-14（跨标点误匹配）同源但语义影响不同：FIXME-14 是跨句误匹配，本题是同一合成词内反向误匹配，对互斥条件对（dissatisfaction vs trust, dissatisfaction vs gov_responsiveness）的语义区分度有直接影响。
**修复**: 在无 jieba 依赖约束下，可选方案：(1) 在分词时检测否定前缀（"不"、"没"、"无"等）并将后续字符标记为否定上下文；(2) 为互斥条件对（如 dissatisfaction 和 trust）设置互斥约束——同一文本在互斥条件上的分数不能同时高；(3) 引入 BERT 语义验证通道，标记存在否定构造的文本供人工审查。方案 (3) 与 BERT 路线图（P1-32/33）直接相关。
**来源**: 技术顾问 BERT-vs-关键词分析#2026-05-24

### FIXME-35: models/qca.py:41-47 — ScoringSource 枚举封闭，无 BERT/SEMANTIC 预留 [NEW 技术顾问分析]

**文件**: `src/experiment_engine/models/qca.py`
**严重程度**: 🟡 警告
**问题**: `ScoringSource` 枚举目前仅有 `KEYWORD`、`PROTOTYPE`、`HYBRID` 三个值。BERT 语义相似度作为一种本质不同的 scoring 来源（需要 JS 侧推理、不同的 raw score 分布特征、不同的用户输入要求），在枚举中无预留位置。将来新增 BERT scoring 时需要修改 `ScoringSource` 枚举 + `_compute_raw_scores` 分支 + `calibrator.py` + 前端 TS 类型 + Worker handler，属于破坏性变更。

HACK-17 记录了此设计缺口。本 FIXME 补充其严重程度和具体影响范围。
**修复**: 在实现 P1-32（BERT 产品定位）阶段，提前在 `ScoringSource` 中新增 `BERT = "bert"` 值，并在 `_compute_raw_scores` 添加占位分支（抛出 NotImplementedError 附带提示信息）。这样 P2-25（条件级混合模式）实现时无需修改枚举定义。
**来源**: 技术顾问 BERT-vs-关键词分析#2026-05-24

### FIXME-36: strategies.py — 所有校准策略假设 raw score 来自关键词匹配的分布 [NEW 技术顾问分析]

**文件**: `src/experiment_engine/text_calibration/strategies.py`
**严重程度**: 🟢 建议
**问题**: DirectCalibration、IndirectCalibration、RaginCalibration 三个策略类均通过 min-max 归一化（`(raw - min) / (max - min)`）将 raw score 映射到 [0,1]。这个归一化步骤假设 raw score 来自关键词匹配的计数求和分布（非负、有界、右偏）。BERT 余弦相似度的分布特征不同（理论范围 [0,1] 或 [-1,1]，实际集中在 [0.3, 0.9]，近似正态而非右偏），当前校准公式的交叉点设定和 logistic steepness 参数 k=10（见 FIXME-22）可能不适合 BERT 相似度的分布。

这不是算法 bug——当前公式对关键词是正确的——但 BERT 集成后，用户可能对同一 `CalibrationParams` 配置在 keyword 和 BERT 两种 scoring 来源下产生不同的隶属度分布感到困惑。
**修复**: (1) 为 BERT 相似度提供专用的默认校准参数建议（如阈值 full_in=0.85, full_out=0.40, crossover=0.65）；(2) 在 calibrator 中添加 raw score 分布诊断输出（mean, std, skew），帮助用户判断校准参数是否合理；(3) 长期可将校准参数的默认值与 ScoringSource 绑定。
**来源**: 技术顾问 BERT-vs-关键词分析#2026-05-24

---

## 统计

| 严重程度 | 原始 | 已修复 | 新增(需求变更+客户代表+技术顾问) | 剩余 |
|----------|------|--------|----------------------|------|
| 🔴 严重 | 5 (FIXME-1~5) | 5 | 2 | 2 (FIXME-23, 24) |
| 🟡 警告 | 11 (FIXME-6~16) | 10 (FIXME-6~13, 15, 16) | 8 | 9 (FIXME-14, 25, 26, 27, 29, 30, 31, 34, 35) |
| 🟢 建议 | 6 (FIXME-17~22) | 5 (FIXME-17, 18, 20, 21, 33) | 4 | 5 (FIXME-19, 22, 28, 32, 36) |
| **合计** | **22** | **20** | **14** | **16** |

下一次 session 建议优先处理：
1. 🔴 FIXME-23 → prototype 独立管道错误假设（阻塞所有 raw/prototype 统一工作）
2. 🔴 FIXME-24 → csQCA 全链路缺失（阻塞 fsQCA/csQCA 区分功能）
3. 🟡 FIXME-29 → Settings 缺少 fsQCA/csQCA 选择器（前端体验阻塞项）
4. 🟡 FIXME-31 → DataInput 强制 raw/prototype 二选一（前端体验阻塞项）
5. 🟡 FIXME-30 → Results 无并排对比视图（前端体验阻塞项）
6. 🟡 FIXME-25/26/27 → 模型重命名和重构（需求变更阻塞项 P0-11/12）
7. 🟡 FIXME-34/35/36 → BERT 架构预留（P1-32 阶段实现，非当前阻塞项）
8. 其余按严重程度递减
