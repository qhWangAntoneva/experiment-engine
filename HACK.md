# HACK — QCA Analysis Tool

> 自动生成于 2026-05-24 | 来源：三方审查中识别出的技术债务、设计妥协、临时方案
> HACK 区别于 FIXME：HACK 记录的是**有意的设计权衡/临时方案**（而非 bug），需要在未来重新审视

---

## 架构层面

### HACK-1: 字符 n-gram 替代 jieba 分词

**位置**: `src/experiment_engine/text_calibration/keyword_dict.py:83-96`
**性质**: 设计权衡
**描述**: 因"纯 Python + numpy，不额外安装依赖"约束，使用滑动窗口 bigram 分词替代 jieba。优点是无外部依赖，缺点是无法处理多字词、同义词和标点移除后的跨句匹配。
**风险**: bigram 跨标点误匹配（见 FIXME-14），对正式书面中文可接受但对口语/网络文本准确度下降。
**何时重新审视**: 当 Pyodide 支持 jieba 安装或项目接受外部依赖时，应迁移到 jieba + 自定义词典。
**来源**: cerebrum.md#5.1, 评审者#15

### HACK-2: Pyodide CDN 策略 — 50MB 核心从 jsDelivr 加载

**位置**: `src/pyodide/engine.ts`, `.github/workflows/deploy.yml`
**性质**: 设计权衡
**描述**: Pyodide 核心 50MB 从 jsDelivr CDN 加载，仅 ~80KB Python 源模块自托管（tar.gz 挂载），以避开 GitHub Pages 1GB 软限制。代价是首次加载需 30MB+ 网络请求，离线不可用。
**风险**: CDN 不可用时工具完全无法启动。中国大陆用户访问 jsDelivr 可能较慢。
**何时重新审视**: 当移到非 GitHub Pages 托管或打包为 Electron 桌面版时。
**来源**: cerebrum.md 决策日志, 客户#S4

### HACK-3: pydantic v2 ↔ dataclass 双后端方案未实现

**位置**: `src/experiment_engine/models.py`
**性质**: 未完成的设计
**描述**: cerebrum.md 决策日志记录了"采用 Pydantic v2 → dataclass 双后端方案，通过 IN_BROWSER 门控选择模型后端"，但代码库中不存在任何 `IN_BROWSER`、`models_browser.py` 或 dataclass shim 实现。当前 Pyodide 环境直接使用 Pydantic v2，依赖 pydantic-core Rust 二进制通过 Pyodide 编译。
**风险**: pydantic-core 在 Pyodide 下的兼容性未经过充分测试，未来版本升级可能 break。
**何时重新审视**: 如果 pydantic-core 在 Pyodide 中出问题，或要减小 WASM 包体积。
**来源**: cerebrum.md 决策日志, 技术顾问探索发现

### HACK-4: QCA 分析全部在 Web Worker 单线程中运行

**位置**: `src/services/pyodide.worker.ts`
**性质**: 设计约束
**描述**: Pyodide 在 Web Worker 中运行，所有 Python 调用通过 message passing 串行化。虽然 UI 不冻结，但无法利用多核并行（如并行校准多个条件、bootstrap 重抽样）。
**风险**: 大数据集（10000+ 文本）分析可能需要数分钟。
**何时重新审视**: 当浏览器支持 SharedArrayBuffer + Pyodide 多线程或迁移到服务端方案时。
**来源**: 架构分析

### ~~HACK-5: Quine-McCluskey 不支持 don't-care minterm~~ [已解决 2026-05-24]

**位置**: `src/experiment_engine/qca_engine/minimization.py`
**性质**: 功能缺口
**描述**: QM 现已支持 `dont_care_minterms` 参数。所有 minterms（常规 + don't-care）参与 prime implicant 生成，但 don't-care 不进入覆盖表（idx >= n_reg 的列不建）。见 FIXME-1。
**提交**: c4c6aa2
**来源**: 评审者#1

---

## 代码层面

### ~~HACK-6: calibrator.py 硬编码的 if/elif 校准方法选择~~ [已解决 2026-05-24]

**位置**: `src/experiment_engine/text_calibration/calibrator.py`, `src/experiment_engine/text_calibration/strategies.py` (新增)
**性质**: 技术债务
**描述**: `_apply_calibration()` 现已使用 `CalibrationStrategyRegistry` 策略模式查找，新增校准方法只需注册 `CalibrationStrategy` 实例，无需修改 `TextCalibrationStage`。详见 `strategies.py`。
**提交**: 10dbed0
**来源**: 技术顾问#5

### HACK-7: DataInput.tsx 前端硬编码了默认条件集 YAML 模板

**位置**: `src/pages/DataInput.tsx:34-100`
**性质**: 重复实现
**描述**: `DEFAULT_CONDITION_SET_YAML` 常量在前端硬编码，与 `domains.py` 的领域预设功能重复。前端 YAML 模板和 Python 领域预设必须人工保持同步。
**风险**: 前后端领域预设不同步会导致"前端显示的关键词"与"实际分析使用的关键词"不一致。
**何时重新审视**: 实现 TODO P1-16（前端解析归一到 Pyodide Worker）时同步解决。
**来源**: 技术顾问#7

### ~~HACK-8: pyodide.worker.ts 使用 JS 模板字符串嵌入 Python 代码~~ [已解决 2026-05-24]

**位置**: `src/services/pyodide.worker.ts`, `src/experiment_engine/pyodide_handlers.py` (新增)
**性质**: 技术债务（维护性已修复）
**描述**: Python handler 代码已提取到 `pyodide_handlers.py` 的独立函数中（pytest/ruff/mypy 可覆盖）。Worker 使用通用 `runHandler()` 模板，每个 handler 从 ~50 行缩减到 ~8 行。Worker 从 659 行缩减到 464 行。同步修复 2 个隐蔽运行时 bug。
**提交**: d08786c
**来源**: 技术顾问#2

### HACK-9: PluginRegistry 全局单例

**位置**: `src/experiment_engine/plugins.py:77-238`
**性质**: 技术债务
**描述**: `PluginRegistry` 是全局单例（`_instance` 类变量），测试通过 `reset_instance()` 在每次测试前重置，但多线程/并行测试下线程不安全。
**风险**: pytest-xdist 并行测试可能互相干扰，同一进程无法运行两个独立 QCA 管道。
**何时重新审视**: 引入并行测试或需要多租户场景前必须重构。 @see TODO P2-15
**来源**: 技术顾问#9

### HACK-10: 前端的 parseTextContent() 与后端的 TextCorpusReader 功能重复

**位置**: `src/pages/DataInput.tsx:120-168`, `src/experiment_engine/io/readers.py`
**性质**: 重复逻辑
**描述**: 前端在浏览器端手动解析 CSV/JSON/TXT，与 Python 端 `TextCorpusReader` 功能重复。CSV 转义符、编码处理在两处可能产生不同结果。
**风险**: 前端预检通过但后端解析失败，用户看到不一致的错误信息。
**何时重新审视**: 实现 TODO P1-16 时解决。
**来源**: 技术顾问#7

### HACK-13: 预置词典硬编码在 domains.py [NEW 需求变更]

**位置**: `src/experiment_engine/text_calibration/domains.py`
**性质**: 设计妥协
**描述**: 5 个领域的 200+ 关键词词典全部硬编码为 `domains.py` 中的 Python dict 常量。用户修改词典需要前端导入功能或手工编辑代码。需求变更后，每个条件需要同时定义关键词和 prototype 文本，固定代码中的词典结构阻碍条件级别的灵活配置。
**风险**: 研究者的领域知识无法方便地加入词典，自定义词典覆盖预置词典的行为不透明。
**何时重新审视**: 实现 TODO P1-34 + TODO P1-1 时解决——前端条件编辑器 + localStorage 持久化 + "恢复默认词典"。
**来源**: 客户代表分析, 评审者#2026-05-24

---

## 测试层面

### ~~HACK-11: QCA 核心算法仅通过集成测试覆盖~~ [已解决 2026-05-24]

**位置**: `tests/test_qca_core.py` (新增)
**性质**: 测试策略缺口
**描述**: 新增 104 个单元测试覆盖全部 7 个核心 QCA 模块（consistency/truth_table/minimization/necessity/sufficiency/calibrator/keyword_dict），使用 Ragin (2008) Lipset 数据集作为黄金标准基准。测试套件 361→465。
**提交**: d08786c
**来源**: 技术顾问#3, 评审者#20

### HACK-12: 零前端自动化测试

**位置**: `src/pages/`, `src/components/`, `src/hooks/`, `src/store/`
**性质**: 测试空白
**描述**: 项目有 7 个 Python 测试文件但 0 个前端测试。13 种 PipelineStage 的状态转换、useReducer reducer 纯逻辑、useQCAWorkflow hook 全部无测试覆盖。bug-010（`'running-robustness'` 错误用于 counterfactuals）和 bug-011（错误 action type）是缺乏前端测试的直接后果。
**风险**: 状态管理 bug 难以在 CR 中发现，仅在手动测试时暴露。
**何时重新审视**: 实现 TODO P2-18 时解决。
**来源**: 技术顾问#12

### HACK-14: `ScoringSource.PROTOTYPE` 将原型文本建模为独立模式而非通用 scoring 方法 [NEW 需求变更]

**位置**: `models/qca.py` (ScoringSource), `calibrator.py` (_compute_raw_scores), `pyodide_handlers.py` (handle_calibrate_prototype), `DataInput.tsx` (calibrationMode), `QCAPipelineContext.tsx` (prototype stages)
**性质**: 设计错误（基于错误需求理解）
**描述**: 当前代码将 prototype text 处理为独立于 keyword 的校准模式，由 `ScoringSource.PROTOTYPE` 枚举值驱动全链路分支（前后端各一条独立管道）。需求澄清后，prototype 相似度应是所有条件通用的**可选 scoring 来源之一**（和 keyword 相似度并列），而非管道级模式切换。整个 `ScoringSource.PROTOTYPE` → `handle_calibrate_prototype` → `calibrate-prototype-done` 链路是过渡期遗物。
**风险**: 每新增一种 scoring 方法就需要新增一条独立管道（违反开闭原则）；raw + prototype 的对比分析无法在同一管道中完成。
**何时重新审视**: 立即——这是 P0-9 阻塞项。重构为统一管道 + 条件粒度 scoring 来源 + 双批次输出对比。
**来源**: 需求变更审查, 评审者#2026-05-24

### HACK-15: 校准类型全链路硬编码为 fuzzy-set，缺少 csQCA 门控 [NEW 需求变更]

**位置**: `strategies.py` (仅注册 4 个 fuzzy 策略), `truth_table.py` (fuzzy AND/consistency 硬编码), `calibrator.py` (仅 fuzzy 校准), `cli.py` (无 variant 参数)
**性质**: 功能缺口 / 技术债务
**描述**: 整个 QCA 分析链路（calibrate → truth table → minimize → analyze）硬编码为 fuzzy-set 逻辑。没有 `QCAVariant` 参数来控制是走 fuzzy 还是 crisp 分支。csQCA 启用需要在以下位置添加门控：strategies.py（新增 CrispCalibration）、truth_table.py（配置隶属度用 crisp AND=min(val,1-val)、consistency 用 strict subset proportion）、analyzer.py（参数名和 docstring 更新）。
**风险**: 用户在 csQCA 场景下只能通过人工强制设定 threshold_full_in/out 近似 crisp，方法不正确且结果误导。
**何时重新审视**: 立即——这是 P0-10 阻塞项。
**来源**: 需求变更审查, 评审者#2026-05-24

### HACK-16: prototype 字段在前端使用不一致 [NEW 客户代表]

**位置**: `src/pages/DataInput.tsx` (generatePrototypeConditionSet, parsePrototypeTexts), `src/types/qca.ts` (ConceptPrototype)
**性质**: 技术债务 / UI 不一致
**描述**: `ConceptPrototype` 类型定义了 `weight` 字段（Default 1.0），但：(1) `prototype_similarity.py:compute_similarities()` 不读取该字段（FIXME-19）；(2) 前端 `parsePrototypeTexts()` 硬编码 `weight: 1.0`（行 170、177），用户无法在 UI 中设置权重；(3) `generatePrototypeConditionSet()` 的 `hybrid_keyword_weight` 和 `hybrid_prototype_weight` 始终为 0，混合同样硬编码固定值。整体上 prototype 相关字段在前端的"定义"和"使用"之间脱节——type 定义暗示灵活权重，实际代码全部硬编码。
**风险**: 用户看到 type definition 中有 `weight` 字段却无法在 UI 中设置，造成"功能不完整"的印象。需求变更后，prototype 相似度作为 scoring 方法之一更需要权重可调（区分重要原型和次要原型）。
**何时重新审视**: 实现 P0-9（统一管道）时同步修复 prototype 字段的 UI 交互，让用户在条件编辑器中可调整原型权重。(@see TODO P2-21, FIXME-19)
**来源**: 客户代表分析#2026-05-24

### HACK-17: 代码库未为语义校准（BERT）预留扩展点 [NEW 客户代表，已分析: 2026-05-24]

**位置**: `calibrator.py` (_compute_raw_scores), `strategies.py`, `models/qca.py` (ScoringSource)
**性质**: 设计缺口
**描述**: 产品的长期路线包括 BERT 语义校准（TODO P1-32/33），但当前 `_compute_raw_scores()` 的 `ScoringSource` 枚举仅有 `KEYWORD`/`PROTOTYPE`/`HYBRID` 三种值，没有 `SEMANTIC` 或 `BERT` 预留。如果 BERT PoC 通过后需要新增语义 scoring，需修改 ScoringSource 枚举 + calibrator 全链路，属于破坏性变更。
**风险**: 将来新增 BERT scoring 需要同时修改 `ScoringSource` 枚举、`_compute_raw_scores` 分支、`CalibrationStrategyRegistry` 注册表、前端 TS 类型、Worker handler——至少涉及 5 个文件，且可能破坏现有 HYBRID 逻辑（如果 HYBRID 被解释为 keyword+bert 而非 keyword+prototype）。
**何时重新审视**: P1-32（BERT 产品定位设计）阶段需决定 ScoringSource 是否扩展或重构为更灵活的插件化 scoring 来源系统。建议 P0-9（统一管道）时预留 `bert` 作为 ScoringSource 的未来值。
**参考分析**: `.wolf/bert-vs-keyword-analysis.md` — 最终决议（2026-05-25）：BERT 作为辅助工具不做主引擎。浏览器端 BERT 等待 WebGPU >90% + Safari 稳定 + 模型 <30MB 后再评估。CLI 端 `qca bert-validate/suggest/coverage` 从 P1-32/33 开始实施。
**来源**: 客户代表分析#2026-05-24, 技术顾问 BERT 分析#2026-05-24

### HACK-18: BERT 推理无法在 Pyodide 中运行，必须在 JS 侧执行 [NEW 技术顾问分析]

**位置**: 架构层面（跨 Pyodide / JS Worker 边界）
**性质**: 架构约束
**描述**: sentence-transformers、transformers、torch 均无法在 Pyodide 中运行（torch 需要 C++ 扩展编译，无 WASM 后端；transformers 依赖 torch）。BERT 语义相似度计算必须在浏览器 JS 侧通过 ONNX Runtime Web 或 Transformers.js 执行，然后将相似度分数传回 Pyodide Python 环境进行校准。这意味着：(1) 需要一个独立的 BERT Web Worker；(2) Pyodide worker 和 BERT worker 之间需要通过主线程 postMessage 进行数据交换；(3) BERT worker 需要单独的生命周期管理（初始化、模型加载、推理、错误处理）。

当前 Pyodide 单 worker 架构将变为双 worker 架构（Pyodide Python worker + BERT JS worker）。
**风险**: 双 worker 通信复杂度增加：BERT worker 崩溃不影响关键字匹配但会使 BERT scoring 失败；首次加载从 ~50MB 增至 ~150MB（Pyodide 50MB + ONNX Runtime 5MB + BERT 量化模型 ~100MB）；中国用户访问 Hugging Face CDN 可能需要镜像。
**何时重新审视**: P1-33（BERT CLI 可行性 PoC）阶段验证纯 Python CLI 方案（非浏览器端！）。浏览器端双 Worker 架构等待 WebGPU 覆盖率 >90% + Safari 稳定支持 + ONNX 量化模型 <30MB 后再评估。当前不做浏览器端 BERT。
**参考分析**: `.wolf/bert-vs-keyword-analysis.md`, Section 5 + Section 10（最终决议）
**来源**: 技术顾问 BERT-vs-关键词分析#2026-05-24

---

## 统计

| 类别 | 数量 |
|------|------|
| 架构层面 | 6 (1 已解决) |
| 代码层面 | 10 (2 已解决) |
| 测试层面 | 2 (1 已解决) |
| **合计** | **18** (4 已解决, 6 新增需求变更+客户代表+技术顾问)
