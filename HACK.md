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

### HACK-6: calibrator.py 硬编码的 if/elif 校准方法选择

**位置**: `src/experiment_engine/text_calibration/calibrator.py:291-304`
**性质**: 技术债务
**描述**: `_apply_calibration()` 和 `_compute_raw_scores()` 使用硬编码 if/elif 分支选择校准方法和评分来源。每新增一种校准方法需直接修改 `TextCalibrationStage` 类。
**风险**: 违反开闭原则，长期维护成本递增。
**何时重新审视**: 新增第 4 种校准方法前必须重构为策略模式。 @see TODO P1-15
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

---

## 统计

| 类别 | 数量 |
|------|------|
| 架构层面 | 5 (1 已解决) |
| 代码层面 | 4 (1 已解决) |
| 测试层面 | 0 (2 已解决) |
| **合计** | **9** (3 已解决)
