# HACK — QCA Analysis Tool

> 自动生成于 2026-05-24 | 最后更新 2026-05-26
> HACK 区别于 FIXME：HACK 记录的是**有意的设计权衡/临时方案**（而非 bug），需要在未来重新审视
> Re-synced with actual codebase state on 2026-05-26.

---

## 架构层面

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

### ~~HACK-1: 字符 n-gram 替代 jieba 分词~~ [已解决 2026-05-26]

**位置**: `src/experiment_engine/text_calibration/keyword_dict.py:83-96` (文件已删除)
**性质**: 设计权衡 → **MOOT**
**描述**: 曾因"纯 Python + numpy，不额外安装依赖"约束，使用滑动窗口 bigram 分词替代 jieba。`keyword_dict.py` 已删除，BERT CLS embedding 已替代 bigram 匹配。
**来源**: cerebrum.md#5.1, 评审者#15

### ~~HACK-5: Quine-McCluskey 不支持 don't-care minterm~~ [已解决 2026-05-24]

**位置**: `src/experiment_engine/qca_engine/minimization.py`
**性质**: 功能缺口
**描述**: QM 现已支持 `dont_care_minterms` 参数。所有 minterms（常规 + don't-care）参与 prime implicant 生成，但 don't-care 不进入覆盖表（idx >= n_reg 的列不建）。见 FIXME-1。
**提交**: c4c6aa2
**来源**: 评审者#1

---

## 代码层面

### HACK-7: DataInput.tsx 前端硬编码了默认条件集 YAML 模板

**位置**: `src/pages/DataInput.tsx:34-100`
**性质**: 重复实现
**描述**: `DEFAULT_CONDITION_SET_YAML` 常量在前端硬编码，与 `domains.py` 的领域预设功能重复。前端 YAML 模板和 Python 领域预设必须人工保持同步。
**风险**: 前后端领域预设不同步会导致"前端显示的关键词"与"实际分析使用的关键词"不一致。
**何时重新审视**: 实现 TODO P1-16（前端解析归一到 Pyodide Worker）时同步解决。
**来源**: 技术顾问#7

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

### HACK-13: 预置词典/原型硬编码在 domains.py

**位置**: `src/experiment_engine/text_calibration/domains.py`
**性质**: 设计妥协
**描述**: 5 个领域的 prototype 预设全部硬编码为 `domains.py` 中的 Python 常量。用户修改预设需要前端导入功能或手工编辑代码。底层问题（硬编码预设）仍然存在，但内容已从 keyword 词典转换为 prototype 预设——与 BERT PROTOTYPE scoring 方法对齐。
**风险**: 研究者的领域知识无法方便地加入预设，自定义预设覆盖预置预设的行为不透明。
**何时重新审视**: 实现 TODO P1-34 + TODO P1-1 时解决——前端条件编辑器 + localStorage 持久化 + "恢复默认预设"。
**来源**: 客户代表分析, 评审者#2026-05-24

### ~~HACK-6: calibrator.py 硬编码的 if/elif 校准方法选择~~ [已解决 2026-05-24]

**位置**: `src/experiment_engine/text_calibration/calibrator.py`, `src/experiment_engine/text_calibration/strategies.py` (新增)
**性质**: 技术债务
**描述**: `_apply_calibration()` 现已使用 `CalibrationStrategyRegistry` 策略模式查找，新增校准方法只需注册 `CalibrationStrategy` 实例，无需修改 `TextCalibrationStage`。详见 `strategies.py`。
**提交**: 10dbed0
**来源**: 技术顾问#5

### ~~HACK-8: pyodide.worker.ts 使用 JS 模板字符串嵌入 Python 代码~~ [已解决 2026-05-24]

**位置**: `src/services/pyodide.worker.ts`, `src/experiment_engine/pyodide_handlers.py` (新增)
**性质**: 技术债务（维护性已修复）
**描述**: Python handler 代码已提取到 `pyodide_handlers.py` 的独立函数中（pytest/ruff/mypy 可覆盖）。Worker 使用通用 `runHandler()` 模板，每个 handler 从 ~50 行缩减到 ~8 行。Worker 从 659 行缩减到 464 行。同步修复 2 个隐蔽运行时 bug。
**提交**: d08786c
**来源**: 技术顾问#2

### ~~HACK-14: `ScoringSource.PROTOTYPE` 将原型文本建模为独立模式而非通用 scoring 方法~~ [已解决 2026-05-26]

**位置**: `models/qca.py` (ScoringSource), `calibrator.py` (_compute_raw_scores), `pyodide_handlers.py` (handle_calibrate)
**性质**: 设计错误（基于错误需求理解）→ **RESOLVED**
**描述**: 原先将 prototype text 处理为独立于 keyword 的校准模式，由 `ScoringSource.PROTOTYPE` 枚举值驱动全链路分支。现已统一：`ScoringSource` 仅有 `PROTOTYPE`，`handle_calibrate` 为统一入口，不再有管道级模式切换。
**来源**: 需求变更审查, 评审者#2026-05-24

### ~~HACK-15: 校准类型全链路硬编码为 fuzzy-set，缺少 csQCA 门控~~ [已解决 2026-05-26]

**位置**: `strategies.py`, `truth_table.py`, `calibrator.py`, `cli.py`
**性质**: 功能缺口 / 技术债务 → **RESOLVED**
**描述**: 原先整个 QCA 分析链路硬编码为 fuzzy-set 逻辑。现已实现 `QCAVariant` 枚举（含 `CRISP` 和 `FUZZY`）及 crisp calibration 策略，`handle_calibrate` 根据 variant 参数选择校准路径。
**来源**: 需求变更审查, 评审者#2026-05-24

### ~~HACK-16: prototype 字段在前端使用不一致~~ [已解决 2026-05-26]

**位置**: `src/pages/DataInput.tsx`, `src/types/qca.ts` (ConceptPrototype)
**性质**: 技术债务 / UI 不一致 → **MOOT**
**描述**: 曾因 `ConceptPrototype.weight` 字段在前端硬编码为 1.0，用户无法在 UI 中设置权重。`prototype_similarity.py` 已删除——BERT CLS embedding 替代了旧的 prototype similarity 计算，该 HACK 随之失效。
**来源**: 客户代表分析#2026-05-24

### ~~HACK-17: 代码库未为语义校准（BERT）预留扩展点~~ [已解决 2026-05-26]

**位置**: `calibrator.py` (_compute_raw_scores), `strategies.py`, `models/qca.py` (ScoringSource)
**性质**: 设计缺口 → **MOOT**
**描述**: 曾因 `ScoringSource` 仅有 `KEYWORD`/`PROTOTYPE`/`HYBRID` 担心 BERT 扩展无门。BERT PROTOTYPE 现已成为主要 scoring 方法——`ScoringSource` 不再需要 `BERT` 枚举值，prototype similarity 直接走 BERT CLS embedding，无需额外的扩展点。
**来源**: 客户代表分析#2026-05-24, 技术顾问 BERT 分析#2026-05-24

### ~~HACK-18: BERT 推理无法在 Pyodide 中运行，必须在 JS 侧执行~~ [已解决 2026-05-26]

**位置**: 架构层面（跨 Pyodide / JS Worker 边界）
**性质**: 架构约束 → **RESOLVED**
**描述**: `BertEngine` 已通过 Transformers.js 实现，BERT 推理在 JS 侧执行，相似度分数传回 Python 校准管道。双 worker 通信路径已打通，不再是一个待解决的架构问题。
**来源**: 技术顾问 BERT-vs-关键词分析#2026-05-24

---

## 测试层面

### HACK-12: 零前端自动化测试

**位置**: `src/pages/`, `src/components/`, `src/hooks/`, `src/store/`
**性质**: 测试空白
**描述**: 项目有 7 个 Python 测试文件但 0 个前端测试。13 种 PipelineStage 的状态转换、useReducer reducer 纯逻辑、useQCAWorkflow hook 全部无测试覆盖。bug-010（`'running-robustness'` 错误用于 counterfactuals）和 bug-011（错误 action type）是缺乏前端测试的直接后果。
**风险**: 状态管理 bug 难以在 CR 中发现，仅在手动测试时暴露。
**何时重新审视**: 实现 TODO P2-18 时解决。
**来源**: 技术顾问#12

### ~~HACK-11: QCA 核心算法仅通过集成测试覆盖~~ [已解决 2026-05-24]

**位置**: `tests/test_qca_core.py` (新增)
**性质**: 测试策略缺口
**描述**: 新增 104 个单元测试覆盖全部 7 个核心 QCA 模块（consistency/truth_table/minimization/necessity/sufficiency/calibrator/keyword_dict），使用 Ragin (2008) Lipset 数据集作为黄金标准基准。测试套件 361→465。
**提交**: d08786c
**来源**: 技术顾问#3, 评审者#20

---

## 统计

| 类别 | 数量 |
|------|------|
| 架构层面 | 5 (2 已解决) |
| 代码层面 | 11 (7 已解决) |
| 测试层面 | 2 (1 已解决) |
| **合计** | **18** (10 已解决, 8 待解决) |
