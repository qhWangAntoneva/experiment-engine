# QCA Analysis Tool — Project Status (2026-05-27)

> BERT embeddings → fuzzy calibration → QCA truth table → solutions.

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| HEAD | `5a6a00d` — fix: Pyodide pydantic 缺失修复 |
| 分支 | `master` |
| 测试 | 532 passed, 1 skipped, 6 xfailed |
| TS build | clean (0 errors) |
| 本地改动 | (已推送干净) |

## 2. 本轮已完成 (2026-05-27 Session)

| 任务 | 描述 | 状态 | Review |
|------|------|------|--------|
| **Use Template Bug** | DataInput.tsx 忽略 state.conditionSet → 添加 useEffect 注入 | **已修复** | TS build clean |
| **P2-33** | LaTeX 空段落过滤 — qca_reporter.py generate() 空字符串过滤 | **已推送** | ACCEPTED: 532 passed |
| **P2-37** | 统一 report 调用路径 — cli.py → api.run_report() | **已推送** | ACCEPTED: console路径保留 |
| **P2-26** | 消除 FuzzySetData 废弃别名 — 17个文件全部替换 | **已推送** | ACCEPTED: grep零命中 |
| **P2-31** | Plotly 显示模式栏 — 4组件 displayModeBar hover | **已推送** | ACCEPTED: TS clean |
| **P2-28** | validate_qca_output.py 增强 — 形状/outcome/质量评分 | **已推送** | ACCEPTED: 532 passed |
| **Bug: Pyodide pydantic 缺失** | 加载30条样本数据因 pydantic 未预加载崩溃；(1) `pyodide.worker.ts` REQUIRED_PACKAGES 添加 `'pydantic'`；(2) `config.py` 将 `from pydantic import ValidationError` 改为函数内懒加载。验证: Python import OK, TS 0 errors, 532 passed。 | **已修复 (已推送)** | `5a6a00d` |

## 3. TODO.md 重构

三位专业架构师分析报告整合为 TODO.md 新结构:
- **A. 后端/算法优化** (4项) — P2-25~28 (P2-28已完成)
- **B. 前端/可视化优化** (4项) — P2-29~32 (P2-31已完成)
- **C. 报告/DevOps 优化** (5项) — P2-33~37 (P2-33/37已完成)
- **D. 原有P2保留** (14项)

## 4. 快速验证

```bash
PYTHONIOENCODING=utf-8 uv run python validate_qca_output.py   # 验证所有域（含新增强检查）
PYTHONIOENCODING=utf-8 uv run pytest --tb=no -q               # 532 passed
npm run dev                                                    # 前端 127.0.0.1:3000
```

## 5. 推荐下一步

S级任务已全部完成。推荐继续按 TODO.md 顺序推进：
1. **P2-25**: 统一 CSV 读取路径 (M)
2. **P2-34**: DOCX 空解渲染 + 硬编码修复 (M)
3. **P2-35**: CI 管线搭建 (M)
4. **P2-30**: 可视化错误边界 (M)
5. 后续 L 级: P2-29 (可视化桥接) / P2-36 (报告测试) / P2-32 (联动)

## 相关文档

- `TODO.md` — 完整任务列表（27项，含本轮完成5项）
- `.wolf/plans/technical_advisory_plan.md` — 技术顾问诊断方案
- `.wolf/plans/package_optimization_plan.md` — 包体优化方案
