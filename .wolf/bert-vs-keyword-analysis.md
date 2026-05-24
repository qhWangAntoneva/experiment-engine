# BERT-Base 语义核心 vs 关键词匹配：QCA 文本校准架构分析

> 日期：2026-05-24（初稿）→ 2026-05-25（最终决议）
> 分析者：技术顾问 + 评审者 + 算法顾问 三方综合
> 状态：**已定案**
> 结论：**BERT 作为辅助工具（不做主引擎）。关键词匹配是 QCA 方法论核心，不可替代。BERT 仅用于差异标记、覆盖率诊断、候选关键词推荐。从 MiniLM-L6（~25MB）轻量模型开始，仅在 WebGPU 可用且模型缓存命中时启用。**

---

## 0. 执行摘要

**一句话结论：BERT-Base 不能完全替代关键词匹配功能。关键词匹配是 QCA 方法论中"理论操作化"的载体——每个关键词都是一次有意的理论选择。BERT 可以且应该作为补充（语义覆盖率、词典辅助构建、歧义消解），但关键词/词典匹配是 QCA 方法的核心，移除它意味着移除分析的理论基础。**

推荐的架构路径：
1. **短期（P1）**：保留关键词为主，新增 BERT 相似度作为"语义验证"通道（双通道并行，标记高差异文本供研究者审查）
2. **中期（P2）**：实现条件粒度 scoring 来源选择（keyword / bert / hybrid），用户可选择每个条件的匹配方式
3. **长期（P3）**：BERT 成为默认辅助引擎（非替代），为关键词词典提供"候选关键词推荐"和"覆盖率报告"

---

## 1. 当前关键词匹配引擎架构

### 1.1 数据流

```
用户上传中文文本 (CSV/JSON/TXT)
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  keyword_dict.py: ChineseKeywordDictionary           │
│  - match_corpus(texts) → (n_texts, n_conditions)     │
│  - 每个条件: 40+ 关键词，每个词含 pattern + weight     │
│  - 匹配粒度: bigram 字符 n-gram（滑窗，无 jieba 依赖）  │
│  - 复杂度: O(n_texts × n_conditions × n_keywords)     │
│  - 关键词权重求和 = raw score                          │
└──────────────────────┬───────────────────────────────┘
                       │ raw scores (float ndarray)
                       ▼
┌──────────────────────────────────────────────────────┐
│  calibrator.py: TextCalibrationStage                 │
│  - _compute_raw_scores(): 根据 ScoringSource 分发     │
│    * KEYWORD → kw_matrix[:, col]                      │
│    * PROTOTYPE → PrototypeSimilarityEngine (Jaccard)  │
│    * HYBRID → w1*kw + w2*proto                        │
│  - _apply_calibration(): 策略模式 → 3种校准方法        │
│    * direct: 分段线性 (full_in/out/crossover)          │
│    * indirect: Log-Odds logistic                      │
│    * ragin: Ragin 直接法 (logit formula)               │
│  - 输出: FuzzySetData (membership ∈ [0,1])            │
└──────────────────────┬───────────────────────────────┘
                       │ membership matrix
                       ▼
               QCA 分析管道 (truth table → QM → 解)
```

### 1.2 5 个预置领域

| 领域 | 条件数 | 关键词数 | 典型关键词 |
|------|--------|---------|-----------|
| dissatisfaction | 6 (5 causal + 1 outcome) | 53 | 投诉, 不满, 推诿, 愤怒, 不作为 |
| policy_demand | 6 | 31 | 建议, 应当出台, 补贴, 呼吁 |
| co_production | 5 | 22 | 我愿意, 积极参加, 共同, 共建 |
| trust | 6 | 25 | 相信政府, 公信力, 廉洁, 感谢 |
| gov_responsiveness | 6 | 29 | 及时, 解决了, 落实到位, 回访 |

合计：29 条件 × ~200 关键词

### 1.3 关键词匹配的核心优势

1. **完全可解释**：每条文本可精确展示"命中了哪些关键词，每个贡献了多少权重"
2. **理论操作化**：关键词词典本身就是理论——"不满"由 `投诉(0.6) + 失望(0.7) + 糟糕(0.7) + ...` 构成是研究者的有意理论选择
3. **极低计算成本**：纯 CPU、单线程、O(n*m) 复杂度，无需 GPU，WASM 友好
4. **确定性**：相同输入永远产生相同输出，可复现、可审计
5. **可控性**：研究者可精确调整每个词的权重，增删关键词，完全掌控分数计算逻辑

### 1.4 当前方案的已知局限（与 BERT 对比相关）

- **FIXME-14**：bigram 跨标点误匹配（"他对产品不满，意在投诉" → "不满意"被错误匹配）
- **HACK-1**：字符 n-gram 无法处理同义词（"不满意"和"不高兴"对关键词匹配是不同的）
- **HACK-13**：词典硬编码，用户无法在线编辑
- **FIXME-19**：prototype weight 字段未使用
- **歧义问题**："不满意"→ 反义匹配问题（当前 bigram 拆为"不满"+"满意"，"满意"可能被 trust 领域的关键词匹配）

---

## 2. BERT-Base 语义校准的输入输出模型

### 2.1 用户需要提供什么？

**关键词方案**：条件名 + 关键词列表（每词含权重） + 校准阈值（full_in/full_out/crossover）

**BERT 方案（最小化假定）**：
- 条件名 + **条件描述文本**（如"该文本表达了对政府服务的不满、投诉或负面情感"）+ 校准阈值
- 或者：条件名 + **正负例语义锚点**（如 3-5 条"肯定是不满"的原型文本 + 3-5 条"肯定不是不满"的原型文本）

**输入对比**：

| 输入项 | 关键词方案 | BERT 方案（描述文本） | BERT 方案（原型锚点） |
|--------|-----------|---------------------|---------------------|
| 条件定义 | 条件名 | 条件名 + 自然语言描述 | 条件名 |
| 匹配依据 | 40+ 关键词 | 1 段描述文字 | 6-10 条原型文本 |
| 校准阈值 | 3 个（full_in/out/crossover） | 3 个 | 3 个 |
| 维护成本 | 持续调优关键词列表 | 调优描述文本措辞 | 调整原型文本 |

### 2.2 BERT 相似度计算

```
文本 → BERT-Base-Chinese → [CLS] hidden state / mean pooling → 768-dim embedding
条件描述 → BERT-Base-Chinese → 768-dim embedding
相似度 = cosine_similarity(embed_text, embed_condition)  # ∈ [-1, 1], 实际通常 [0.3, 0.9]
```

关键问题：**余弦相似度本身不是模糊隶属度**。它需要经过校准（与关键词 raw score 经过 calibration 一样）。

### 2.3 BERT 是否需要"校准"步骤？

**需要**。BERT 输出的余弦相似度是语义空间中的距离度量，不是 QCA 方法学意义上的模糊隶属度。

原因：
1. 余弦相似度的分布取决于 batch 内文本的语义多样性——同一段条件描述对不同语料库产生的相似度分布不同
2. QCA 隶属度有明确的理论含义：0 = 完全不具备该属性，1 = 完全具备，0.5 = 最大模糊点
3. 余弦相似度 0.5 ≠ "最大模糊点"——不同条件/语料库的"交叉点"语义距离不同

因此，BERT 管道仍是：`text → BERT embedding → cosine similarity → calibration → membership`

BERT 替换的是 "keyword matching → raw score" 这一步，而非 calibration 步骤。

---

## 3. BERT 语义 vs 关键词匹配：根本区别

| 维度 | 关键词匹配 | BERT 语义 | 含义 |
|------|-----------|-----------|------|
| **匹配粒度** | 字面匹配（bigram 窗口） | 语义相似度（上下文向量空间） | BERT 能捕捉"办事效率低"与"处理事情太慢"的语义等价 |
| **可解释性** | 极高（精确知道哪个词命中） | 极低（768 维向量空间距离） | 关键词可审计，BERT 是黑盒 |
| **理论根基** | 强（词典本身就是理论操作化） | 弱（相似度反映的是预训练语料的分布，非研究者的理论） | QCA 要求校准有理论依据 |
| **歧义处理** | 弱（"不满意"→"满意"错误匹配） | 强（上下文理解否定、反讽、程度修饰） | BERT 天然理解"不太满意"≠"满意" |
| **跨领域泛化** | 弱（需人工构建每领域词典） | 强（预训练语义泛化，1 个模型覆盖所有领域） | BERT 可为自定义领域提供零-shot 打分 |
| **计算成本** | 极低（纯 CPU，O(n*m)，~1ms/文本） | 中等（~50-200ms/文本 on WebGPU） | 100 条文本 × 5 条件 ≈ 25-100s BERT 推理 |
| **确定性** | 完全确定 | 确定（同一模型同一输入 → 同一输出） | 但模型升级会改变所有分数 |
| **WASM 可行性** | 已运行（numpy ~10MB） | 需要额外 ~100MB 模型文件 | 首次加载从 ~50MB 增至 ~150MB |
| **Python 依赖性** | numpy（Pyodide 内置） | transformers / sentence-transformers（Pyodide 不支持） | BERT 必须在 JS 侧运行（ONNX Runtime Web），非 Pyodide |

### 3.1 关键区别：理论操作化的载体

**这是本分析最核心的论点。**

在 QCA 方法论中，校准不是纯统计操作——它是**基于理论的**（Ragin 2008, p.85: "calibration is theory-driven, not data-driven"）。

关键词方案中，`投诉(0.6) + 失望(0.7) + 糟糕(0.7)` 这组关键词和权重本身就是研究者对"不满"的理论定义。它是一个有意的、可争论的、可修改的学术主张。如果评审者认为"糟糕"的权重应该更高，他们可以提出异议——这是一个学术讨论，不是技术调参。

BERT 方案中，`cosine_similarity(embed(text), embed("对政府服务不满意"))` 是一个统计操作——它反映的是 BERT 预训练语料中文本的分布关系，不是研究者的理论主张。如果评审者质疑"为什么这条文本得了 0.73 的隶属度"，研究者无法给出理论层面的回应，只能说"模型认为它和'对政府服务不满意'的语义距离是 0.73"。

**这就是关键词匹配与 BERT 匹配的根本区别：前者承载理论，后者承载统计。**

---

## 4. 关键可行性问题的详细回答

### 4.1 用户输入作为"锚点"的语义校准是否足够？

**不足够，但可以作为补充。**

QCA 要求条件隶属度有理论依据。BERT 的余弦相似度是以"条件描述文本"为锚点的语义距离——这不是理论，是 NLP 模型在预训练语料上学到的分布。对于探索性研究（exploratory QCA），这可能是可接受的；对于验证性研究（confirmatory QCA），这是不够的。

**实用建议**：
- 条件描述文本应精确、具体，而非概括性短语。例如，"用户表达对政府服务速度慢、态度差、效率低的不满，包括投诉、举报、负面评价" 比仅 "dissatisfaction" 更有效。
- 同时提供 3-5 个正例文本和 3-5 个负例文本作为语义锚点（类似于原型校准），BERT 计算文本与这些锚点的平均余弦相似度。
- 正负例锚点方案比单一描述文本方案更接近于 QCA 的"理论锚定"哲学。

### 4.2 BERT 是否可以同时覆盖关键词匹配的所有功能？

**不能。**

当前关键词方案提供的能力清单及 BERT 的覆盖情况：

| 功能 | 关键词能否 | BERT 能否 | 说明 |
|------|-----------|-----------|------|
| 精确匹配特定术语 | 能 | 部分（语义近似） | "信访"是精确的制度术语，BERT 可能难以区分 |
| 领域覆盖 | 能（200+ 关键词 × 5 领域） | 能（1 模型 5 描述文本） | BERT 覆盖更广但不精确 |
| 同义词/变体覆盖 | 弱 | 强 | "效率低"="处理慢"="办事拖拉" 对 BERT 是相似的 |
| 否定逻辑 | 弱（"不满意"→"满意"误匹配） | 强 | "不太满意但也可以接受" BERT 理解为中度负向 |
| 用户自建领域 | 需要手动列关键词 | 需要提供描述文本 | BERT 对新领域门槛更低 |
| 分数可解释 | 能（逐词报告命中情况） | 不能（768 维黑盒） | 这是 BERT 最大的劣势 |
| 学术可辩护性 | 能（词典 = 理论） | 弱（模型 = 工具） | QCA 方法学的核心要求 |

### 4.3 语义相似度 → 模糊隶属度的校准逻辑

```
BERT cosine_similarity ∈ [expected_range: 0.2, 0.9]
    │
    ▼
需要校准！余弦相似度不是隶属度。
    │
    ▼
选项 1: Min-Max 缩放 → direct/indirect/ragin 方法（保留 3 种 calibration strategy）
    - 将余弦相似度视为另一种 raw score，通过相同的校准管道
选项 2: 直接使用（将 cosine similarity 视为 membership）
    - 简单但方法学上不严谨
    - 余弦相似度 0.3 并不对应于 QCA 中的任何理论概念
```

**建议**：选项 1。BERT 相似度应经过与关键词 raw score 相同的校准流程（min-max 归一化 → direct/indirect/ragin）。三种 calibration strategy 全部保留。

BERT 不应添加新的 calibrate 方法——校准方法描述的是"原始分数 → 隶属度"的映射逻辑，与分数的来源（关键词/BERT/原型）无关。

---

## 5. 技术可行性（Pyodide/WASM）

### 5.1 模型大小与加载

| 模型 | 参数量 | FP32 大小 | INT8 量化 | 备注 |
|------|--------|----------|-----------|------|
| BERT-Base-Chinese | 110M | ~420MB | ~110MB | 标准中文 BERT |
| paraphrase-multilingual-MiniLM-L12-v2 | 118M | ~470MB | ~120MB | sentence-transformers 推荐 |
| shibing624/text2vec-base-chinese | 110M | ~420MB | ~110MB | 中文专用 sentence embedding |
| distiluse-base-multilingual-cased-v2 | 135M | ~540MB | ~135MB | 蒸馏模型，更快推理 |

### 5.2 Pyodide 兼容性

**关键发现：sentence-transformers 和 transformers 库无法在 Pyodide 中运行。**

原因：
1. `torch` 不可用于 Pyodide（需要 C++ 扩展编译，无 WASM 后端）
2. `transformers` 依赖 `torch`
3. `sentence-transformers` 依赖 `transformers`
4. Pyodide 仅支持纯 Python 包 + 预编译的 WASM 包（如 numpy）

**这意味着 BERT 推理必须在 JavaScript 侧执行，而非在 Pyodide Python 环境中。** 这不是"好不好"的问题——Pyodide 物理上无法加载 BERT 模型。

### 5.3 JS 侧 BERT 推理方案

| 方案 | 推理引擎 | 模型格式 | 内存占用 | 推理速度（per text） |
|------|---------|---------|---------|---------------------|
| transformers.js | ONNX Runtime Web | ONNX 量化 | ~100-150MB | ~50-200ms (WebGPU) / ~500ms-2s (WASM CPU) |
| Transformers.js + WebGPU | ONNX Runtime Web + WebGPU | ONNX | ~100-150MB | ~20-80ms |
| 自定义 ONNX Runtime | ONNX Runtime Web | ONNX INT8 | ~100MB | ~50-200ms |

### 5.4 架构影响

引入 BERT 后的架构：

```
浏览器
├── Pyodide Web Worker (现有)
│   ├── numpy, pydantic, pyyaml (~50MB 加载)
│   ├── Python QCA 引擎（text_calibration, qca_engine）
│   └── 接收来自 JS 的 BERT 相似度分数
│
└── BERT Web Worker (新增)
    ├── ONNX Runtime Web (~5MB)
    ├── BERT 量化模型 (~100-120MB, CDN 缓存)
    └── 通过 postMessage 将相似度分数发送给 Pyodide worker
```

### 5.5 性能估算（100 文本 × 5 条件）

| 方案 | 推理时间 | 内存上限 | 首次加载 | 可行性 |
|------|---------|---------|---------|--------|
| 关键词（当前） | <1s | ~10MB (numpy) | ~50MB (Pyodide) | 已运行 |
| BERT (WebGPU) | ~10-50s | ~150MB (Pyodide + ONNX + BERT) | ~150MB | 可行但需 WebGPU 支持 |
| BERT (WASM CPU) | ~50-500s | ~150MB | ~150MB | 体验差，不推荐 |
| 混合（关键词 + BERT 验证） | ~1-50s | ~150MB | ~150MB | 推荐：BERT 仅用于差异检测 |

### 5.6 WebGPU 可用性

- Chrome 113+ (2023年4月): 已支持
- Edge 113+: 已支持
- Firefox Nightly: 实验性支持
- Safari 17+: 实验性支持
- 当前全球覆盖率: ~75% (2026年5月)

对于不支持的浏览器，降级为 WASM CPU（慢但可用）。

---

## 6. 方案对比

### 方案 A：完全移除关键词，纯 BERT 语义校准

**优点**：
- 用户只需提供条件描述文本，无需构建关键词词典
- 语义覆盖率高，自动处理同义词、否定、反讽
- 自定义领域门槛极低
- 代码简化（删除 ~1000 行关键词相关代码）

**缺点**：
- **失去可解释性**——无法解释"为什么这条文本得了 0.73 的隶属度"
- **失去理论根基**——QCA 校准从"理论操作化"变为"模型统计"
- **学术界接受度问题**——QCA 方法论期刊可能拒绝基于纯 BERT 校准的论文
- **模型漂移**——BERT 模型升级后所有分数改变（破坏可复现性）
- **首次加载 3x**（50MB → 150MB）
- **离线不可用**（100MB 模型文件需 CDN）

**对现有代码的影响范围**：
- 删除：keyword_dict.py, domains.py, keyword_io.py（~2500 行）
- 重写：calibrator.py（移除 KEYWORD/HYBRID 分支）
- 修改：condition.py, models/qca.py, strategies.py
- 新增：bert_similarity.py（JS 侧 BERT 推理 + Python 侧集成）
- 新增：BERT Web Worker
- 新增：ONNX Runtime Web 依赖

**WASM 可行性**：技术上可行但需要 JS 侧推理，体验取决于 WebGPU 支持

**用户输入**：每个条件提供 1 段自然语言描述文本 + 校准阈值

---

### 方案 B：BERT 为主，关键词为可选辅助/Fallback

**优点**：
- BERT 作为默认 scoring 方法，降低新用户门槛
- 保留关键词作为"高可解释性模式"供需要理论辩护的用户使用
- 条件粒度可选（条件 A 用 BERT，条件 B 用关键词）
- 可通过比较 BERT 分数和关键词分数来发现"词典覆盖率不足"的条件

**缺点**：
- 两套系统同时维护，代码量最大
- 关键词质量可能因"降级为辅助"而缺乏维护动力
- "默认 BERT"可能导致研究方法学退步（忽视理论操作化）

**对现有代码的影响范围**：
- 保留所有关键词代码
- 新增：bert_similarity.py, BERT Web Worker
- 修改：ScoringSource 枚举 + bert, calibrator.py 新增 BERT 分支
- 修改：前端 Settings 新增条件级 scoring 来源选择
- 预计新增 ~1500 行代码

**WASM 可行性**：同方案 A

**用户输入**：每个条件可选关键词或描述文本；优先用 BERT 描述文本，也可提供关键词作为可解释性参考

---

### 方案 C：关键词为主（当前方案），BERT 为未来可选项

**优点**：
- 保持当前架构稳定
- 维护 QCA 方法论纯度
- 学术界最容易辩护
- 零额外 WASM 负载

**缺点**：
- 新领域构建词典门槛高（每个领域需要 40+ 关键词）
- 关键词维护负担重
- 无法处理同义表达和隐含语义
- 竞争力随时间下降（学术界也在探索 NLP + QCA）

**对现有代码的影响范围**：
- 无需修改当前代码
- 仅在 TODO 中保留 BERT 作为 P2/P3 可选路线
- FIXME 和 HACK 中已有预留（FIXME-33, HACK-17）

**WASM 可行性**：N/A（当前方案无 BERT 依赖）

**用户输入**：当前方案不变

---

### 方案 D：双通道并存，用户可选

**优点**：
- 最大灵活性——用户完全控制每个条件的 scoring 方式
- 支持"先用关键词，再用 BERT 验证差异"的工作流
- 同时满足"理论驱动"和"数据驱动"两类用户
- 与需求变更中"raw/prototype 双路对比"的概念一致

**缺点**：
- 最复杂的实现
- UI 复杂度大幅增加（条件编辑器需显示两种 scoring 的预览）
- 首次加载从 50MB 增至 150MB（即使 BERT 只是"可选"也需要加载 ONNX Runtime）

**对现有代码的影响范围**：
- 与方案 B 相同 + 额外复杂度
- 前端：双通道配置面板 + 双通道结果对比
- 预计新增 ~3000 行代码

**WASM 可行性**：同方案 A

**用户输入**：同方案 B，但用户在两通道间的交互更复杂

---

## 7. 最终建议

### 7.1 核心立场：BERT 是补充，不是替代

作为技术顾问，我的立场是明确的：**BERT 不应完全替代关键词匹配功能。** 理由不（仅）是技术上的——技术上是可行的——而是方法学上的。

QCA 不是纯文本聚类工具。它是一个基于理论的条件分析方法。关键词词典不仅仅是"匹配引擎"，它是研究者理论立场的可操作化表达。替换关键词匹配就是替换理论操作化本身。

这不是"守旧"或"抵制新技术"。BERT 确实在很多维度上优于关键词匹配（语义覆盖、歧义处理、跨领域泛化）。但它在最关键的维度上——**理论可辩护性**——是无法替代关键词的。

### 7.2 阶段性推荐

**当前阶段（2026 Q2）**：方案 C（关键词为主，BERT 为未来可选项）
- 关键词匹配已经成熟且稳定
- 有 5 个预置领域、200+ 关键词词典
- 学术界最能接受
- 将有限工程资源用于 P0 需求变更（FIXME-23~31, csQCA 支持等）

**下一阶段（2026 Q3-Q4）**：引入 BERT 作为"语义验证"工具（方案 B 的简化版）
- 不做实时 scoring 替换，而是作为"离线对比"功能
- 对逐条文本标记"关键词分数与 BERT 相似度差异较大"的文本
- 为研究者提供词典覆盖率诊断报告（"BERT 认为这些文本属于 '不满'，但关键词词典未命中"）

**长期阶段（2027+）**：方案 B 完整实现
- 条件粒度 scoring 来源选择
- BERT 作为独立 scoring 选项（非替代默认值）
- BERT 辅助词典构建（候选关键词推荐）
- 学术界对 NLP+QCA 的接受度应已更高

### 7.3 如果必须现在做决定

如果必须在当前阶段就做出架构选择（例如因为关键利益相关者的要求），推荐**方案 B 的分阶段实施**：

1. **Phase 1（MVP）**：新增 `ScoringSource.BERT` 枚举值 + BERT Web Worker + 基本余弦相似度计算
2. **Phase 2（集成）**：calibrator.py 新增 BERT 分支，完成完整的 BERT raw score → calibration → membership 管道
3. **Phase 3（UI）**：Settings 页面条件级 scoring 来源选择器
4. **Phase 4（对比）**：Results 页面关键词 vs BERT 分数对比视图

每个 Phase 都可独立交付，且不与现有关键词功能冲突。

### 7.4 关键警告

1. **不要将 BERT 相似度直接用作隶属度**。必须经过 calibration 步骤（与关键词 raw score 一样）。
2. **BERT 模型版本必须被锁定**并随仓库一起分发。模型的任何升级都会改变所有分数，破坏可复现性。建议将 ONNX 模型文件的 hash 记录在分析结果的 metadata 中。
3. **首次加载将增至 ~150MB**（Pyodide 50MB + ONNX Runtime 5MB + BERT 模型 100MB）。建议使用 lazy loading——BERT 模型仅在用户选择 BERT scoring 时才下载。
4. **WebGPU 不是可选的**——WASM CPU 推理 100 条文本 × 5 条件需要数分钟。必须检测 WebGPU 可用性并降级引导（"您的浏览器不支持 WebGPU 加速，BERT 语义分析将较慢或不可用"）。
5. **不要删除关键词代码**。即使 BERT 成为默认选项，关键词匹配作为可解释性参考和理论辩护工具永远有其价值。

---

## 8. 对现有代码的具体影响（按方案 B）

### 8.1 需要新增的文件

| 文件 | 职责 | 预估行数 |
|------|------|---------|
| `src/services/bert.worker.ts` | BERT Web Worker：加载 ONNX 模型，接收文本批次，返回相似度矩阵 | ~250 |
| `src/experiment_engine/text_calibration/bert_similarity.py` | Python 侧 BERT 接口（通过文件系统与 JS worker 交换数据） | ~150 |
| `src/types/bert.ts` | BERT 相关 TypeScript 类型定义 | ~50 |

### 8.2 需要修改的文件

| 文件 | 变更 | 影响 |
|------|------|------|
| `models/qca.py:41-47` | `ScoringSource` 枚举新增 `BERT = "bert"` | 破坏性：所有现有 ScoringSource 引用需检查 |
| `calibrator.py:210-270` | `_compute_raw_scores()` 新增 BERT 分支 | 约 20 行新增 |
| `strategies.py` | 无需修改（BERT 相似度=raw score，复用现有 calibration） | 无 |
| `DataInput.tsx` | 条件编辑器新增 scoring 来源下拉框 | 约 50 行新增 |
| `Settings.tsx` | 新增 BERT 相关配置（模型选择、条件粒度默认） | 约 40 行新增 |
| `qca.ts` | TypeScript ScoringSource 类型同步 | 1 行新增 |
| `FIXME.md` | 新增 BERT 相关 FIXME | 本文档的一部分 |
| `HACK.md` | 更新 HACK-17（已预留 BERT 扩展点） | 本文档的一部分 |

### 8.3 WASM 加载影响

- 现有：Pyodide 运行时 ~50MB（jsDelivr CDN）
- 新增：ONNX Runtime Web ~5MB + BERT 量化模型 ~100MB（建议使用 Hugging Face or jsDelivr CDN）
- 总计：~155MB（首次冷启动，有 CDN 缓存后极快）
- Loading 策略：BERT 模型仅在 ScoringSource.BERT 被使用时才加载（lazy load）
- 降级策略：无 WebGPU 时自动使用 WASM CPU 后端（慢但可用）

---

## 9. 参考

- Ragin, C. C. (2008). *Redesigning Social Inquiry: Fuzzy Sets and Beyond*. University of Chicago Press.
- Rihoux, B. & Ragin, C. C. (2009). *Configurational Comparative Methods*. SAGE.
- Schneider, C. Q. & Wagemann, C. (2012). *Set-Theoretic Methods for the Social Sciences*. Cambridge University Press.
- Reimers, N. & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP-IJCNLP*.
- ONNX Runtime Web: https://onnxruntime.ai/docs/get-started/with-javascript/web.html
- Transformers.js: https://huggingface.co/docs/transformers.js
- Pyodide 0.26.4: https://pyodide.org/en/stable/

---

## 10. 最终决议（2026-05-25 三方综合）

### 10.1 决策过程

经过三轮逐层深入的讨论，三方（技术顾问、评审者、算法顾问）达成共识：

1. **第一轮（技术顾问初稿）**：论证 BERT 不应完全替代关键词，推荐方案 C（关键词为主，BERT 可选）
2. **第二轮（客户要求重新评估）**：用户提出"最好能用 BERT 完全取代关键词"——技术顾问设计了浏览器端双 Worker 架构，评审者提出 16 个批判性质疑
3. **第三轮（定量对比 + 独立评审）**：逐项对比两个方案的硬指标，评审者给出最终判断

### 10.2 定量对比关键数据

| 维度 | 纯关键词 | BERT L12 (兼顾方案) | 倍率 |
|------|---------|-------------------|------|
| 冷启动 10Mbps | 15s | 89s | 5.9x |
| 推理 100 文本 (WASM CPU) | 140ms | 12,070ms | 86x |
| 峰值内存 | 105MB | 273MB | 2.6x |
| 首次传输体积 | 11.5MB | 95.6MB | 8.3x |
| WebGPU 覆盖率 | 97.3% (any WASM) | 72.5% (WebGPU required for usable speed) | — |
| GitHub Pages 月容量 | ~2,850 次 | ~512 次 | 5.6x |
| 5 年可复现性 | 极高 | 中等偏低 | — |

### 10.3 最终方案：BERT 作为辅助工具，不做主引擎

**核心原则**：
1. **关键词匹配是 QCA 方法论核心，不可替代。** 关键词词典 = 理论操作化，可完整打印在论文附录供读者复现。
2. **BERT 作为辅助工具**，仅在以下场景启用：
   - **语义验证/差异标记**：对比 BERT 和关键词分数，标记分歧大的文本供人工审查
   - **词典覆盖率诊断**：发现"BERT 认为应命中但关键词遗漏"的文本，推荐候选关键词
   - **候选关键词推荐**：给定条件描述，从语料中提取高频高相关词汇供构建词典
3. **BERT 不决定隶属度分数。** 所有隶属度由关键词引擎生成，BERT 仅提供第二视角参考。

### 10.4 技术路线

**当前阶段（2026 Q2-Q3）**：不做浏览器端 BERT。关键词引擎足够成熟，P0 需求变更优先。

**下一阶段（P1-32/33 实施时）**：
- 使用 `paraphrase-multilingual-MiniLM-L6-v2`（~25MB，非 L12 的 85MB）
- 通过 `sentence-transformers` 在**纯 Python CLI** 中实现（非浏览器）
- CLI 新增命令：`qca bert-validate`、`qca bert-suggest`、`qca bert-coverage`
- 浏览器端仅在上传预计算的 BERT 分数文件时展示差异对比

**Web 端何时启用**：需全部满足以下条件后再评估：
- WebGPU 覆盖率 >90%（含 Safari 稳定支持）
- Transformers.js 发布 v3.0+ 稳定 API
- ONNX 量化模型 <30MB
- QCA 方法学期刊出现 >=3 篇 BERT 校准发表先例

### 10.5 对本会话后续工作的影响

**立即推进**：P0-9 ~ P0-12（需求变更阻塞项：prototype 统一管道 + csQCA 支持）
**暂不启动**：P2-25/26（BERT 深度集成），等待 P1-32/33 先验证 CLI 可行性
**保留**：FIXME-34/35/36 和 HACK-17/18 作为 BERT 架构预留，不删除

### 10.6 文档状态

本文档已完成其使命——为"BERT 是否应该替代关键词"这个架构问题提供了全面的分析、对比和最终判断。后续 BERT 相关工作（P1-32/33）应参考本文档第 5 节（技术可行性）和第 8 节（代码影响范围），但不再需要重新讨论"是否替代"的问题。
