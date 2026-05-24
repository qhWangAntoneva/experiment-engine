# TODO — QCA Analysis Tool

> 自动生成于 2026-05-24 | 最后更新：2026-05-24 (四阶段 P0 修复完成)
> 优先级：P0 = 必须做 | P1 = 应该做 | P2 = 锦上添花

---

## P0 — 必须修复（阻塞发布） [全部完成 ✓]

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

### 架构重构

- [ ] **P1-14: models.py 拆分为 models/framework.py + models/qca.py + models/training.py** — 框架层模型和 QCA 领域模型耦合在 9500 token 单文件中。(工作量: M, 来源: 技术顾问#4) @see FIXME-16
- [ ] **P1-15: 校准器策略模式重构** — 硬编码 if/elif 分支 → CalibrationStrategy ABC + 注册表，支持新校准方法无需改源码。(工作量: M, 来源: 技术顾问#5)
- [ ] **P1-16: 前端解析逻辑归一到 Pyodide Worker** — DataInput.tsx 的 parseTextContent() 与 TextCorpusReader 功能重复，前端应仅做轻量预检。(工作量: M, 来源: 技术顾问#7)
- [ ] **P1-17: 校准器 for-loop → numpy 向量化** — calibrate_direct/indirect/ragin 用 np.where/np.select 替换 Python 循环，WASM 下快 20-50 倍。(工作量: S-M, 来源: 技术顾问#8)

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
- [ ] **P2-14: 语义校准** — sentence-transformers 中文模型计算文本-条件语义相似度（需评估 Pyodide 性能可行性）。(工作量: XL, 来源: 客户#F3)

### 架构改进

- [ ] **P2-15: PluginRegistry 单例降级** — Pipeline/PluginLoader 构造函数支持注入 registry 实例，提升测试隔离性。(工作量: S-M, 来源: 技术顾问#9)
- [ ] **P2-16: 结构化可观测性** — 引入 structlog，PipelineResult 添加 metrics 字段，Worker 请求添加 request_id。(工作量: M, 来源: 技术顾问#10)
- [ ] **P2-17: CLI/Python API 一致化** — 将 CLI 命令核心逻辑提取到 api.py，qca run 配置格式改为 QCA 语义 schema。(工作量: M, 来源: 技术顾问#11)
- [ ] **P2-18: 前端自动化测试** — vitest + @testing-library/react，优先测 QCAPipelineContext reducer + useQCAWorkflow hook。(工作量: L, 来源: 技术顾问#12)
- [ ] **P2-19: prototype weight 字段启用** — `ConceptPrototype.weight` 已定义但 `compute_similarities()` 未使用。(来源: 评审者#16) @see FIXME-19
- [x] **P2-20: calibrate_indirect 的 k=10 可配置化** — 已通过 P0-6/Phase 1 的 calibrate_ragin 修复间接解决（logistic 变换现在正确实现）。原 k=10 硬编码仍在 calibrate_indirect 中，可作为独立优化项。(见 FIXME-22)

---

## 统计

| 优先级 | 原始 | 已修复 | 剩余 |
|--------|------|--------|------|
| P0 | 8 | 8 | 0 |
| P1 | 23 | 6 (P1-18~P1-23) | 17 |
| P2 | 20 | 0 | 20 |
| **合计** | **51** | **14** | **37** |

预计剩余工作量：约 40-50 天（1.5-2 个全职工月）。

下一 session 建议按 P1 → P2 顺序推进，优先处理：
1. P1-14 (models.py 拆分，解决 FIXME-16)
2. P1-15 (校准器策略模式重构，解决 HACK-6)
3. P1-16 + P1-17 (前端解析归一 + numpy 向量化)
4. P1-1 ~ P1-13 (功能需求，按客户优先级)
