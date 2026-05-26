# TODO — QCA Analysis Tool

> 自动生成于 2026-05-24 | 最后更新：2026-05-26
> 优先级：P0 = 必须做 | P1 = 应该做 | P2 = 锦上添花
> **当前焦点**: P0/P1 已清零，剩余 21 个 P2 增强项

---

## BERT+Prototype 架构重构

### 核心决策

- 废弃关键词识别方案，Prototype 理论是 QCA 的唯一理论基础
- BERT CLS embedding + 余弦相似度 → 模糊集隶属度
- 架构方案：Hybrid Transformers.js + Pyodide
- 模型：`bert-base-chinese`（ONNX int8 量化，~100MB），后续支持模型切换
- 算法：Mean Pooling + Centroid Aggregation + Softmax(τ=5.0)
- 详细规范：`.wolf/bert-prototype-algorithm-spec.md`

### P0-BERT — 全部完成

12/12 完成：cosine_similarity 引擎、bert-engine.ts 模型加载 + CLS embedding、bert-cache.ts IndexedDB 持久化缓存、模型层重构（仅保留 PROTOTYPE 评分源）、calibrator.py 移除关键词路径、Worker 协议扩展（init_bert/compute_embeddings）、pyodide handler（handle_embed_calibrate）、前端类型同步（qca.ts + bert.ts）、DataInput.tsx 重构（移除关键词编辑器）、Settings BERT 模型选择、QCAPipelineContext embedding 状态、端到端集成验证。

### P1-BERT — 清理与优化

- [x] **P1-B1~B6: 关键词遗留清理** — 删除 keyword_dict.py/keyword_io.py/PrototypeSimilarityEngine，domains.py 关键词预置替换为原型文本模板，测试套件更新，向后兼容别名 + KeywordEntry 类移除。
- [x] **P1-B7: 模型切换支持** — Settings 页支持选择不同 BERT 模型，原型嵌入随模型重新计算。(工作量: M)
- [x] **P1-B8: 性能监控面板** — BERT 推理耗时统计、嵌入缓存命中率展示。(工作量: S)

---

## 需求背景

### 用户工作流（重新理解后）

1. 研究者首先定义条件集（condition set），每个条件配置原型文本（用于语义相似度匹配）。
2. 研究者上传两批文本：(a) **raw text**（公民反馈原文，来自问卷调查/社交媒体/投诉平台）和 (b) **prototype text**（为每个条件手动撰写的"典型范例"文本）。
3. 两批文本通过**相同的处理管道**（embedding → 余弦相似度 → 校准 → 隶属度矩阵）各自生成一组隶属度数据。
4. 在最后阶段，分别对两组数据运行 QCA 分析（真值表 → 布尔最小化 → 解），产出的结果并排对比展示。

**核心用户价值**：研究者想知道——"基于原型文本校准的 QCA 解"与"基于真实公民反馈文本校准的 QCA 解"之间是否有系统性差异？如果差异显著，意味着实际数据中的条件组合模式与理论期望不同，这本身就是一项重要发现。

---

## P0 — 已完成

- [x] **P0-1: QM 指数复杂度保护** — minimize() k<=12 检查，前端 >=10 条件黄色警告。
- [x] **P0-2: pyodide.worker.ts 去重抽象** — 提取 handler 到 pyodide_handlers.py，worker 简化 30%，修复 2 个隐蔽运行时 bug。
- [x] **P0-3: QCA 核心算法单元测试** — 104 个测试覆盖 7 个模块，使用 Lipset 黄金标准数据集。
- [x] **P0-4: counterfactual.py produce_parsimonious_solution 算法错误** — 全部逻辑余项作为 don't-care，QM 扩展支持 don't-care minterm。
- [x] **P0-5: calibrator.py 混合 scoring_source 列索引偏移修复**
- [x] **P0-6: calibrator.py calibrate_ragin 实现错误修复** — 分段线性→logistic 公式重写。
- [x] **P0-7: calibrator.py match_corpus() 重复调用修复** — 预计算缓存。
- [x] **P0-8: pipeline.py 错误处理导致静默数据损坏** — fail_fast=True 默认。
- [x] **P0-9: 消除"原型模式"独立管道** — raw/prototype 统一为同一管道双输入批次。
- [x] **P0-10: csQCA 校准全链路实现** — 支持 CRISP_SET + QCAVariant。
- [x] **P0-11: FuzzySetData 重命名为 MembershipData**
- [x] **P0-12: CalibrationType 重命名为 CalibrationMethod + QCAVariant 枚举**

---

## P1 — 应该做

### 已完成

- [x] **P1-1: 关键词词典导入/导出** — CSV/JSON 批量导入自定义关键词，预置词典可另存为修改。
- [x] **P1-2: Excel 文件支持** — .xlsx/.xls 上传，自动识别文本列，支持多 sheet 切换。
- [x] **P1-3: QCA 结果自然语言解读** — 解公式旁自动生成中文解读，覆盖度和一致度通俗解释。
- [x] **P1-4: 中文界面** — 完整简体中文界面，方法学术语保留中英双语。
- [x] **P1-5: 个案级校准结果展示** — 交互表格：每行文本 + 各条件隶属度分数，可排序筛选，点击展开原文。
- [x] **P1-8: 隐私声明** — 首页/上传页添加隐私与数据安全声明，一键清除所有本地数据按钮。
- [x] **P1-9: Recent Runs 真实数据** — Dashboard 从 localStorage 读取历史记录，空状态引导文案。
- [x] **P1-10: 校准参数即时预览** — Settings/DataInput 页面参数效果预览：Plotly 直方图 + 阈值拖动实时更新隶属度分布。
- [x] **P1-14: models.py 拆分为 models/ 子包** — framework.py + qca.py + training.py。
- [x] **P1-15: 校准器策略模式重构** — CalibrationStrategy ABC + 注册表，支持新校准方法无需改源码。
- [x] **P1-16: 前端解析逻辑归一到 Pyodide Worker** — 前端仅做轻量预检，解析逻辑统一在 Worker 内。
- [x] **P1-17: 校准器 for-loop → numpy 向量化** — np.where/np.select 替换 Python 循环，WASM 下快 20-50 倍。
- [x] **P1-18~P1-23: 鲁棒性 + 报告修复** — coverage_stability 修复、perturbation 重命名、LaTeX 转义、IndexError 守卫、bootstrap 检验、theoretical_expectation 构建。
- [x] **P1-24~P1-31: 原型管道统一 + csQCA 全链路** — 删除 PROTOTYPE 独立分支、统一 calibrate handler、移除前端 mode selector、QCAVariant 枚举、CrispCalibration 策略、TruthTable 适配、去除 prototype 专用 stage、raw-prototype 对比视图。

### 剩余

- [x] **P1-6: 项目保存与恢复** — 一键"保存项目"(.qca JSON 下载)，一键"加载项目"恢复会话，localStorage 自动保存。(工作量: L, 来源: 客户#F1)
- [x] **P1-7: 参数对比 / A/B 分析** — 两组参数配置并排对比，差异高亮，对比报告可导出。(工作量: L, 来源: 客户#F2)
- [x] **P1-11: 中文 Word 报告导出** — 除 LaTeX 外增加 .docx 导出，含中文自然语言解读 + 图表嵌入。(工作量: M, 来源: 客户#F4)
- [x] **P1-12: 多结果变量分析** — Web 界面支持多结果模式，并排展示两个 outcome 的解和异同。(工作量: L, 来源: 客户#F5)
- [x] **P1-13: 条件集共享与团队模板** — 条件集导出为分享链接(base64 URL 参数)，Dashboard 展示模板库。(工作量: M, 来源: 客户#C1)

---

## P2 — 锦上添花

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

### 架构改进

- [ ] **P2-15: PluginRegistry 单例降级** — Pipeline/PluginLoader 构造函数支持注入 registry 实例，提升测试隔离性。(工作量: S-M, 来源: 技术顾问#9)
- [ ] **P2-16: 结构化可观测性** — 引入 structlog，PipelineResult 添加 metrics 字段，Worker 请求添加 request_id。(工作量: M, 来源: 技术顾问#10)
- [ ] **P2-17: CLI/Python API 一致化** — 将 CLI 命令核心逻辑提取到 api.py，qca run 配置格式改为 QCA 语义 schema。(工作量: M, 来源: 技术顾问#11)
- [ ] **P2-18: 前端自动化测试** — vitest + @testing-library/react，优先测 QCAPipelineContext reducer + useQCAWorkflow hook。(工作量: L, 来源: 技术顾问#12)
- [ ] **P2-19: prototype weight 字段启用** — `ConceptPrototype.weight` 已定义但 `compute_similarities()` 未使用，加权提升区分度。(来源: 评审者#16)
- [x] **P2-20: calibrate_indirect 的 k 可配置化** — k 作为 CalibrationParams 可选字段。
- [ ] **P2-21: `TextCase.outcome` 字段语义更新** — 当前仅支持 binary 0/1，fsQCA 模式下 outcome 应为 0.0-1.0 连续值，需添加 validator。(工作量: S, 来源: 需求变更)
- [x] **P2-22: CLI 新增 `--variant fsqca|csqca` 全局参数** — `qca calibrate`/`qca analyze`/`qca run` 等命令支持 `--variant` 选项。
- [ ] **P2-23: 多结果分析前端 UI 更新** — multi_outcome.py 已实现，前端 UI（P1-12）需适配 raw/prototype 双结果对比。(工作量: M, 来源: 需求变更)
- [ ] **P2-24: `FuzzySetData` → `MembershipData` 向后兼容别名** — 保留 deprecated alias，给下游代码迁移窗口。(工作量: S, 来源: 需求变更)

---

## 统计

| 优先级 | 剩余 |
|--------|------|
| P0 | **0** |
| P1 | **0** |
| P2 | **21** |
| **合计** | **21** |

**推荐推进顺序**：
1. **P2-1~P2-13 功能增强** — P2-1 (描述统计), P2-2 (步进引导), P2-3 (DataInput 拆分), P2-4 (工具内帮助), P2-5 (导出按钮), P2-6 (英文文本支持), P2-7 (政策文件分析), P2-8 (外部工具互操作), P2-9 (条件间关系检测), P2-10 (增量分析), P2-11 (版本对比), P2-12 (数据密码保护), P2-13 (离线桌面版)
2. **P2-15~P2-24 架构改进** — P2-15 (PluginRegistry 单例降级), P2-16 (结构化可观测性), P2-17 (CLI/Python API 一致化), P2-18 (前端自动化测试), P2-19 (prototype weight 字段启用), P2-20 (calibrate_indirect k 可配置), P2-21 (TextCase.outcome 语义更新), P2-22 (CLI --variant 参数), P2-23 (多结果 UI), P2-24 (向后兼容别名)
