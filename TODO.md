# TODO — QCA Analysis Tool

> 更新于 2026-05-27 | 整合三位专业架构师（后端/前端/DevOps）优化分析报告
> P0/P1 全部完成 | 新增 13 个 P2 优化项（来自架构评审）

---

## P0 — 全部完成

12 项：QM 指数保护、Worker 去重、核心算法测试、Parsimonious 算法修复、列索引偏移修复、Ragin 校准修复、match_corpus 重复调用、Pipeline fail_fast、原型管道统一、csQCA 全链路、模型重命名、枚举重构。

## P1 — 全部完成

25 项：关键词清理、模型切换、性能面板、词典导入导出、Excel 支持、NL 解读、中文界面、个案级展示、隐私声明、Recent Runs、参数预览、Project Save/Load、参数对比、DOCX 导出、多结果分析、条件集共享、PluginRegistry、CLI/API 一致化、prototype weight、k 可配置、TextCase 语义更新、--variant 参数、多结果 UI、向后兼容别名、模型分包。

---

## P2 — 锦上添花

### A. 后端/算法优化（来自后端架构师分析）

- [ ] **P2-25: 统一 CSV 读取路径** — `api.py` 直接调用 `pd.read_csv`，而 `io/readers.py` `TextCorpusReader` 有独立实现，两条代码路径行为不一致。统一为一套 CSV 解析逻辑，增加列名校验。（工作量: M）
- [ ] **P2-26: 消除 FuzzySetData 废弃别名** — 代码库仍有多处引用 `FuzzySetData`（deprecated 别名），统一为 `MembershipData` 后彻底移除。（工作量: S）
- [ ] **P2-27: 后端 BERT 嵌入服务** — CLI/API 路径当前使用三元组 Jaccard fallback，与浏览器端 Transformers.js BERT 有语义鸿沟。后端引入 ONNX Runtime 或 sentence-transformers，使所有路径获得一致的语义评分。（工作量: XL，依赖外部模型部署）
- [ ] **P2-28: validate_qca_output.py 增强** — 增加 membership 形状验证 `(N_cases, N_conditions+1)`、outcome 列唯一值数量检查（确保非退化）、solution 质量评分。（工作量: S）

### B. 前端/可视化优化（来自前端架构师分析）

- [ ] **P2-29: 可视化桥接集成** — `viz/` 模块存在但从未被调用。在 `pyodide_handlers.py` 新增 `handle_visualize()` 返回 JSON 绘图数据，前端新增 `VizDataViewer` 组件统一展示热力图/柱状图/散点图，复用现有 `PlotlyChart`。（工作量: L）
- [ ] **P2-30: 可视化组件错误边界与加载态** — 用 React Error Boundary 包裹每个可视化卡片（FuzzySetHeatmap、NecessityXYPlot、SolutionViewer），配合 Suspense + skeleton 加载态。当前异步数据加载无保护。（工作量: M）
- [ ] **P2-31: Plotly 显示模式栏** — 真值表等组件 `displayModeBar: false`，用户无法下载/缩放。改为 `displayModeBar: 'hover'` + 添加 `toImageButtonOptions` 支持一键导出 PNG。（工作量: S）
- [ ] **P2-32: 可视化组件间联动** — 真值表高亮行时在解决方案视图自动定位、必要性散点图点击展开条件详细信息。当前各可视化组件间无交互联动。（工作量: L）

### C. 报告/DevOps 优化（来自 DevOps 工程师分析）

- [ ] **P2-33: LaTeX 空段落修复** — `qca_reporter.py` `generate()` 用 `"\n\n".join(sections)` 拼接，数据缺失节返回空字符串导致孤立空段落。添加 `sections = [s for s in sections if s]` 过滤。（工作量: S）
- [ ] **P2-34: DOCX 空解渲染 + 硬编码修复** — `docx_reporter.py`: (a) 空解场景跳过导致静默无输出，需添加 `\top` 等效分支；(b) 标题/表头存在硬编码占位符（`"  "`），需注入本地化字符串。(工作量: M)
- [ ] **P2-35: CI 管线搭建** — 新建 `.github/workflows/test.yml`（`on: [push, pull_request]`），包含 `uv run pytest --cov` + `ruff check` + `mypy`。设置 coverage >80% 阈值。当前仅 deploy.yml，无测试/lint 管线，已导致多次回归。（工作量: M）
- [ ] **P2-36: 报告模块单元测试** — `QCALaTeXReporter`（零测试）、`QCADocxReporter`（零测试）、`validate_qca_output.py`（零测试）。补 >70 个测试，含空解/退化数据处理、各节条件渲染、DOCX 集成。（工作量: L）
- [ ] **P2-37: 统一 report 调用路径** — `cli.py` 直接调用 `QCALaTeXReporter` 而非通过 `api.py` `run_report()`，存在重复逻辑。统一为 api.py 入口，cli.py 仅做薄包装。（工作量: S）

### D. 原有 P2 保留项

- [ ] **P2-1: 数据预分析和描述统计** — 文本长度分布、关键词命中热力图、条件分布直方图 + 偏度警告。(工作量: M)
- [ ] **P2-2: 全流程步进引导 (Stepper)** — 所有页面顶部统一步进指示器：Upload → Calibrate → Analyze → Review。(工作量: M)
- [ ] **P2-3: DataInput 页面拆分** — 拆为 3 个引导步骤，YAML 编辑器默认折叠，初级用户使用表单模式。(工作量: M)
- [ ] **P2-6: 英文文本支持** — 关键词引擎支持空格分词 + 词干提取，英文预置领域，UI 中英切换。(工作量: L)
- [ ] **P2-7: 政策文件分析场景** — "自定义领域"模式，不绑定 5 个预置领域。(工作量: L)
- [ ] **P2-8: 外部 QCA 工具互操作** — 导入 R QCA 包格式模糊集数据，导出 fsQCA 兼容真值表。(工作量: M)
- [ ] **P2-9: 条件间关系检测** — 相关系数矩阵热力图，>0.8 警告，Venn/Upset 图。(工作量: S)
- [ ] **P2-10: 增量分析** — 追加新数据，仅对新增数据校准后重新跑真值表，结果变化对比。(工作量: M)
- [ ] **P2-11: 分析结果版本对比** — 每次运行自动记录快照，版本对比视图，导出分析日志。(工作量: M)
- [ ] **P2-12: 数据密码保护** — 可选会话密码，AES-GCM 加密 localStorage，30 分钟无操作自动锁定。(工作量: M)
- [ ] **P2-13: 离线桌面版** — Electron 封装，预打包 Pyodide + numpy + Python 包。(工作量: XL)
- [ ] **P2-16: 结构化可观测性** — 引入 structlog，PipelineResult 添加 metrics 字段，Worker 请求添加 request_id。(工作量: M)
- [ ] **P2-18: 前端自动化测试** — vitest + @testing-library/react，优先测 QCAPipelineContext reducer + useQCAWorkflow hook。(工作量: L)
- [ ] **P2-23: 多结果分析前端 UI 更新** — multi_outcome.py 已实现，前端 UI 需适配 raw/prototype 双结果对比。(工作量: M)

---

## 统计

| 分组 | 数量 | 优先级 |
|------|------|--------|
| A. 后端/算法优化 | 4 | P2-28 (S) → P2-26 (S) → P2-25 (M) → P2-27 (XL) |
| B. 前端/可视化优化 | 4 | P2-31 (S) → P2-30 (M) → P2-29 (L) → P2-32 (L) |
| C. 报告/DevOps 优化 | 5 | P2-33 (S) → P2-37 (S) → P2-34 (M) → P2-35 (M) → P2-36 (L) |
| D. 原有 P2 保留 | 14 | 按原有优先级 |
| **合计** | **27** | **S: 5 / M: 12 / L: 7 / XL: 3** |

**推荐执行顺序**：先做 S 级快速修复（P2-28/31/33/37/26）→ M 级改进（P2-25/34/35/30）→ L 级集成（P2-29/36/32）→ XL 架构（P2-27）。

---

## 相关文档

- `.wolf/handover.md` — 项目接手状态
- `.wolf/plans/technical_advisory_plan.md` — 技术顾问诊断方案
- `.wolf/plans/package_optimization_plan.md` — 包体优化方案
