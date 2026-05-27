# QCA Text Analysis Tool

> **公民反馈文本 → 模糊集 QCA 分析**

将中文民众反馈文本通过 BERT 语义嵌入 + 余弦相似度评分，转化为模糊集 QCA（定性比较分析）结果。支持 CLI 命令行和 React 浏览器端两种使用方式。

## 目录

- [功能概述](#功能概述)
- [安装](#安装)
- [演示数据](#演示数据)
- [CLI 使用](#cli-使用)
- [API 使用](#api-使用)
- [前端应用（浏览器端）](#前端应用浏览器端)
- [条件集配置](#条件集配置)
- [项目结构](#项目结构)
- [开发](#开发)
- [许可证](#许可证)

---

## 功能概述

### 5 个预设分析领域

| 领域 | 条件数 | 说明 |
|------|--------|------|
| `dissatisfaction`（不满） | 5 条件 + 1 结果 | 负面情绪、服务失败、紧急性、对比投诉、升级威胁 |
| `policy_demand`（政策诉求） | 5 条件 + 1 结果 | 具体政策建议、资源请求、群体代表、证据引用、可行性论证 |
| `co_production`（合作生产） | 4 条件 + 1 结果 | 参与意愿、资源贡献、知识共享、集体行动 |
| `trust`（信任） | 5 条件 + 1 结果 | 制度信任、能力感知、善意感知、诚信感知、积极体验分享 |
| `gov_responsiveness`（政府回应） | 5 条件 + 1 结果 | 响应及时性、解决有效性、过程透明度、互动质量、后续机制 |

### 评分方法

- **BERT CLS 嵌入 + 余弦相似度**（唯一的评分引擎）
- 原型文本（prototype）代表理论上的条件隶属/不隶属理想
- Cosine similarity + Softmax(τ=5.0) 将语义相似度转化为原始分数

### 校准方法

| 方法 | 描述 |
|------|------|
| **Direct**（直接校准） | 分段线性模糊隶属度，min-max 归一化 + 阈值插值 |
| **Indirect**（间接校准） | Log-odds 对数几率转换，以交叉点为中心的 Logistic 函数 |
| **Ragin**（Ragin 模糊直接法） | 三个定性锚点（fully out=0.05, crossover=0.50, fully in=0.95），Logistic 变换 |

### QCA 分析

- **真值表**：基于一致性和频率阈值的逻辑配置
- **布尔最小化**：Quine-McCluskey 算法（确定性，生成所有质蕴含项）
- **三种解**：复杂解（Complex）、简约解（Parsimonious）、中间解（Intermediate）
- **必要性分析**：单个条件的一致性和覆盖度
- **充分性分析**：条件组合的一致性和覆盖度
- **鲁棒性测试**：参数敏感性分析
- **反事实分析**：逻辑余项的简单/困难反事实分类

---

## 安装

### 后端 CLI

```bash
# 使用 uv（推荐）
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

要求：Python >= 3.10

### 前端浏览器

```bash
npm install
npm run dev      # 开发模式
npm run build    # 生产构建
```

---

## 演示数据

项目自带 **30 条标注入样数据**，覆盖全部 5 个领域，每条包含正反案例。

**文件位置**：`tests/fixtures/sample_cases.csv`

```csv
text_id,domain,text,expected_outcome
1,dissatisfaction,"你们这服务太差了，去办证跑了五趟都没办成，窗口人员推诿踢皮球，我要打市长热线投诉你们",1
7,policy_demand,"建议政府尽快出台针对老旧小区加装电梯的补贴政策，我们全体居民强烈要求",1
13,co_production,"我们社区居民愿意出钱出力，一起把垃圾分类这个事情做好，希望政府能组织协调",1
19,trust,"我对政府很放心，相信他们能公正处理好这件事，现在办事确实越来越透明了",1
25,gov_responsiveness,"反映问题后当天就有人联系我，三天内就办好了，效率非常高，处理很到位",1
4,dissatisfaction,"今天去办了业务，工作人员态度还可以，虽然等了一会儿但总算办完了",0
10,policy_demand,"我想咨询一下现在执行的购房补贴政策具体是什么条件",0
16,co_production,"这是政府的事，我们老百姓管不了那么多，你们自己想办法处理",0
22,trust,"政府没什么公信力，说要解决问题说了半年了也没见动静，完全不靠谱",0
28,gov_responsiveness,"反映了好几次问题，等了两个星期也没人回复，石沉大海一样",0
```

**条件集配置**（每领域一个）：`tests/fixtures/condset_*.yaml`

```yaml
# tests/fixtures/condset_dissatisfaction.yaml (片段)
conditions:
  - name: strong_negative_affect
    prototypes:
      - prototype_text: "你们这服务太差了，态度恶劣，办事效率极低，我非常愤怒要投诉你们"
        is_member: 1
        weight: 1.0
      - prototype_text: "请帮我查一下这个申请什么时候能办好，谢谢"
        is_member: 0
        weight: 1.0
    calibration_params:
      threshold_full_in: 0.8
      threshold_full_out: 0.2
      crossover_point: 0.5
      direction: ascending
outcome:
  name: high_dissatisfaction
  prototypes:
    - prototype_text: "你们的服务太差了，严重不作为，我对你们彻底失望"
      is_member: 1
      weight: 1.0
```

---

## CLI 使用

安装后通过 `qca` 命令使用（9 个子命令）：

### `calibrate` — 文本校准

将原始文本校准为模糊集隶属度分数：

```bash
qca calibrate -c tests/fixtures/condset_dissatisfaction.yaml \
              -i tests/fixtures/sample_cases.csv \
              -o fuzzy_data.npz \
              --variant fsqca
```

输出：
```
✓ Loaded condition set: dissatisfaction_default
✓ Calibrated: 6 cases x 6 sets
✓ Saved to fuzzy_data.npz
```

### `analyze` — QCA 分析

运行完整 QCA 分析：真值表 → 最小化 → 必要性 → 充分性：

```bash
qca analyze -c tests/fixtures/condset_dissatisfaction.yaml \
            -f fuzzy_data.npz \
            --consistency 0.75 \
            --frequency 1.0 \
            -o qca_results.json
```

输出示例：
```
  Truth table: 3/4 rows included
  Positive configurations: 2
  Complex solution: strong_negative_affect*srvc_failure + urgency ~comparative
    Consistency=0.833  Coverage=0.714
  Necessary conditions: strong_negative_affect
```

### `train` — 训练校准参数

从标注样本中拟合校准参数：

```bash
qca train -c tests/fixtures/condset_dissatisfaction.yaml \
          -s training_samples.csv \
          -o conditions_fitted.yaml
```

### `robustness` — 鲁棒性测试

对 QCA 结果进行参数敏感性分析：

```bash
qca robustness -c tests/fixtures/condset_dissatisfaction.yaml \
               -f fuzzy_data.npz \
               -o robustness_report.json
```

输出：
```
Overall robustness: 0.82
```

### `counterfactuals` — 反事实分析

生成复杂/简约/中间三种解：

```bash
qca counterfactuals -c tests/fixtures/condset_dissatisfaction.yaml \
                    -f fuzzy_data.npz \
                    -o .
```

输出：
```
Easy counterfactuals: 1
Hard counterfactuals: 2
Logical remainders: 3
Complex solution: 4 terms
Parsimonious solution: 2 terms
Intermediate solution: 3 terms
```

### `report` — 生成分析报告

支持 LaTeX、控制台、DOCX 三种格式：

```bash
qca report -r qca_results.json -f latex -o report/
qca report -r qca_results.json -f console
qca report -r qca_results.json -f docx -o report/
```

### `run` — 全流程运行

一键完成校准 → 分析 → 鲁棒性 → 报告全流程：

```bash
qca run -c workflow_config.yaml -o qca_output/
```

`workflow_config.yaml` 示例：

```yaml
input:
  path: tests/fixtures/sample_cases.csv
  text_column: text
conditions:
  definition_file: tests/fixtures/condset_dissatisfaction.yaml
qca:
  consistency_threshold: 0.75
  frequency_threshold: 1.0
```

### `validate` — 验证条件集

检查条件集 YAML 文件格式是否正确：

```bash
qca validate -c tests/fixtures/condset_dissatisfaction.yaml
```

输出：
```
✓ Valid condition set: dissatisfaction_default
  Domain: dissatisfaction
  Conditions: 5
  Condition names: strong_negative_affect, service_failure_mention, ...
  Outcome: high_dissatisfaction
```

### `list-conditions` — 列出领域预设

查看所有预设领域及其原型条件：

```bash
qca list-conditions
qca list-conditions --domain dissatisfaction
```

输出：
```
DISSATISFACTION
  strong_negative_affect: 2 prototypes (1+/1-)
  service_failure_mention: 2 prototypes (1+/1-)
  urgency_expression: 2 prototypes (1+/1-)
  comparative_complaint: 2 prototypes (1+/1-)
  escalation_threat: 2 prototypes (1+/1-)
  high_dissatisfaction (outcome): 2 prototypes (1+/1-)
```

---

## API 使用

Python 程序化调用：

```python
from experiment_engine.api import (
    run_calibrate,
    run_analyze,
    run_robustness,
    run_counterfactuals,
    run_report,
)

# 1. 校准
fuzzy = run_calibrate(
    condition_set_path="tests/fixtures/condset_dissatisfaction.yaml",
    data_path="tests/fixtures/sample_cases.csv",
    variant="fsqca",
)
print(f"Calibrated: {fuzzy.n_cases} cases x {fuzzy.n_conditions + 1} sets")

# 2. 分析
result = run_analyze(
    condition_set_path="tests/fixtures/condset_dissatisfaction.yaml",
    fuzzy_data_path="fuzzy_data.npz",
    variant="fsqca",
    consistency_threshold=0.75,
    frequency_threshold=1.0,
)

# 查看结果
print(f"Truth table: {len(result.truth_table.rows)} rows")
if result.solutions.complex:
    print(f"Complex solution: {result.solutions.complex.formula}")
    print(f"  Consistency: {result.solutions.complex.solution_consistency:.3f}")
    print(f"  Coverage: {result.solutions.complex.solution_coverage:.3f}")
```

---

## 前端应用（浏览器端）

前端是 React 18 + TypeScript + Vite 5 应用，通过 **Pyodide**（浏览器中的 Python）将 Python 分析引擎嵌入浏览器。

### 启动

```bash
npm install
npm run dev
```

### 页面

| 路由 | 功能 |
|------|------|
| `/` | Dashboard — 项目概览和快速入口 |
| `/data-input` | DataInput — 上传数据、编辑条件集 YAML、配置校准参数 |
| `/results` | Results — 查看真值表、解决方案、必要性/充分性分析 |
| `/compare` | Compare — 对比多次分析结果 |
| `/settings` | Settings — 应用设置 |

### 技术栈

- **UI**：React 18 + React Router 6
- **构建**：Vite 5 + TypeScript 5
- **分词嵌入**：Transformers.js（Xenova，浏览器端 BERT）
- **Python 运行时**：Pyodide 0.26.4（浏览器内运行 Python 引擎）
- **可视化**：Plotly.js（交互式图表）+ Matplotlib（Python 静态图表）

---

## 项目结构

```
qca-analysis-tool/
├── src/
│   ├── experiment_engine/          # Python 后端
│   │   ├── api.py                  # 5 个公共 API 函数
│   │   ├── cli.py                  # 9 个 CLI 子命令
│   │   ├── pipeline.py             # Pipeline 编排框架
│   │   ├── config.py               # YAML/JSON 配置加载
│   │   ├── plugins.py              # 插件注册表（Singleton）
│   │   ├── pyodide_handlers.py     # Pyodide Worker 处理器
│   │   ├── models/
│   │   │   └── qca.py              # 领域模型（MembershipData, QCAAnalysisResult等）
│   │   ├── text_calibration/       # 文本校准模块
│   │   │   ├── cosine_similarity.py  # BERT CLS + 余弦相似度
│   │   │   ├── calibrator.py        # 3 种校准方法
│   │   │   ├── domains.py           # 5 个领域预设
│   │   │   ├── strategies.py        # 策略模式校准器
│   │   │   └── training.py          # 校准参数训练
│   │   ├── qca_engine/             # QCA 分析引擎
│   │   │   ├── truth_table.py      # 真值表构建
│   │   │   ├── minimization.py     # Quine-McCluskey 最小化
│   │   │   ├── solution.py         # 三种解生成
│   │   │   ├── necessity.py        # 必要性分析
│   │   │   ├── sufficiency.py      # 充分性分析
│   │   │   └── advanced/           # 鲁棒性、反事实、多结果
│   │   ├── report/                 # LaTeX/DOCX 报告生成
│   │   ├── viz/                    # Matplotlib/Plotly 可视化
│   │   └── io/                     # 数据读取/导出（CSV/JSON/XLSX/SQLite）
│   ├── pages/                      # React 页面
│   │   ├── Dashboard.tsx
│   │   ├── DataInput.tsx
│   │   ├── Results.tsx
│   │   ├── Compare.tsx
│   │   └── Settings.tsx
│   ├── components/                 # React 组件
│   ├── services/                   # 前端服务层
│   │   ├── pyodide.worker.ts       # Web Worker（运行 Python）
│   │   ├── pyodide.ts              # Worker 桥接
│   │   ├── bert-engine.ts          # BERT 引擎封装
│   │   └── bert-cache.ts           # BERT 嵌入缓存
│   └── store/
│       └── QCAPipelineContext.tsx   # 状态管理
├── tests/
│   └── fixtures/                    # 测试数据（含 30 条标注样本）
├── examples/                        # 示例脚本
└── configs/                         # 配置示例
```

---

## 开发

```bash
# 安装 dev 依赖
uv pip install -e ".[dev]"

# 运行测试（532 个测试用例）
pytest

# 类型检查
mypy src/

# 代码风格检查
ruff check src/

# 前端构建校验
npm run build
```

---

## 许可证

MIT
