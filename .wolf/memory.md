# Memory

| 2026-05-28 | Fix Transformers.js 云端推理崩溃: _model() 调用添加 try-catch + 零向量回退，替代 throw new Error 传播到 pipeline 崩溃 | bert-engine.ts | bug-393 logged, TS clean, 532 tests pass | ~200 |
| 2026-05-28 | Fix analyzer.py: solution_consistency/solution_coverage 在 QCAAnalysisResult.solutions 中显示 0.000 — SufficiencyAnalyzer 计算了正确值但保存在 SufficiencyResults.solutions, 未回写到主 solutions 对象 | analyzer.py | 532 tests pass, ALL MATCH verified | ~350 |
| 2026-05-28 | Fix robustness 一直显示 N/A: DataInput.tsx 调用 runFullPipeline 没有传 runRobustness: true，稳健性步骤被跳过 | DataInput.tsx | bug-401 logged | ~50 |

> Active sessions: most recent 2. Older sessions archived to `memory-archive.md`.
| 2026-05-28 | 清理项目过时内容: tmp/ 目录删除 40+ 文件, buglog.json 从 3460 行精简至 67 个实质性 bug, memory.md 从 654 行精简至 6 行, cerebrum.md HEAD 更新至 b914889 | tmp/, .wolf/buglog.json, .wolf/memory.md, .wolf/cerebrum.md, .wolf/anatomy.md | done | ~100 |

## Session: 2026-05-27 01:50

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 01:53 | Edited src/pages/DataInput.tsx | CSS: runRobustness | ~103 |
