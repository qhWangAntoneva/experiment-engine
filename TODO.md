# TODO — QCA Analysis Tool

> 自动生成于 2026-05-24 | 最后更新：2026-05-24 (需求变更审查 + 客户代表分析)
> 优先级：P0 = 必须做 | P1 = 应该做 | P2 = 锦上添花

---

## 需求背景（客户代表分析，2026-05-24）

### 用户工作流的重新理解

**之前的错误认知**：将"prototype text"视为独立于"raw text"的输入模式，要求用户在 DataInput 页面二选一（keyword 模式 或 prototype 模式）。

**正确的用户场景**：
1. 研究者首先定义条件集（condition set），每个条件配置关键词词典（用于关键词匹配）和/或原型文本（用于语义相似度匹配）。
2. 研究者上传两批文本：(a) **raw text**（公民反馈原文，来自问卷调查/社交媒体/投诉平台）和 (b) **prototype text**（为每个条件手动撰写的"典型范例"文本，如"不满"条件的一段代表性投诉文字）。
3. 两批文本通过**相同的处理管道**（关键词提取 → 原始分数计算 → 校准 → 隶属度矩阵）各自生成一组 CLI。
4. 在最后阶段，分别对两组 CLI 运行 QCA 分析（真值表 → 布尔最小化 → 解），产出的结果并排对比展示。

**核心用户价值**：研究者想知道——"基于原型文本校准的 QCA 解"与"基于真实公民反馈文本校准的 QCA 解"之间是否有系统性差异？如果差异显著，意味着实际数据中的条件组合模式与理论期望不同，这本身就是一项重要发现。

### fsQCA vs csQCA 的用户选择场景

| 场景 | 推荐方法 | 典型使用情况 |
|------|---------|------------|
| 公民情感分析 | fsQCA | "不满"不是有/无的二分，而是从轻微不满到极度愤怒的连续谱 |
| 政策需求强度分析 | fsQCA | 需求从"随口一提"到"强烈呼吁"是连续变化的 |
| 合产意愿 | csQCA | 愿意/不愿意参与是清晰的二分 |
| 政府回应结果 | csQCA | 回应了/没回应是二分 |
| 定性比较研究（小 N，如 10-30 个案例） | csQCA | 手工编码每个案例在每个条件上的 0/1 |
| 大样本文本挖掘（N > 100） | fsQCA | 自动关键词匹配产生连续分数，模糊集更自然 |

用户应该能**一键切换** fsQCA/csQCA，而非重新配置所有校准参数——切换时系统应自动调整校准阈值界面（csQCA 隐藏 full_in/full_out/crossover）。

### BERT 语义校准的产品定位 **[已定案 2026-05-25]**

**最终决议**：BERT 作为辅助工具，不做主引擎。关键词匹配是 QCA 方法论核心，不可替代。

详见 `.wolf/bert-vs-keyword-analysis.md` 第 10 节"最终决议"。

**决策要点**：
- 关键词匹配 = QCA 理论操作化载体，不可移除
- BERT 仅用于：(1) 语义验证/差异标记，(2) 词典覆盖率诊断，(3) 候选关键词推荐
- BERT 不决定隶属度分数——所有隶属度由关键词引擎生成
- 先从纯 Python CLI（`qca bert-validate`、`qca bert-suggest`、`qca bert-coverage`）开始，使用 `paraphrase-multilingual-MiniLM-L6-v2`（~25MB）
- 浏览器端 BERT（Transformers.js + ONNX Runtime Web）等待 WebGPU 覆盖率 >90% + Safari 稳定支持 + 模型 <30MB 后再评估

**与 P1-32/33 的关系**：P1-32/33 仍然是下一阶段任务，但范围已明确缩小为"CLI 辅助工具"，不做浏览器端主引擎。

---

## P0 — 必须修复（阻塞发布）

### 需求变更导致的阻塞项（2026-05-24 评审者审查）

- [ ] **P0-9: 消除 "原型模式" 独立管道** — 当前 `ScoringSource.PROTOTYPE` 将原型文本视为独立校准模式（前端模式选择器、独立 handler、独立 pipeline 状态）。需求澄清后：raw text 和 prototype text 是同一管道的两个输入批次，仅在最后分别输出各自的 score 和 QCA result。需统一处理管道。(工作量: L, 来源: 需求变更, @see FIXME-23)
- [ ] **P0-10: csQCA（清晰集）校准全链路实现** — 当前 `CalibrationType` 仅含模糊集校准方法（direct/indirect/fuzzy_direct/passthrough），缺失 crisp-set 校准。需新增 `CRISP_SET` 校准类型：单一阈值将 raw score 二分为 0/1。同时需在 strategies.py、calibrator.py、truth_table.py、CLI、前端 Settings 全链路支持。(工作量: L, 来源: 需求变更, @see FIXME-24)
- [ ] **P0-11: `FuzzySetData` 重命名为 `MembershipData`（或更通用的名称）** — 类名暗示仅支持模糊集，但实际上 0/1 crisp-set 值也通过该结构流通。csQCA 使用时会语义混淆。(工作量: M, 来源: 需求变更, @see FIXME-25)
- [ ] **P0-12: `CalibrationType` 重命名为 `CalibrationMethod` + 析出 fsQCA/csQCA 区分** — 当前 `CalibrationType` 混合了校准算法（direct/indirect/ragin）和 set 类型区别。应新增顶层 `QCAVariant: fsQCA | csQCA` 枚举，`CalibrationMethod` 仅表示算法。(工作量: M, 来源: 需求变更, @see FIXME-26)

### 已完成的 P0

- [x] **P0-1: QM 指数复杂度保护** — minimize() 添加 k<=12 检查，超限抛 ValueError。前端 Settings 页 >=10 条件黄色警告。(Phase 3, 提交 9b58081)
- [x] **P0-2: pyodide.worker.ts 去重抽象** — 提取 7 个 Python handler 到 `pyodide_handlers.py`，worker 简化为 `runHandler()` 通用模板。659→464 行 (-30%)。同步修复 2 个隐蔽运行时 bug。(Phase 4, 提交 d08786c)
- [x] **P0-3: QCA 核心算法单元测试** — 新增 `tests/test_qca_core.py` 104 个测试覆盖 7 个模块，使用 Ragin 2008 Lipset 数据集作为黄金标准。测试套件 361→465。(Phase 4, 提交 d08786c)
- [x] **P0-4: counterfactual.py `produce_parsimonious_solution` 算法错误** — 全部逻辑余项作为 don't-care；QM 扩展支持 don't-care minterm。(Phase 1, 提交 c4c6aa2) @see FIXME-1, HACK-5
- [x] **P0-5: calibrator.py 混合 scoring_source 列索引偏移** — `_precompute_kw_context()` 建立 col_idx→kw_col_idx 映射。(Phase 1, 提交 c4c6aa2) @see FIXME-2
- [x] **P0-6: calibrator.py `calibrate_ragin` 实现错误** — 分段线性→logistic 公式重写。(Phase 1, 提交 c4c6aa2) @see FIXME-3
- [x] **P0-7: calibrator.py `match_corpus()` 重复调用** — `_precompute_kw_context()` 缓存一次。(Phase 1, 提交 c4c6aa2) @see FIXME-4
- [x] **P0-8: pipeline.py 错误处理导致静默数据损坏** — fail_fast=True 默认，失败时立即中止。(Phase 2, 提交 9842e11) @see FIXME-5

---

## P1 — 应该做（下一个版本）

### 功能需求

- [ ] **P1-1: 关键词词典导入/导出** — 支持 CSV/JSON 批量导入自定义关键词，预置词典可"另存为"修改，词典可导出复用。(工作量: M, 来源: 客户#P1)
- [ ] **P1-2: Excel 文件支持** — 直接上传 .xlsx/.xls，自动识别文本列，支持多 sheet 切换。(工作量: S, 来源: 客户#P2)
- [ ] **P1-3: QCA 结果自然语言解读** — 解公式旁自动生成中文自然语言解读，覆盖度和一致度通俗解释。(工作量: L, 来源: 客户#P3)
- [ ] **P1-4: 中文界面** — 完整简体中文界面（至少作为可切换语言），方法学术语保留中英双语。(工作量: L, 来源: 客户#P4)
- [ ] **P1-5: 个案级校准结果展示** — 校准完成后展示交互表格：每行文本 + 各条件隶属度分数，可排序筛选，点击展开原文和高亮关键词。(工作量: M, 来源: 客户#P5)
- [ ] **P1-6: 项目保存与恢复** — 一键"保存项目"(.qca JSON 下载)，一键"加载项目"恢复会话，localStorage 自动保存。(工作量: L, 来源: 客户#F1)
- [ ] **P1-7: 参数对比 / A/B 分析** — 两组参数配置并排对比，差异高亮，对比报告可导出。(工作量: L, 来源: 客户#F2)
- [ ] **P1-8: 隐私声明** — 首页/上传页添加隐私与数据安全声明，"一键清除所有本地数据"按钮。(工作量: S, 来源: 客户#D1)
- [ ] **P1-9: Recent Runs 真实数据** — Dashboard 的 Recent Runs 从 localStorage 读取历史记录，空状态引导文案。(工作量: S, 来源: 客户#U1)
- [ ] **P1-10: 校准参数即时预览** — Settings/DataInput 页面添加参数效果预览：拖动阈值竖线，实时更新隶属度分布。(工作量: M, 来源: 客户#U2)
- [ ] **P1-11: 中文 Word 报告导出** — 除 LaTeX 外增加 .docx 导出，含中文自然语言解读 + 图表嵌入。(工作量: M, 来源: 客户#F4)
- [ ] **P1-12: 多结果变量分析** — Web 界面支持多结果模式，并排展示两个 outcome 的解和异同。(工作量: L, 来源: 客户#F5)
- [ ] **P1-13: 条件集共享与团队模板** — 条件集导出为分享链接(base64 URL 参数)，Dashboard 展示模板库。(工作量: M, 来源: 客户#C1)

### 需求变更相关（原型管道统一 + csQCA）

- [ ] **P1-24: 删除 `ScoringSource.PROTOTYPE` 独立分支** — calibrator.py `_compute_raw_scores()` 中 PROTOTYPE/HYBRID 分支不再是独立模式。原型相似度应作为所有条件的通用 scoring 选项之一（和 keyword 并列），而非管道级模式切换。(工作量: L, 来源: 需求变更, @see FIXME-23)
- [ ] **P1-25: 统一 `handle_calibrate` 和 `handle_calibrate_prototype`** — pyodide_handlers.py 和 pyodide.worker.ts 中双 handler 合并为单一 `handle_calibrate(texts, conditionSet)`，支持传入两组文本（raw + prototype）。(工作量: M, 来源: 需求变更)
- [ ] **P1-26: 前端去除 prototype/keyword mode selector** — DataInput.tsx 的模式切换器移除，原型文本输入和 raw text 输入同时可见。条件编辑器中 prototype 文本不再独占一个 tab，而是作为条件的可选字段。(工作量: L, 来源: 需求变更)
- [ ] **P1-27: 新增 `QCAVariant` 枚举（fsQCA vs csQCA）** — models/qca.py 新增 `QCAVariant` 枚举，`ConditionSet` 新增 `qca_variant` 字段。fsQCA 使用连续模糊校准，csQCA 使用二分 crisp 校准。Settings 页新增 variant 选择开关。(工作量: M, 来源: 需求变更, @see FIXME-26)
- [ ] **P1-28: 新增 `CrispCalibration` 策略** — strategies.py 新增 `CrispCalibration(CalibrationStrategy)`：单一阈值二分 raw score。threshold >= crossover → 1，否则 → 0。注册到 `CalibrationStrategyRegistry`。(工作量: S, 来源: 需求变更, @see FIXME-24)
- [ ] **P1-29: TruthTableBuilder 支持 crisp-set 配置隶属度计算** — 当前 `_compute_config_membership` 用 `min(membership, 1-membership)`（模糊逻辑 AND），csQCA 需使用 `min(value, 1-value)`（布尔逻辑）。(工作量: S, 来源: 需求变更)
- [ ] **P1-30: 前端 QCAPipelineContext 去除 prototype 专用 stage** — 移除 `calibrating-prototype`、`calibrated-prototype` stage，移除 `startPrototypeCalibration`/`finishPrototypeCalibration` action。(工作量: S, 来源: 需求变更)
- [ ] **P1-31: Result 页新增 raw-prototype 对比视图** — 两侧并排展示 raw text 的 QCA result 和 prototype text 的 QCA result，差异高亮。(工作量: M, 来源: 需求变更)

### 语义校准（BERT）路线图（客户代表分析新增）

- [ ] **P1-32: BERT 语义校准产品定位与 CLI 命令设计** [用户故事] 作为研究者，我需要理解 BERT 辅助工具的使用场景：(1) `qca bert-validate` — 对比 BERT 和关键词分数，标记分歧文本供人工审查；(2) `qca bert-suggest` — 从语料中推荐候选关键词；(3) `qca bert-coverage` — 词典覆盖率诊断报告。BERT 不作为主引擎，不决定隶属度分数。产出：CLI 子命令设计 + `bert_engine.py`（纯 Python，sentence-transformers）+ pyproject.toml 可选依赖 `qca[bert]`。(工作量: M, 来源: 客户代表, @see .wolf/bert-vs-keyword-analysis.md#10 最终决议)

- [ ] **P1-33: BERT CLI 可行性 PoC — 轻量模型 + 双通道审计** [用户故事] 验证纯 Python CLI 下使用 `paraphrase-multilingual-MiniLM-L6-v2`（~25MB）进行 BERT 辅助分析的可行性。需验证：模型加载时间、100 条文本 × 5 条件的推理延迟（期望 <5s）、与现有关键词分数的 Spearman 秩相关系数、`qca bert-validate` 输出的差异报告格式。产出：可行/不可行判断 + 性能数据 + CLI 命令原型。(工作量: M, 来源: 客户代表, @see .wolf/bert-vs-keyword-analysis.md#10 最终决议)

注意：浏览器端 BERT（Transformers.js + ONNX Runtime Web）**不在 P1 范围内**。P1-33 仅验证 CLI 方案。浏览器端需等待 WebGPU 覆盖率 >90% + Safari 稳定支持后再评估。

- [ ] **P1-34: 预置词典在线编辑器** [用户故事] 作为研究者，我应能在前端直接编辑预置词典（添加/修改/删除关键词和权重），无需手动编辑 YAML 或后端 domains.py。当前预置词典硬编码在 `domains.py`，用户只能通过导入词典间接修改，修改后的词典也不会持久化。需：前端编辑表格 + localStorage 持久化修改 + "恢复默认词典"按钮。(工作量: M, 来源: 客户代表, @see HACK-13)

### 架构重构

- [x] **P1-14: models.py 拆分为 models/framework.py + models/qca.py + models/training.py** — 框架层模型和 QCA 领域模型耦合在 9500 token 单文件中。(工作量: M, 来源: 技术顾问#4) @see FIXME-16 [DONE 2026-05-24]
- [x] **P1-15: 校准器策略模式重构** — 硬编码 if/elif 分支 → CalibrationStrategy ABC + 注册表，支持新校准方法无需改源码。(工作量: M, 来源: 技术顾问#5) [DONE 2026-05-24, 提交 10dbed0] @see HACK-6
- [x] **P1-16: 前端解析逻辑归一到 Pyodide Worker** — DataInput.tsx 的 parseTextContent() 与 TextCorpusReader 功能重复，前端应仅做轻量预检。(工作量: M, 来源: 技术顾问#7) [DONE 2026-05-24, 提交 b9b1687] @see HACK-7, HACK-10
- [x] **P1-17: 校准器 for-loop → numpy 向量化** — calibrate_direct/indirect/ragin 用 np.where/np.select 替换 Python 循环，WASM 下快 20-50 倍。(工作量: S-M, 来源: 技术顾问#8) [DONE 2026-05-24, 提交 b9b1687]

### 算法 / 报告修复 [部分已完成]

- [x] **P1-18: robustness.py coverage_stability 始终为 0** — 已 run minimization + sufficiency 计算真实 coverage。(Phase 3, 提交 9b58081) @see FIXME-6
- [x] **P1-19: robustness.py test_calibration_sensitivity 实际是 membership perturbation** — 已重命名为 test_membership_perturbation，排除 outcome 列，保留向后兼容别名。(Phase 3, 提交 9b58081) @see FIXME-7
- [x] **P1-20: qca_reporter.py LaTeX 特殊字符转义** — 已添加 _escape_latex() + _escape_latex_formula() 应用于全部用户文本插入点。(Phase 3, 提交 9b58081) @see FIXME-10
- [x] **P1-21: qca_reporter.py `_robustness_section` 空列表 IndexError** — 已添加 if t.solution_stability: 守卫。(Phase 3, 提交 9b58081) @see FIXME-11
- [x] **P1-22: robustness.py 缺失 bootstrap 鲁棒性检验** — 已添加 test_bootstrap(n_iterations=100)。(Phase 3, 提交 9b58081) @see FIXME-8
- [x] **P1-23: counterfactual.py theoretical_expectation 字段始终为 None** — 已从 directional_expectations 构建 theo_exp。(Phase 2, 提交 9842e11) @see FIXME-9

---

## P2 — 锦上添花（未来版本）

### 功能增强

- [ ] **P2-1: 数据预分析和描述统计** — 文本长度分布、关键词命中热力图、条件分布直方图 + 偏度警告。(工作量: M, 来源: 客户#P6)
- [ ] **P2-2: 全流程步进引导 (Stepper)** — 所有页面顶部统一步进指示器：Upload → Calibrate → Analyze → Review。(工作量: M, 来源: 客户#U3)
- [ ] **P2-3: DataInput 页面拆分** — 拆为 3 个引导步骤，YAML 编辑器默认折叠，初级用户使用表单模式。(工作量: M, 来源: 客户#U4)
- [ ] **P2-4: 工具内帮助和术语解释** — 每个设置项旁 `?` 图标，hover 弹出通俗中文解释 + 推荐值。(工作量: S, 来源: 客户#U5)
- [ ] **P2-5: 导出按钮一致性与反馈** — 统一位置 + toast 通知 + LaTeX 预览 modal。(工作量: S, 来源: 客户#U6)
- [ ] **P2-6: 英文文本支持** — 关键词引擎支持空格分词 + 词干提取，英文预置领域，UI 中英切换。(工作量: L, 来源: 客户#S1)
- [ ] **P2-7: 政策文件分析场景** — "自定义领域"模式，不绑定 5 个预置领域，提供 1-2 个非公民反馈示例领域。(工作量: L, 来源: 客户#S2)
- [ ] **P2-8: 外部 QCA 工具互操作** — 导入 R QCA 包格式模糊集数据，导出 fsQCA 兼容真值表。(工作量: M, 来源: 客户#S3)
- [ ] **P2-9: 条件间关系检测** — 相关系数矩阵热力图，>0.8 警告，Venn/Upset 图。(工作量: S, 来源: 客户#F7)
- [ ] **P2-10: 增量分析** — 追加新数据，仅对新增数据校准后重新跑真值表，结果变化对比。(工作量: M, 来源: 客户#F6)
- [ ] **P2-11: 分析结果版本对比** — 每次运行自动记录快照，版本对比视图，导出分析日志。(工作量: M, 来源: 客户#C2)
- [ ] **P2-12: 数据密码保护** — 可选会话密码，AES-GCM 加密 localStorage，30 分钟无操作自动锁定。(工作量: M, 来源: 客户#D2)
- [ ] **P2-13: 离线桌面版** — Electron 封装，预打包 Pyodide + numpy + Python 包，完全离线。(工作量: XL, 来源: 客户#S4)
- [ ] **P2-14: 语义校准** — 已拆分为 P1-32（产品定位+交互设计）、P1-33（Pyodide 可行性 PoC）、P2-25（条件级混合模式）、P2-26（BERT 可解释性视图）。原单条 XL 任务已拆分，本条不再独立追踪。(工作量: 已拆分, 来源: 客户#S5)

### 架构改进

- [ ] **P2-15: PluginRegistry 单例降级** — Pipeline/PluginLoader 构造函数支持注入 registry 实例，提升测试隔离性。(工作量: S-M, 来源: 技术顾问#9)
- [ ] **P2-16: 结构化可观测性** — 引入 structlog，PipelineResult 添加 metrics 字段，Worker 请求添加 request_id。(工作量: M, 来源: 技术顾问#10)
- [ ] **P2-17: CLI/Python API 一致化** — 将 CLI 命令核心逻辑提取到 api.py，qca run 配置格式改为 QCA 语义 schema。(工作量: M, 来源: 技术顾问#11)
- [ ] **P2-18: 前端自动化测试** — vitest + @testing-library/react，优先测 QCAPipelineContext reducer + useQCAWorkflow hook。(工作量: L, 来源: 技术顾问#12)
- [ ] **P2-19: prototype weight 字段启用** — `ConceptPrototype.weight` 已定义但 `compute_similarities()` 未使用。需求变更后该字段仍有意义（prototype 相似度作为 scoring 选项，加权提升区分度）。(来源: 评审者#16) @see FIXME-19
- [ ] **P2-20: calibrate_indirect 的 k=10 可配置化** — P0-6/Phase 1 的 calibrate_ragin 修复解决了 logistic 变换正确性问题，但 calibrate_indirect 的 steepness factor k=10 仍硬编码不可配置。需将 k 作为 CalibrationParams 可选字段。(见 FIXME-22)
- [ ] **P2-21: `TextCase.outcome` 字段语义更新** — 当前字段描述为 "Binary outcome (0 or 1) used directly as crisp-set membership"，但 fsQCA 模式下 outcome 应为连续值。需支持 0.0-1.0 连续值并添加 validator。(工作量: S, 来源: 需求变更)
- [ ] **P2-22: CLI 新增 `--variant fsqca|csqca` 全局参数** — `qca calibrate`、`qca analyze`、`qca run` 等命令添加 `--variant` 选项，控制是否使用 crisp-set 校准和真值表构建。(工作量: S, 来源: 需求变更)
- [ ] **P2-23: 多结果分析前端 UI 更新** — multi_outcome.py 已实现，但前端 UI（P1-12）需适配需求变更后的 raw/prototype 双结果对比。(工作量: M, 来源: 需求变更)
- [ ] **P2-24: `FuzzySetData` → `MembershipData` 迁移向后兼容别名** — 重命名后保留 `FuzzySetData` 作为 deprecated alias（或反向：新增 `MembershipData` alias），内部使用新名称，给下游代码迁移窗口。(工作量: S, 来源: 需求变更, @see FIXME-25)

### BERT 深度集成（依赖 P1-33 CLI PoC 通过 + 浏览器端条件满足后评估）

- [ ] **P2-25: 条件级"混合模式"配置** [用户故事] 作为研究者，我对"不满"条件使用关键词匹配，对"信任"条件使用 BERT 辅助验证。Settings 每个条件旁应有"启用 BERT 验证"开关，开启后校准结果页展示该条件的 BERT vs 关键词差异图表。BERT 不决定分数，仅做对比参考。**注意**：本项等待 P1-33 CLI PoC 通过 + WebGPU >90% 后再实施。(工作量: L, 来源: 客户代表, 依赖: P1-33 + 浏览器端条件)

- [ ] **P2-26: BERT 语义匹配差异可视化视图** [用户故事] BERT 验证启用后，Results 展示每条文本的 BERT 相似度 vs 关键词分数的散点图 + 分歧文本高亮表格。用户点击高分歧文本可查看关键词命中详情和 BERT 语义分析（为什么"模型认为"这条文本更接近/更远离该条件）。(工作量: L, 来源: 客户代表, 依赖: P1-33 + P2-25)

---

## 统计

| 优先级 | 原始 | 已修复 | 新增(需求变更+客户代表) | 剩余 |
|--------|------|--------|------------------------|------|
| P0 | 8 | 8 | 4 | 4 |
| P1 | 23 | 10 (P1-14~P1-23) | 11 | 24 |
| P2 | 20 | 0 | 6 | 26 |
| **合计** | **51** | **18** | **21** | **54** |

预计剩余工作量：约 55-70 天（2-2.5 个全职工月），其中需求变更新增约 15-20 天，BERT 路线图约 5-10 天。

下一 session 建议按 P0 → P1 → P2 顺序推进，优先处理：

> **重要架构决策（2026-05-25）**：BERT 作为辅助工具不做主引擎。关键词匹配是 QCA 方法论核心，不可替代。详见 `.wolf/bert-vs-keyword-analysis.md` 第 10 节。P1-32/33（BERT CLI 辅助工具）在 P0 需求变更完成后启动。P2-25/26（浏览器端 BERT）等待条件满足后再评估。

1. P0-9 ~ P0-12 (需求变更导致的阻塞项：原型管道统一 + csQCA 支持)
2. P1-24 ~ P1-31 (需求变更相关的 P1 项)
3. P1-34 (预置词典在线编辑器)
4. P1-1 ~ P1-13 (功能需求，按客户优先级)
5. P1-32 + P1-33 (BERT CLI 辅助工具 — 范围已缩小为纯 Python CLI)
