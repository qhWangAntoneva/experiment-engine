# Cerebrum — QCA Text Analysis Tool

> OpenWolf 学习记忆。最后一次全面更新：2026-05-24
> 用途：新 agent 接手时的项目全貌参考。
> **当前状态**: 三方审查已完成，TODO/FIXME/HACK 就绪，下一 session 开始逐一修复。

---

## 0. 快速上手（新 session 必读）

**在开始任何工作前，先读这三个文件获取当前状态**：
- `TODO.md` — 51 项待办（8 P0 + 23 P1 + 20 P2），按优先级排序
- `FIXME.md` — 22 项 Bug/缺陷（6 🔴严重 + 10 🟡警告 + 6 🟢建议），含精确文件:行号
- `HACK.md` — 12 项技术债务与设计权衡

**推荐的开工顺序**（P0 优先）：
1. FIXME-1 → counterfactual.py parsimonious 算法错误（最严重的正确性 bug）
2. FIXME-3 → calibrate_ragin 实现错误（分段线性→logistic）
3. FIXME-2 → calibrator.py 列索引偏移
4. FIXME-4 → match_corpus() 重复调用优化
5. FIXME-5 → pipeline 错误处理 fail_fast
6. FIXME-6 → robustness coverage_stability=0
7. P0-3 → 为核心 QCA 模块补充单元测试（先写后修）

---

## 1. 项目身份

| 属性 | 值 |
|------|-----|
| **名称** | experiment-engine (包名) / QCA Text Analysis Tool (产品名) |
| **版本** | 0.2.0 |
| **一句话** | 将公民反馈中文文本自动转化为模糊集 QCA 分析结果 |
| **Python** | >=3.10 |
| **包管理器** | uv |
| **CLI 入口** | `qca` (9 个子命令) |
| **测试框架** | pytest (352 passed 历史基线) |

---

## 2. 领域模型：QCA 文本分析是什么

**输入**：公民反馈中文文本（CSV/JSON/TXT） + 条件定义（YAML，含关键词词典和校准参数）
**处理**：文本 → 关键词匹配 → 模糊校准 → 真值表 → 布尔最小化 → 必要/充分分析
**输出**：模糊隶属矩阵、真值表、QCA 解（复杂/精简/中间）、必要性/充分性指标、稳健性报告、LaTeX 报告

**5 个文本领域**（预置关键词词典）：
- `dissatisfaction` — 不满（投诉、举报、负面情感）
- `policy_demand` — 政策需求（建议、资源请求、立法呼吁）
- `co_production` — 合产请求（参与意愿、贡献提供、知识共享）
- `trust` — 信任（制度信任、能力感知、善意感知）
- `gov_responsiveness` — 政府响应（时效性、解决效果、透明度）

**核心约束**：纯 Python 实现（numpy 可用），不额外安装依赖，不调用 R 或其他包。

---

## 3. 架构：四层数据流

```
┌─────────────────────────────────────────────────────────────┐
│  第1层: text_calibration/  文本 → 模糊集                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ domains.py   │  │keyword_dict  │  │ calibrator.py     │   │
│  │ 5领域预设    │→│ 字符n-gram   │→│ 3种校准方法       │   │
│  │ 200+关键词   │  │ 中文匹配引擎 │  │ (direct/indirect/ │   │
│  └──────────────┘  └──────────────┘  │  ragin)           │   │
│                                       └──────────────────┘   │
│  condition.py: YAML ↔ ConditionSet 序列化                    │
│  training.py:  从标注样本通过分位数匹配估计校准阈值           │
├─────────────────────────────────────────────────────────────┤
│  第2层: qca_engine/  模糊集 → QCA 分析                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │consistency   │  │truth_table   │  │ minimization.py  │   │
│  │ 一致性/覆盖度│→│ 2^k配置枚举  │→│ Quine-McCluskey  │   │
│  │ 纯numpy公式  │  │ 频率+一致性  │  │ 质蕴含+最小覆盖  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ necessity.py │  │sufficiency   │  │ solution.py      │   │
│  │ X_i >= Y?    │  │ 解项 <= Y?   │  │ 公式格式化       │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│  analyzer.py: QCAnalyzerStage 编排全部上述组件（@register_stage）│
├─────────────────────────────────────────────────────────────┤
│  第3层: qca_engine/advanced/  高级分析                        │
│  robustness.py:  一致性/频率/校准敏感性 + bootstrap          │
│  counterfactual.py: 易/难反事实分类 → 复杂/精简/中间解       │
│  multi_outcome.py: 跨结果比较（共享条件、Jaccard 相似度）    │
├─────────────────────────────────────────────────────────────┤
│  第4层: 输出                                                   │
│  viz/qca_plots.py:     真值表热力图、N/S XY图、分布直方图    │
│  report/qca_reporter.py: 完整 LaTeX 报告（继承旧 latex_reporter）│
│  io/readers.py:        TextCorpusReader (CSV/JSON/TXT)      │
│  cli.py:               9 命令完整 CLI                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 完整模块路径清单

### 4.1 框架核心（保留自 0.1.0，未修改）

| 文件 | 职责 | 关键类/函数 |
|------|------|-----------|
| `pipeline.py` | Stage/Pipeline 抽象 | `Stage` (ABC: setup/process/teardown), `Pipeline` (composite) |
| `plugins.py` | 插件注册系统 | `BasePlugin(Stage)`, `PluginRegistry` (singleton), `@register_stage`, `PluginLoader` |
| `config.py` | YAML/JSON 配置加载 | `load_config()`, `merge_defaults()`, `apply_cli_overrides()` |
| `core/parallel.py` | 并行执行 | `ParallelStageGroup`, `ParallelPipeline` (ThreadPoolExecutor) |

### 4.2 数据模型

| 文件 | 职责 | 关键模型（30+个 Pydantic v2 模型） |
|------|------|----------------------------------|
| `models.py` | 所有数据模型 | **泛型**：`InputData[T]`, `OutputData[T]`, `PipelineResult`, `ExperimentConfig` |
| | | **QCA**：`TextDomain`, `ConditionDefinition`, `ConditionSet`, `CalibrationParams`, `KeywordEntry` |
| | | **训练**：`TrainingSample`, `TrainingDataset` |
| | | **核心数据**：`FuzzySetData` (ndarray + metadata) |
| | | **分析**：`TruthTable`, `TruthTableRow`, `QCASolutions`, `SolutionTerm`, `QCAAnalysisResult` |
| | | **必要性**：`NecessityResults`, `NecessityConditionResult` |
| | | **充分性**：`SufficiencyResults` |
| | | **稳健性**：`RobustnessReport`, `RobustnessTestResult` |
| | | **反事实**：`CounterfactualReport`, `CounterfactualClassification` |
| | | **多结果**：`MultiOutcomeReport` |

### 4.3 第1层：text_calibration/

| 文件 | 职责 | 关键类/函数 |
|------|------|-----------|
| `domains.py` | 5 领域 × 200+ 中文关键词预设 | `DOMAIN_PRESETS: dict[TextDomain, dict]`, `build_default_conditions(domain)` |
| `keyword_dict.py` | 中文关键词匹配引擎（字符 n-gram 分词，无 jieba 依赖） | `KeywordMatcher` (clean_text, tokenize, score_single), `ChineseKeywordDictionary` (match_text, match_corpus) |
| `condition.py` | 条件集 I/O（YAML 序列化 + Fluent Builder） | `ConditionDefinitionBuilder`, `ConditionSetBuilder`, `save_condition_set()`, `load_condition_set()` |
| `calibrator.py` | 文本校准 Stage（关键词分 → 模糊隶属 0-1） | `TextCalibrationStage(Stage)` — process() 调用 calibrate_direct/indirect/ragin |
| `training.py` | 从标注样本学习校准阈值 | `TrainingEngine` — fit() 用分位数匹配估计 threshold_full_in/out/crossover |

### 4.4 第2层：qca_engine/

| 文件 | 职责 | 关键类/方法 |
|------|------|-----------|
| `consistency.py` | 核心 QCA 数学（纯 numpy） | `ConsistencyCalculator` — subset_consistency, raw_coverage, unique_coverage, solution_consistency/coverage, fuzzy_and/or/not |
| `truth_table.py` | 真值表构建 | `TruthTableBuilder` — build() 枚举 2^k 配置、计算每个案例的配置隶属度（min 交集）、过滤 |
| `minimization.py` | Quine-McCluskey 布尔最小化 | `QuineMcCluskey` — minimize() 分组→合并→质蕴含→最小覆盖（贪心算法） |
| `necessity.py` | 必要条件分析 | `NecessityAnalyzer` — analyze() 对每个条件 + 其否定计算必要性（默认阈值 0.9） |
| `sufficiency.py` | 充分条件分析 | `SufficiencyAnalyzer` — analyze() 对解项计算一致性 + 原始/唯一/解覆盖度 |
| `solution.py` | 解公式格式化 | `SolutionFormatter` — 支持 boolean(*)/logical(∧¬)/latex 三种风格 |
| `analyzer.py` | 编排 Stage | `QCAnalyzerStage(BasePlugin)` — @register_stage("qca_analysis")，编排全部 QCA 流程 |

### 4.5 第3层：qca_engine/advanced/

| 文件 | 职责 | 关键类/方法 |
|------|------|-----------|
| `robustness.py` | 稳健性检验 | `RobustnessTester` — test_consistency_sensitivity, test_frequency_sensitivity, test_calibration_sensitivity, run_all() |
| `counterfactual.py` | 反事实分析 | `CounterfactualAnalyzer` — analyze() 分类易/难反事实, produce_complex/parsimonious/intermediate_solution() |
| `multi_outcome.py` | 多结果比较 | `MultiOutcomeComparison` — compare() 跨结果 Jaccard 相似度 + 共享/独有条件 |

### 4.6 I/O 层

| 文件 | 职责 | 关键类 |
|------|------|--------|
| `io/readers.py` | 数据读取器 | `DataReader` (ABC), `CSVReader`, `JSONReader`, `ArrayReader`, `SyntheticReader`, **`TextCorpusReader`**（新增——读中文语料 CSV/JSON/TXT） |
| `io/exporters.py` | 数据导出 | `CSVExporter`, `JSONExporter`, `HTMLExporter` |
| `io/sources.py` | 数据源抽象 | `DataSource`, `FileDataSource`, `StdinDataSource`, `GeneratorDataSource` |
| `io/db.py` | 数据库连接 | `SQLiteDataSource`, `SQLiteDataWriter`, PostgreSQL stubs |

### 4.7 可视化层

| 文件 | 职责 | 关键类 |
|------|------|--------|
| `viz/base.py` | 渲染器 ABC | `Renderer` |
| `viz/console.py` | Rich 终端渲染 | `ConsoleRenderer` |
| `viz/matplotlib_renderer.py` | Matplotlib 静态图 | `MatplotlibRenderer` |
| `viz/plotly_renderer.py` | Plotly 交互图 | `PlotlyRenderer` |
| `viz/streamlit_dashboard.py` | Streamlit Web 仪表板 | Streamlit app |
| `viz/qca_plots.py` | **QCA 专用图** | `QCAPlotBuilder` — truth_table_heatmap, necessity_xy_plot, sufficiency_xy_plot, fuzzy_distribution_plot, solution_bar_chart |

### 4.8 报告层

| 文件 | 职责 | 关键类 |
|------|------|--------|
| `report/latex_reporter.py` | 基础 LaTeX 生成 | `LaTeXReporter` — 从 PipelineResult 生成报告（保留自 0.1.0） |
| `report/qca_reporter.py` | **QCA 专用 LaTeX** | `QCALaTeXReporter` — generate() 产出含真值表、解公式、必要性/充分性/稳健性表格的完整 LaTeX 文档 |

### 4.9 CLI（cli.py，完全重写）

9 个子命令，全部通过 Click 实现：

| 命令 | 功能 | 关键参数 |
|------|------|---------|
| `qca calibrate` | 文本 → 模糊集 | --condition-set, --input, --text-column, --output |
| `qca train` | 从标注样本训练校准参数 | --condition-set, --samples, --output |
| `qca analyze` | 完整 QCA 分析 | --condition-set, --fuzzy-data, --consistency, --frequency |
| `qca robustness` | 稳健性检验 | --condition-set, --fuzzy-data, --output |
| `qca counterfactuals` | 反事实分析 | --condition-set, --fuzzy-data, --expectations |
| `qca report` | 生成报告（latex/console） | --results, --format, --output |
| `qca run` | 一键全流程 | --config (完整 YAML 工作流配置) |
| `qca validate` | 验证条件集 YAML | --condition-set |
| `qca list-conditions` | 列出领域预设 | --domain (可选筛选) |

---

## 5. 关键设计决策

### 5.1 为什么用字符 n-gram 而非 jieba？
**约束**：纯 Python + numpy，不额外安装依赖。中文文本用滑动窗口 bigram 分词足以匹配领域关键词（投诉政策类词汇多为 2-4 字）。领域专有词典补偿了缺乏完整分词的不足。

### 5.2 为什么用 Quine-McCluskey？
QCA 文献的标准算法（Ragin, Rihoux, Schneider & Wagemann）。确定性、生成所有质蕴含、5-12 条件的典型 QCA 场景下复杂度可接受。纯 Python 自实现。

### 5.3 为什么保留 Pipeline/Stage/Plugin 抽象？
QCA 工作流天然是管道式的：加载→校准→分析→检验→可视化→报告。现有框架的组合模式、生命周期管理（setup/process/teardown）、Rich 进度条、错误处理、并行执行全部直接映射到 QCA 需求。

### 5.4 模糊集校准的三种方法
- **direct**（直接法）：分段线性，给定 full_in/full_out/crossover 三个阈值
- **indirect**（间接法）：先归一化到 [0,1]，再用 Log-Odds 变换
- **ragin**（Ragin 直接法）：用定性锚点做 Log-Odds 校准

### 5.5 三种 QCA 解
- **复杂解**（complex）：仅最小化经验观察到的配置行
- **精简解**（parsimonious）：包含"易反事实"（与理论期望一致的逻辑余项）作为 don't-care 行
- **中间解**（intermediate）：仅包含有明确方向预期的反事实

---

## 6. 依赖清单

**运行时**（pyproject.toml [project].dependencies）：
numpy>=1.24, pydantic>=2.0, click>=8.0, pyyaml>=6.0, matplotlib>=3.7, plotly>=5.14, rich>=13.0

**开发时**（[project.optional-dependencies].dev）：
pytest>=7.0, pytest-cov>=4.0, black>=23.0, ruff>=0.1, mypy>=1.0, pre-commit>=3.0

**文档**（[project.optional-dependencies].docs）：
mkdocs>=1.5, mkdocstrings[python]>=0.24

**前端**（package.json，独立）：React 18 + TypeScript + Vite 5 + react-router-dom

---

## 7. 测试

| 文件 | 覆盖范围 |
|------|---------|
| `tests/test_pipeline.py` | Stage/Pipeline 生命周期 |
| `tests/test_io.py` | 读取器/导出器/数据源 |
| `tests/test_integration.py` | 端到端流水线 |
| `tests/test_viz.py` | 可视化渲染器 |
| `tests/test_algorithms.py` | 旧算法测试（待更新为 QCA 测试） |
| `tests/test_report.py` | 报告生成 |
| **运行**：`uv run pytest` |
| **QCA 标准验证**：用 Ragin (2008) 教材经典数据集验证分析结果 |

---

## 8. 用户偏好

- 项目文档用中文编写
- 文档优先用本地 MkDocs 构建验证，无需推送 GitHub Pages
- CLI 默认用 Rich 美化输出
- 所有 Python 文件显式指定 `encoding='utf-8'`

---

## 9. Do-Not-Repeat

- [2026-05-24] pyproject.toml 的 `long_description_content_type` 字段不被 setuptools 支持，已删除
- [2026-05-24] CLI 中 `click.Choice([d.value for d in [...strings...]])` 会报 AttributeError（字符串无 .value），应直接用字符串列表
- [2026-05-24] `_print_fit_metrics` 函数需要在模块级别定义（不能嵌套在 train 函数内）
- [2026-05-24] rf-string 中的 `\begin{center}` 被解析为 Python 表达式 `{center}`，造成 F821 错误；应用字符串拼接替代
- [2026-05-24] Ruff RUF001 对中文标点（，。！？等）报 ambiguous 是预期行为，在 keyword_dict.py 中已通过 per-file-ignore 抑制
- [2026-05-24] **pre-commit 版本不匹配陷阱**：本地 `uv run ruff` 和 pre-commit hook 的 ruff 版本必须一致。当 per-file-ignore 引用新规则（如 RUF043）但 hook 用旧版本时会报 "Unknown rule selector"。解决方案：升级 `.pre-commit-config.yaml` 中 ruff 的 `rev` 对齐 `uv.lock` 版本。
- [2026-05-24] **PD901 规则已在 ruff 0.15.x 移除**：如果 pyproject.toml 中全局 ignore 了 PD901，升级 ruff 后会报 "rules have been removed" 警告。应及时从 ignore 列表中删除已废弃的规则。
- [2026-05-24] **Windows Python GBK 陷阱也影响 buglog.json**：`python -c "import json; ..."` 默认用 GBK 读文件，会导致 UnicodeDecodeError。必须始终用 `open(path, encoding='utf-8')`。
- [2026-05-24] **npm ci 失败会掩盖后续 TypeScript 错误**：CI 在 npm ci 步骤失败即退出，tsc -b 从未执行。修复 lock file 后才能看到真正的 TS 编译错误。应该在推送前跑 `npm run build` 本地验证。
- [2026-05-24] **package-lock.json 与 package.json 不同步陷阱**：手动改 package.json 后没跑 `npm install`，且直接提交了旧的 lock file。lock file 中版本超出 semver 范围时 npm ci 会拒绝安装。修改依赖后必须跑 npm install 刷新 lock file。
- [2026-05-24] **plotly.js-dist-min v2.x 无 TypeScript 类型声明**：v2.35.x 不内置 .d.ts（v3.x 才有）。需在 vite-env.d.ts 中加 `declare module 'plotly.js-dist-min';`。
- [2026-05-24] **Pyodide 中严禁用 JS 模板字面量往 Python 代码注入数据**：`pyodide.runPython(\`x = ''''${json}\n''')` 的模式是代码注入漏洞。攻击者输入 `'''` 即可逃逸出 Python 字符串执行任意代码。安全方式：先用 `pyodide.FS.writeFile('/tmp/xxx.json', jsonStr)` 写入 VFS，再在 Python 中 `json.load(open('/tmp/xxx.json'))` 读取。
- [2026-05-24] **Pyodide mountFromInline 必须写 __init__.py**：仅创建目录（os.makedirs）不能让 Python 识别为包。必须在每个包目录写入 `__init__.py` 文件。遗漏会导致 `ModuleNotFoundError`。
- [2026-05-24] **PipelineStage 类型交叉验证**：每次添加新的 PipelineStage 值时，必须同时确认所有 dispatch 调用使用了该值（而非写死的字符串），否则 TypeScript 编译通过但运行时语义错误（如 'running-robustness' 被用于 counterfactuals）。
- [2026-05-24] **pre-commit stash-conflict 无限循环**：git commit 时如果存在未暂存的修改（unstaged changes），pre-commit hooks（ruff-format、end-of-file-fixer）自动格式化后，unstash 会因冲突而回滚修复，导致 commit 反复失败。解决方案：(1) 已添加 PreToolUse hook（`.wolf/hooks/pre-commit.js`），在每次 git commit 前自动执行 `ruff format . && ruff check --fix . && git add -u`；(2) 如手动提交，先确保 `git add -u` 后再 commit。
- [2026-05-24] **counterfactual.py produce_parsimonious_solution 算法错误**（见 FIXME-1）：精简解应包含全部逻辑余项作为 don't-care 行，当前仅添加 easy counterfactuals，行为与 intermediate solution 完全相同。修复时需同步扩展 QM 以支持 don't-care minterm。【已修复：2026-05-24 — produce_parsimonious_solution 现在所有 remainder 作为 dont_care_minterms 传入，不通过 _classify_counterfactual 过滤；QM.minimize() 新增 dont_care_minterms 参数，don't-care 参与合并但不进入覆盖表；同时修复 FIXME-17 (counterfactual.py:140 dead code)、FIXME-18 (minimization.py:43-44 dead code)、HACK-5 (QM don't-care 支持)】
- [2026-05-24] **calibrate_ragin 实现的是分段线性而非 log-odds**（见 FIXME-3）：docstring 声称 Ragin log-odds 直接法但实际是分段线性插值。应用 logistic 公式 `exp(dev)/(1+exp(dev))` 重写。【已修复：2026-05-24 — 用 np.where/np.exp/logistic formula 重写 calibrate_ragin()；添加 deviation clipping ([-700, 700]) 防 exp overflow；floor/ceiling 通过 np.clip(result, 0.05, 0.95) 实现】
- [2026-05-24] **calibrator.py 混合 scoring_source 列索引偏移**（见 FIXME-2）：KEYWORD/HYBRID/PROTOTYPE 混合时，`col_idx` 直接索引 `match_corpus()` 返回矩阵导致列错位。需建立 col_idx→kw_col_idx 映射。【已修复：2026-05-24 — 新增 _precompute_kw_context() 构建映射；_compute_raw_scores() 接受可选 kw_matrix+col_to_kw 参数；同时修复 FIXME-4 match_corpus 缓存】
- [2026-05-24] **match_corpus() 每个条件重复调用**（见 FIXME-4）：O(n_conditions × n_texts × n_keywords) 冗余。在 process() 开头缓存一次。【已修复：2026-05-24 — _precompute_kw_context() 调用 match_corpus() 一次并缓存；process/process_with_outcome/calibrate_one 全部复用；同时修复 FIXME-20 通过提取 _process_core() 消除 process/process_with_outcome 间 ~60 行重复代码】
- [2026-05-24] **pipeline Stage 失败后静默传递损坏数据**（见 FIXME-5）：Stage 失败后 Pipeline 传递上一次正常数据给下游。【已修复：2026-05-24 — 添加 fail_fast: bool = True 到 Pipeline/ParallelPipeline；添加 data_quality 字段到 StageResult（valid/stale/None）；添加 failed_stages 属性和 fail_fast 字段到 PipelineResult。fail_fast=True 时 set PipelineStatus.FAILED + break。Pipeline.process() 在 fail_fast=True 时 re-raise。更新 3 个测试适配新默认行为。】
- [2026-05-24] **robustness coverage_stability 始终为 0**（见 FIXME-6）：`hasattr(tt, "solution_coverage")` 始终 False（TruthTable 无此字段）。应 run minimization+sufficiency 计算真实 coverage。【已修复：2026-05-24 — 添加 _compute_solution_coverage() 通过 term membership AND + union + ConsistencyCalculator 计算真实 fuzzy-set 解覆盖度；test_consistency_sensitivity 和 test_frequency_sensitivity 均使用此方法；同时一并修复了 FIXME-7 (成员扰动重命名+outcome排除)、FIXME-8 (bootstrap 重抽样)、FIXME-12 (频率阈值自适应小N)】
- [2026-05-24] **robustness test_calibration_sensitivity 实际是 membership perturbation**（见 FIXME-7）：方法对所有 membership 列（含 outcome）施加 uniform additive 扰动，混入了 outcome sensitivity。【已修复：2026-05-24 — 重命名为 test_membership_perturbation，仅扰动 condition 列 (perturbed[:, :-1]) 排除 outcome；保留 test_calibration_sensitivity 向后兼容别名；run_all 调用新名称】
- [2026-05-24] **robustness 缺失 bootstrap 重抽样**（见 FIXME-8）：docstring 提到但无实现。【已修复：2026-05-24 — 添加 test_bootstrap(n_iterations=100, sample_fraction=1.0)：case replacement resampling，truth table + minimization per sample，Jaccard similarity + term appearance proportion 报告】
- [2026-05-24] **robustness 默认频率阈值对小 N 不合理**（见 FIXME-12）：默认 [1.0, 2.0, 3.0, 5.0] 对 N<10 可能排除所有行。【已修复：2026-05-24 — N<20 使用比例阈值 [0.05*N, 0.10*N, 0.15*N, 0.25*N]；N>=20 使用绝对阈值 [1.0, 2.0, 3.0, 5.0]】
- [2026-05-24] **qca_reporter.py LaTeX 特殊字符未转义**（见 FIXME-10）：`*` `~` `_` 等字符直接插入 LaTeX 导致编译失败。需添加转义函数。【已修复：2026-05-24 — 添加 _escape_latex()（转义 %$#&{}_ 为带反斜杠形式，~→\\textasciitilde{}）和 _escape_latex_formula()（~*+ → \\neg \\land \\lor 用于数学模式）。所有用户文本（outcome_name, config_label, condition_name, term label, test_name, parameter_varied, summary, formula）均应用转义】
- [2026-05-24] **qca_reporter.py _robustness_section 空列表 IndexError**（见 FIXME-11）：`t.solution_stability[0]` 和 `t.solution_stability[-1]` 在列表为空时直接崩溃。【已修复：2026-05-24 — 添加 if t.solution_stability: 守卫，空列表时 stability_range = "N/A"】
- [2026-05-24] **minimization.py hash-based identity 不可靠**（见 FIXME-21）：`hash((imp1, tuple(cov1)))` 存在理论碰撞风险和 PYTHONHASHSEED 跨进程不稳定。【已修复：2026-05-24 — 用 itertools.count() 顺序 ID 计数器替换 hash()；每个 implicant 创建时分配唯一 ID → 数据结构从 (pattern, coverage) 改为 (id, pattern, coverage)；combined_this_round 和 used_in_combination 跟踪 int ID 而非 hash 值】
- [2026-05-24] **QM 无 k<=12 上限守卫导致浏览器 WASM 卡死**（见 P0-1）：minimize() 无条件数上限检查，k>12 时 2^k 指数爆炸阻塞单线程 WASM。【已修复：2026-05-24 — minimize() 入口添加 n_vars = len(minterms[0]) > 12 检查，超限抛出 ValueError("Quine-McCluskey does not support more than 12 conditions...")】

- [2026-05-24] **counterfactual.py theoretical_expectation 始终为 None**（见 FIXME-9）：`theo_exp` 初始化为 None 后从未赋值，所有行的 `CounterfactualClassification.theoretical_expectation` 始终为 None。修复方式：在 `analyze()` 循环中从 `directional_expectations` 构建 `theo_exp` 字符串，格式为 "+name1, -name2"（分别代表预期 present/absent）。【已修复：2026-05-24】
- [2026-05-24] **sufficiency.py 条件名不匹配时静默跳过**（见 FIXME-13）：`_compute_term_membership` 中 condition name 不匹配时 silent pass（视为 1.0），隐藏 term label 与 condition_matrix 列名不匹配的 bug。修复方式：添加 `warnings.warn()` 分别在否定和非否定分支输出 warning，使用 `stacklevel=2` 指向调用方。【已修复：2026-05-24】

---


## 10. 决策日志

- [2026-05-24] **三方角色审查完成**：派 3 个 subagent 分别扮演技术顾问（架构优化）、客户代表（需求提出）、评审者（代码评估），对项目进行深度审查。产出 TODO.md（51项）、FIXME.md（22项）、HACK.md（12项）。发现 5 个严重算法 Bug（parsimonious 算法错误、calibrate_ragin 实现错误、列索引偏移、match_corpus 重复调用、管道静默数据损坏）。由 reviewer subagent 验收通过。下一 session 按 P0 优先级开始修复。
- [2026-05-24] **新增原型匹配校准模式**：用户可通过"condition, 原型文本, 隶属(0/1)"格式提供概念原型，用 bigram Jaccard 相似度计算文本与正/负例原型的匹配度，最终得分 = max(pos_sims) - max(neg_sims)。前端新增模式选择器（关键词/原型），原型模式用表格编辑器+结构化 CSV 输入（编号,文本,结果）。结果列直接作为 crisp-set membership。所有新字段有默认值，keyword 模式完全向后兼容。
- [2026-05-24] 将 experiment-engine 从通用"算法实验框架"重构为领域特定的 QCA 文本分析系统。这是该框架的**全部功能**（非附加模块）。
- [2026-05-24] 删除了 `algorithms/linear_regression.py` 和 `algorithms/kmeans.py`——与 QCA 无关
- [2026-05-24] CLI 入口点从 `experiment-engine` 更名为 `qca`
- [2026-05-24] 全局忽略 ruff E501（行长度）——中文关键词和 LaTeX 字符串自然较长
- [2026-05-24] 全局忽略 PD901（df 变量名）——pandas 生态中 `df` 是通用惯例，ruff 0.15.x 已将该规则移除
- [2026-05-24] **采用 Pyodide 浏览器端运行方案**：将 QCA Python 引擎通过 Pyodide 编译为 WebAssembly 在浏览器中运行，零后端服务器。React + Vite + TypeScript 前端，GitHub Pages 部署。
- [2026-05-24] **Pyodide CDN 策略**：Pyodide 核心 50MB 从 jsDelivr CDN 加载（利用全球缓存），仅 ~80KB Python 源模块自托管。避免 GitHub Pages 1GB 软限制。
- [2026-05-24] **单仓库 gh-pages 部署**：选择 Option B（同一 repo 的 gh-pages 分支），避免跨仓库 PAT 复杂度。URL: `qhWangAntoneva.github.io/experiment-engine/`
- [2026-05-24] **pydantic v2 → dataclass 双后端方案**：pydantic-core 为 Rust 二进制无法在 Pyodide 运行。采用 `IN_BROWSER` 门控选择模型后端：CLI 保持 Pydantic v2，浏览器使用 dataclass shim (models_browser.py)。
- [2026-05-24] **Plotly.js 替代 matplotlib**：浏览器端仅用 Plotly（纯 Python + HTML/JS 输出），matplotlib Agg 后端仅用于 PNG 导出。Plotly.js 惰性加载节省首屏体积。
- [2026-05-24] **修复 FIXME-1/HACK-5/FIXME-17/FIXME-18**：重写 `produce_parsimonious_solution` 使其包含所有逻辑余项为 don't-care（不经过 `_classify_counterfactual` 过滤），对齐 Ragin 2008。扩展 `QuineMcCluskey.minimize()` 新增 `dont_care_minterms` 参数：don't-care 参与质蕴含生成（帮助合并）但不进入覆盖表（idx >= n_reg 的行不建列）。同时修复 `produce_intermediate_solution` 使其 easy counterfactuals 也经由 don't-care 传入（不再作为 outcome=1 行）。清理 FIXME-17（counterfactual.py:140 死代码）和 FIXME-18（minimization.py:43-44 死代码）。HACK-5 已解决。
- [2026-05-24] **修复 FIXME-2/3/4/20（calibrator.py 四个 Bug）**：
  - **FIXME-3 (calibrate_ragin)**：重写为 logistic 公式 `exp(dev)/(1+exp(dev))`，deviation 为 `(raw-cross)*scale`，添加 np.clip(deviation, -700, 700) 防 overflow
  - **FIXME-2 (列索引偏移)**：新增 `_precompute_kw_context()` 构建 col_idx→kw_col_idx 映射，`_compute_raw_scores()` 接受可选 kw_matrix+col_to_kw 参数
  - **FIXME-4 (重复 match_corpus)**：`_precompute_kw_context()` 缓存一次 match_corpus 结果，process/process_with_outcome/calibrate_one 全部复用
  - **FIXME-20 (代码重复)**：提取 `_process_core(texts, kw_matrix, col_to_kw, outcome_provider)` 消除 process/process_with_outcome 间 ~60 行重复，outcome_provider 回调分离 outcome 列赋值逻辑。calibrate_one 也使用 `_precompute_kw_context`
  - 所有 360 测试通过，ruff 干净
- [2026-05-24] **修复 FIXME-9 (counterfactual.py theoretical_expectation 始终为 None)**：在 `analyze()` 循环中新增代码，从 `directional_expectations` 构建 `theo_exp` 字符串，格式为 "+name" 或 "-name"（用 ', ' 连接多条期望）。若无方向性期望则保持 None。所有 353 测试通过，ruff 干净。
- [2026-05-24] **修复 FIXME-13 (sufficiency.py 条件名不匹配时静默跳过)**：在 `_compute_term_membership` 的两处 silent pass（否定/非否定分支）添加 `warnings.warn()` 调用，使用 `stacklevel=2` 指向调用方。导入 `warnings` 模块。所有 353 测试通过，ruff 干净。
- [2026-05-24] **修复 FIXME-6/7/8/12（robustness.py 四个 Bug）**：
  - **FIXME-6 (coverage_stability 始终 0)**：添加 `_compute_solution_coverage()` helper，通过 fuzzy AND term membership + union + `ConsistencyCalculator.solution_coverage` 计算真实 fuzzy-set 解覆盖度。新增 module-level `_compute_term_membership()` helper（复用 sufficiency.py 逻辑但避免 SLF001）。test_consistency_sensitivity 和 test_frequency_sensitivity 均使用此方法。
  - **FIXME-7 (calibration sensitivity 实际是 membership perturbation)**：重命名为 `test_membership_perturbation`；仅扰动 condition 列 (`perturbed[:, :-1]`) 排除 outcome；保留 `test_calibration_sensitivity` 为向后兼容别名（返回新 RobustnessTestResult）；`run_all` 调用新名称。
  - **FIXME-8 (缺失 bootstrap)**：添加 `test_bootstrap(n_iterations=100, sample_fraction=1.0)`：`np.random.choice` case resampling with replacement，truth table + QM minimization per sample，Jaccard similarity + term appearance proportion；`coverage_stability` 存储各 baseline term 出现在 bootstrap 样本中的平均比例。
  - **FIXME-12 (频率阈值小N不合理)**：N<20 使用比例阈值 `[0.05*N, 0.10*N, 0.15*N, 0.25*N]`（round 2dp）；N>=20 使用绝对阈值 `[1.0, 2.0, 3.0, 5.0]`。
  - 所有 361 测试通过，ruff 干净，integration test 验证全部四项修复。
- [2026-05-24] **修复 P0-1/FIXME-10/FIXME-11/FIXME-21（跨文件四个 Bug 批量修复）**：
  - **P0-1 (QM k<=12 guard)**：minimize() 入口添加 n_vars = len(minterms[0]) > 12 检查，超限抛 ValueError
  - **FIXME-10 (LaTeX escaping)**：添加 _escape_latex() 转义 %$#&{}_ → 反斜杠形式、~ → \\textasciitilde{}；添加 _escape_latex_formula() 转换 ~*+ → \\neg \\land \\lor 用于数学模式；在所有用户文本进入 LaTeX 前应用转义
  - **FIXME-11 (empty solution_stability IndexError)**：添加 if t.solution_stability: 守卫，空列表时 stability_range = "N/A"
  - **FIXME-21 (hash→ID identity)**：用 itertools.count() 顺序 ID 替换 hash()；implicant_map/next_map 数据结构从 (pattern, coverage) 改为 (id, pattern, coverage)；combined_this_round 和 used_in_combination 跟踪 int ID
  - 所有 361 测试通过，ruff 干净，额外函数测试验证 QM guard + LaTeX escaping 正确性
- [2026-05-24] **Do-Not-Repeat: @staticmethod 中调用另一个 @staticmethod 需用 ClassName.method()**：在 static method 中不能用 self.method()（因为 static method 没有 self 参数）。需使用 ClassName.method()。如果在静态方法中误用 self. 会导致 NameError。
