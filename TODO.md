# TODO — QCA Analysis Tool

> 自动生成于 2026-05-24 | 来源：技术顾问 + 客户代表 + 评审者三方审查
> 优先级：P0 = 必须做 | P1 = 应该做 | P2 = 锦上添花

---

## P0 — 必须修复（阻塞发布）

### 架构 / 安全

- [ ] **P0-1: QM 指数复杂度保护** — `minimization.py` 对 k 个条件无上限检查，k>12 时浏览器 WASM 单线程卡死。在 `minimize()` 入口加 k<=12 检查，超限抛 ValueError 引导用户减少条件数或使用 Espresso 替代算法。前端 Settings 页条件数>=10 显示黄色警告。(工作量: M, 来源: 技术顾问#1)
- [ ] **P0-2: pyodide.worker.ts 去重抽象** — 10 个 handler 重复相同模式：`JSON.stringify → FS.writeFile → runPythonAsync(40行字符串) → JSON.parse`。将内嵌 Python 代码提取为 `pyodide_handlers.py` 独立函数，worker handler 简化为通用模板。(工作量: L, 来源: 技术顾问#2) @see FIXME-15, HACK-8
- [ ] **P0-3: QCA 核心算法单元测试** — consistency.py/truth_table.py/minimization.py/necessity.py/sufficiency.py/calibrator.py/keyword_dict.py 完全无独立单元测试。用 Ragin 2008 教材 Lipset 数据集作为黄金标准基准测试。(工作量: L, 来源: 技术顾问#3, 评审者#20)

### 算法 Bug

- [ ] **P0-4: counterfactual.py `produce_parsimonious_solution` 算法错误** — 精简解应包含全部逻辑余项作为 don't-care 行，当前仅包含 easy counterfactuals，行为与中间解相同。需重构为添加所有 frequency<1.0 的行。(来源: 评审者#1) @see FIXME-1, HACK-5
- [ ] **P0-5: calibrator.py 混合 scoring_source 列索引偏移** — KEYWORD/HYBRID/PROTOTYPE 混合时 `col_idx` 直接索引 `match_corpus()` 返回矩阵导致列错位。需建立 col_idx → kw_col_idx 映射。(来源: 评审者#2) @see FIXME-2
- [ ] **P0-6: calibrator.py `calibrate_ragin` 实现错误** — docstring 声称 Ragin log-odds 直接法，实际是分段线性插值（与 `calibrate_direct` 相同）。需用正确 logistic 公式重写。(来源: 评审者#3) @see FIXME-3
- [ ] **P0-7: calibrator.py `match_corpus()` 重复调用** — 每个 KEYWORD 条件都调用一次 `match_corpus()`，O(n_conditions × n_texts × n_keywords) 冗余。应在 `process()` 开头缓存一次。(来源: 评审者#4) @see FIXME-4
- [ ] **P0-8: pipeline.py 错误处理导致静默数据损坏** — Stage 失败后管道传给下游上次正常数据，导致 `QCAnalyzerStage` 收到原始文本而非模糊集。加 `fail_fast` 配置项（默认 True）中止管道。(来源: 技术顾问#6) @see FIXME-5

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

### 架构重构

- [ ] **P1-14: models.py 拆分为 models/framework.py + models/qca.py + models/training.py** — 框架层模型和 QCA 领域模型耦合在 9500 token 单文件中。(工作量: M, 来源: 技术顾问#4) @see FIXME-16
- [ ] **P1-15: 校准器策略模式重构** — 硬编码 if/elif 分支 → CalibrationStrategy ABC + 注册表，支持新校准方法无需改源码。(工作量: M, 来源: 技术顾问#5)
- [ ] **P1-16: 前端解析逻辑归一到 Pyodide Worker** — DataInput.tsx 的 parseTextContent() 与 TextCorpusReader 功能重复，前端应仅做轻量预检。(工作量: M, 来源: 技术顾问#7)
- [ ] **P1-17: 校准器 for-loop → numpy 向量化** — calibrate_direct/indirect/ragin 用 np.where/np.select 替换 Python 循环，WASM 下快 20-50 倍。(工作量: S-M, 来源: 技术顾问#8)

### 算法 / 报告修复

- [ ] **P1-18: robustness.py `test_consistency_sensitivity` 的 coverage_stability 始终为 0** — `hasattr(tt, "solution_coverage")` 始终 False，该列无意义。应 run minimization + sufficiency 计算真实 coverage。(来源: 评审者#9) @see FIXME-6
- [ ] **P1-19: robustness.py `test_calibration_sensitivity` 是 membership perturbation 而非 calibration sensitivity** — 应扰动 calibration_params 的阈值参数重新校准。(来源: 评审者#8) @see FIXME-7
- [ ] **P1-20: qca_reporter.py LaTeX 特殊字符转义** — `*`、`~`、`_` 等字符直接插入 LaTeX 会导致编译失败或错误渲染。(来源: 评审者#12) @see FIXME-10
- [ ] **P1-21: qca_reporter.py `_robustness_section` 空列表 IndexError** — `solution_stability[0]` 在列表为空时崩溃，需加守卫。(来源: 评审者#13) @see FIXME-11
- [ ] **P1-22: robustness.py 缺失 bootstrap 鲁棒性检验** — docstring 提到但 `run_all()` 无任何 resampling 方法。(来源: 评审者#10) @see FIXME-8
- [ ] **P1-23: counterfactual.py theoretical_expectation 字段始终为 None** — 从未从 directional_expectations 赋值。(来源: 评审者#7) @see FIXME-9

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
- [ ] **P2-14: 语义校准** — sentence-transformers 中文模型计算文本-条件语义相似度（需评估 Pyodide 性能可行性）。(工作量: XL, 来源: 客户#F3)

### 架构改进

- [ ] **P2-15: PluginRegistry 单例降级** — Pipeline/PluginLoader 构造函数支持注入 registry 实例，提升测试隔离性。(工作量: S-M, 来源: 技术顾问#9)
- [ ] **P2-16: 结构化可观测性** — 引入 structlog，PipelineResult 添加 metrics 字段，Worker 请求添加 request_id。(工作量: M, 来源: 技术顾问#10)
- [ ] **P2-17: CLI/Python API 一致化** — 将 CLI 命令核心逻辑提取到 api.py，qca run 配置格式改为 QCA 语义 schema。(工作量: M, 来源: 技术顾问#11)
- [ ] **P2-18: 前端自动化测试** — vitest + @testing-library/react，优先测 QCAPipelineContext reducer + useQCAWorkflow hook。(工作量: L, 来源: 技术顾问#12)
- [ ] **P2-19: prototype weight 字段启用** — `ConceptPrototype.weight` 已定义但 `compute_similarities()` 未使用。(来源: 评审者#16) @see FIXME-19
- [ ] **P2-20: calibrate_indirect 的 k=10 可配置化** — logistic 变换 steepness factor 硬编码，应作为 CalibrationParams 可选字段。(来源: 评审者#19) @see FIXME-22

---

## 统计

| 优先级 | 数量 |
|--------|------|
| P0 | 8 |
| P1 | 23 |
| P2 | 20 |
| **合计** | **51** |

预计总工作量：约 60-80 天（2-3 个全职工月），建议按 P0 → P1 → P2 分阶段实施。
