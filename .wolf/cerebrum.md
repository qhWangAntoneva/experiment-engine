# Cerebrum — QCA Text Analysis Tool

> OpenWolf 学习记忆。最后一次全面更新：2026-05-24
> 用途：新 agent 接手时的项目全貌参考。

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

---

## 10. 决策日志

- [2026-05-24] 将 experiment-engine 从通用"算法实验框架"重构为领域特定的 QCA 文本分析系统。这是该框架的**全部功能**（非附加模块）。
- [2026-05-24] 删除了 `algorithms/linear_regression.py` 和 `algorithms/kmeans.py`——与 QCA 无关
- [2026-05-24] CLI 入口点从 `experiment-engine` 更名为 `qca`
- [2026-05-24] 全局忽略 ruff E501（行长度）——中文关键词和 LaTeX 字符串自然较长
