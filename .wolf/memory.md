# Memory

> Active sessions: 2026-05-25 onwards. Older sessions archived to `memory-archive.md`.

| 2026-05-26 | 完成部署 + 验收: 修复 3 critical (Python tar.gz 加载, 404 SPA 回退, io/__init__.py ImportError guard), 4-agent expert team 审查部署架构, 推送到 master, 启用 GitHub Pages, Reviewer 验收全部 5 端点 200 PASS。部署至 https://qhWangAntoneva.github.io/experiment-engine/ | pyodide.worker.ts, io/__init__.py, main.tsx, 404.html, vite-env.d.ts, handover.md, memory.md | 部署成功, git push 已触发 workflow, Pages 已启用 | ~32000 |
| 2026-05-26 | FIXER agent 声称完成但 REVIEWER 发现零改动 (agent 虚构完成再次确认) → 亲自修复 3 critical fixes + npm run build pass + git push | pyodide.worker.ts, io/__init__.py, main.tsx, 404.html | 3 fixes applied and verified | ~18000 |
| 2026-05-26 | QCA 计算管道全面验证: 运行 515 pytest (全 PASS) + 48 自定义验证 (全 PASS)。覆盖 5 个步骤: 测试套件、端到端 Lipset 黄金标准、校准算法(4 种)、QM 布尔最小化(已知答案对比)、数值稳定性(NaN/Inf/极端值)。发现 1 个 bug: ConditionDefinition 模型缺少 keywords 字段，build_default_conditions() 传入的关键词被 Pydantic 静默丢弃(5 个域 200+ 关键词实际无效)。 | tmp/verify_pipeline.py, test_qca_core.py, calibrator.py, domains.py, qca.py | 48/48 PASS, bug identified | ~16000 |
| 2026-05-26 | npm run build → tsc -b 报错: Cannot find module CDN URL → 在 vite-env.d.ts 添加 declare module | vite-env.d.ts | build clean, dist 输出已验证 | ~2000 |
| 2026-05-26 | 浏览器验证: Playwright 12 步通过, "加载引擎" flash-back 已修复, engine 加载至 ready | verify-load-engine.mjs, screenshots | 11/12 PASS, 1 脚本 issue (BERT btn disabled 非 bug) | ~25000 |
| 2026-05-26 | 创建 DEPLOY-CHECKLIST.md: 全面部署验证清单, 6 章节 76 项检查(预构建/构建/SPA 404/GH Pages 配置/部署后浏览器测试/边缘用例)。关键发现: site/404.html 是 MkDocs 产物,不会被部署; SPA BrowserRouter 需要专属 404.html 处理直接 URL 访问。清单包含快速运行脚本。 | DEPLOY-CHECKLIST.md, anatomy.md, memory.md | 清单已创建,等待部署前验证 | ~6000 |
| 2026-05-26 | 第二轮修复 + handover 更新: 第一轮经典 worker 方案导致 "Cannot use import statement outside a module" → 正确方案(保持模块 Worker + 动态 import() 加载 pyodide.mjs)。3-agent 验证 26/26 PASS。更新 handover 至最新状态。 | pyodide.worker.ts, pyodide.ts, vite.config.ts, handover.md, memory.md | 2 次要修复 (stale comment + 类型定义 gap), tsc clean | ~80000 |
| 2026-05-26 | 修复"加载引擎"按钮闪回 bug: 4-agent expert team 诊断 → root cause (module worker + importScripts 不兼容, TypeError) → fix (模块 Worker 保持 + import() 加载 pyodide.mjs + Dashboard error state + resolveOne routing + worker cleanup) → explorer+fixer+reviewer 验证(全部 PASS) → 3 次要问题已清理。Dev server 运行在 127.0.0.1:3000。 | pyodide.ts, Dashboard.tsx, vite.config.ts, translations.ts, Dashboard.css, pyodide.worker.ts | 1 critical bug fixed (bug-214), 3 minor issues cleaned, tsc clean | ~120000 |
| 2026-05-25 | 完整 session: E2E 全功能测试 (4 agent 并行, 85 项, 10 Phase, PASS 70/FAIL 5) → 定位 localhost 代理陷阱 (Clash 拦截, 修复为 127.0.0.1) → fixer 修复 5 缺陷 → reviewer 审核 (发现 1 遗漏已补修) → tsc 零错误。核心 Pipeline/BERT/QCA 链路全部验证通过。 | DataInput.tsx, Settings.tsx, translations.ts, vite.config.ts, handover.md, buglog.json, memory.md, e2e-test-plan.md | 5 bugs fixed, handover updated, @~400k total session tokens |
| 2026-05-25 | Phase 4 UI 对接完成 — 3 个文件、2 次提交、6 FIXME 清除。useQCAWorkflow (initBert+runEmbedCalibrate) → DataInput (BERT 按钮+状态) + Settings (模型选择器)。code-review 发现 3 bugs (initBert error 卡 stage、finishEmbedding 未调用、stale prototypeFuzzyData) 并已修复。Build 通过。 | useQCAWorkflow.ts, DataInput.tsx, Settings.tsx | 2 commits: 3df7e57, eba4e1f | ~8000 |
| 2026-05-25 | Designed BERT Prototype similarity algorithm spec: mean pooling > CLS, centroid aggregation > max-similarity, softmax-with-temperature formula as primary (Eq.1), normalized-difference as fallback (Eq.3), full pipeline pseudocode, edge cases, Prototype Theory + fsQCA theoretical justification | .wolf/bert-prototype-algorithm-spec.md | Written, ~27KB, no implementation code | ~12000 |
| 2026-05-25 | Implemented CosineSimilarityEngine + 52 comprehensive unit tests: softmax(tau)/diff scoring, centroid/max aggregation, weighted prototypes, 8 edge cases, numerical stability (overflow-safe softmax, cos clipping, L2 normalization), input validation. 577 total tests pass (52 new), ruff clean | src/experiment_engine/text_calibration/cosine_similarity.py, tests/test_cosine_similarity.py, src/experiment_engine/text_calibration/__init__.py | Created: engine ~4.8k tok, tests ~12k tok; updated __init__.py exports | ~7000 |

> Chronological action log. Hooks and AI append to this file automatically.

| 2026-05-25 | UX tester: Created comprehensive E2E test plan (45 tests, 6 phases) with PASS/FAIL criteria. Focus on engine loading (known bug: Load Engine reverts immediately), i18n, settings persistence, data input/calibration, full pipeline, error handling/edge cases. Includes test data CSV samples and execution order. | .wolf/e2e-test-plan.md | Written: 342 lines, 6 phases, 45 test scenarios | ~1200 |
| 2026-05-25 | P1-31: Verified build + committed raw-prototype contrast view (pre-existing implementation). TODO.md stats updated. | qca.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts, Results.tsx, Results.css, PipelineStatus.tsx, TODO.md | npm build clean, 0 errors | ~800 |
| 2026-05-24 | Reconciled TODO/FIXME/HACK after 3-agent requirement change review: fixed P1-15/16/17 done status, unchecked P2-20 (k=10 still hardcoded), reordered P2 section, corrected all stats tables | TODO.md, FIXME.md, HACK.md | 3 stats tables corrected, 4 checkbox fixes, 2 contradictions resolved, 1 section reordered | ~600 |
| 2026-05-25 | BERT 架构决策定案：Explore Agent 深度复审 bert-vs-keyword-analysis.md + 技术顾问设计浏览器端双 Worker 架构 + 评审者 16 项批判 + 定量对比（86x WASM CPU 推理差距、5.9x 冷启动差距）+ 最终决议 BERT 作为 CLI 辅助工具不做主引擎 | .wolf/bert-vs-keyword-analysis.md, TODO.md, HACK.md, cerebrum.md | 文档已更新，P1-32/33 范围缩小为纯 Python CLI，P2-25/26 添加条件门控 | ~35000 |
> Older sessions (pre-2026-05-25) archived to `memory-archive.md` on 2026-05-26.
## Session: 2026-05-25 09:02

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 09:08 | Edited TODO.md | 7→4 lines | ~26 |
| 09:08 | Edited TODO.md | removed 3 lines | ~11 |
| 09:08 | Edited TODO.md | 6→6 lines | ~70 |
| 09:09 | Edited TODO.md | removed 8 lines | ~2 |
| 09:09 | Edited TODO.md | removed 9 lines | ~7 |
| 09:09 | Edited TODO.md | removed 18 lines | ~1 |
| 09:09 | Edited TODO.md | 4→3 lines | ~26 |
| 09:10 | Edited TODO.md | 6→6 lines | ~70 |
| 09:10 | Edited TODO.md | inline fix | ~11 |
| 09:10 | Edited TODO.md | inline fix | ~14 |
| 09:11 | Edited roadmap/experiment-engine-roadmap.json | inline fix | ~10 |
| 09:11 | Removed all BERT content from TODO.md, handover.md, roadmap: P1-32/33 + P2-25/26 + P2-14 removed. Stats recalculated (P1: 23→10 remaining, P2: 28→23 remaining). | TODO.md, handover.md, experiment-engine-roadmap.json | 33 tasks remaining | ~3000 |
| 09:14 | Session end: 11 writes across 2 files (TODO.md, experiment-engine-roadmap.json) | 3 reads | ~2910 tok |

## Session: 2026-05-25 12:46

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 13:35 | Edited TODO.md | expanded (+40 lines) | ~643 |
| 13:35 | Edited TODO.md | inline fix | ~17 |
| 13:36 | Edited TODO.md | 15→17 lines | ~128 |
| 13:36 | Edited roadmap/experiment-engine-roadmap.json | 18→19 lines | ~175 |
| 13:36 | Edited roadmap/experiment-engine-roadmap.json | expanded (+160 lines) | ~1935 |
| 13:37 | Edited roadmap/experiment-engine-roadmap.json | expanded (+14 lines) | ~113 |
| 13:37 | Edited roadmap/experiment-engine-roadmap.json | 15→16 lines | ~122 |
| 13:42 | BERT+Prototype architecture refactoring plan finalized: TODO.md + roadmap.json + cerebrum.md | 3 files | 5-phase implementation sequence designed | ~12000 tok |
| 13:43 | Session end: 7 writes across 2 files (TODO.md, experiment-engine-roadmap.json) | 42 reads | ~25591 tok |
| 13:44 | Edited package.json | 1→2 lines | ~18 |
| 13:44 | Created src/types/bert.ts | — | ~675 |
| 13:46 | Session end: 9 writes across 4 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts) | 43 reads | ~26959 tok |
| 13:47 | Created src/services/bert-cache.ts | — | ~3612 |
| 13:48 | Created src/experiment_engine/text_calibration/cosine_similarity.py | — | ~4701 |
| 13:49 | Session end: 11 writes across 6 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 46 reads | ~35444 tok |
| 13:49 | Created src/services/bert-engine.ts | — | ~2378 |
| 13:50 | created bert-cache.ts — IndexedDB cache for BERT prototype + text embeddings | src/services/bert-cache.ts | build passes | ~288 tok |
| 13:50 | Edited src/services/bert-engine.ts | modified for() | ~173 |
| 13:51 | Session end: 13 writes across 7 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 47 reads | ~38283 tok |
| 13:51 | Created BertEngine service at src/services/bert-engine.ts | bert-engine.ts | TS type-check passes; lazy-load pipeline, attention-masked mean pooling, L2 norm, embedding cache, batch processing | ~3200 |
| 13:52 | Created tests/test_cosine_similarity.py | — | ~12116 |
| 13:53 | Edited tests/test_cosine_similarity.py | modified test_opposite_with_both_softmax_near_zero() | ~241 |
| 13:53 | Edited tests/test_cosine_similarity.py | modified test_diff_formula_symmetric() | ~312 |
| 13:53 | Edited src/types/bert.ts | 7→5 lines | ~42 |
| 13:53 | Edited src/services/bert-engine.ts | 2→1 lines | ~18 |
| 13:53 | Edited src/experiment_engine/text_calibration/cosine_similarity.py | 8→7 lines | ~120 |
| 13:54 | Edited src/experiment_engine/text_calibration/cosine_similarity.py | modified _normalize_rows() | ~125 |
| 13:54 | Edited src/services/bert-engine.ts | 3→2 lines | ~22 |
| 13:54 | Edited src/services/bert-engine.ts | modified if() | ~27 |
| 13:54 | Edited src/services/bert-engine.ts | inline fix | ~16 |
| 13:54 | Edited src/services/bert-engine.ts | 2→5 lines | ~81 |
| 13:54 | Edited src/services/bert-engine.ts | modified _truncateText() | ~38 |
| 13:54 | Edited src/types/bert.ts | 5→4 lines | ~33 |
| 13:54 | Session end: 26 writes across 8 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 48 reads | ~54674 tok |
| 13:55 | Edited src/experiment_engine/text_calibration/cosine_similarity.py | inline fix | ~13 |
| 13:55 | Edited src/experiment_engine/text_calibration/cosine_similarity.py | 4→3 lines | ~43 |
| 13:55 | Edited tests/test_cosine_similarity.py | inline fix | ~22 |
| 13:56 | Edited src/experiment_engine/text_calibration/cosine_similarity.py | 7→7 lines | ~88 |
| 13:59 | Edited src/experiment_engine/text_calibration/__init__.py | 7→10 lines | ~92 |
| 13:59 | Edited src/experiment_engine/text_calibration/__init__.py | 7→8 lines | ~63 |
| 14:04 | Session end: 32 writes across 9 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 50 reads | ~71865 tok |
| 14:21 | Edited src/experiment_engine/models/qca.py | modified ScoringSource() | ~159 |
| 14:21 | Edited src/experiment_engine/models/qca.py | modified ConditionDefinition() | ~379 |
| 14:21 | Edited src/experiment_engine/models/qca.py | 2→2 lines | ~31 |
| 14:22 | Edited src/types/qca.ts | "keyword" → "prototype" | ~12 |
| 14:22 | Edited src/types/qca.ts | 13→12 lines | ~102 |
| 14:22 | Edited src/i18n/translations.ts | expanded (+8 lines) | ~78 |
| 14:22 | Edited src/i18n/translations.ts | expanded (+8 lines) | ~88 |
| 14:22 | Edited src/i18n/translations.ts | expanded (+8 lines) | ~121 |
| 14:23 | Session end: 40 writes across 12 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 50 reads | ~72835 tok |
| 14:24 | Session end: 40 writes across 12 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 50 reads | ~78275 tok |
| 14:27 | Edited src/types/qca.ts | 4→3 lines | ~69 |
| 14:27 | Edited src/types/qca.ts | 7→4 lines | ~81 |
| 14:27 | Session end: 42 writes across 12 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 54 reads | ~90822 tok |
| 14:27 | Edited src/pages/DataInput.tsx | CSS: prototype_embeddings, embedding_model | ~177 |
| 14:27 | Edited src/pages/DataInput.tsx | CSS: prototype_embeddings, embedding_model | ~128 |
| 14:27 | Edited src/pages/DataInput.tsx | added optional chaining | ~134 |
| 14:27 | Edited src/pages/DataInput.tsx | added optional chaining | ~69 |
| 14:28 | Edited src/pages/DataInput.tsx | added optional chaining | ~273 |
| 14:28 | Edited src/pages/DataInput.tsx | CSS: FIXME-BERT | ~42 |
| 14:28 | Edited src/pages/DataInput.tsx | CSS: FIXME-BERT | ~55 |
| 14:28 | Edited src/pages/DataInput.tsx | CSS: FIXME-BERT | ~52 |
| 14:28 | Created src/i18n/translations.ts | — | ~8236 |
| 14:28 | Edited src/hooks/useQCAWorkflow.ts | 2→3 lines | ~42 |
| 14:28 | Edited src/hooks/useQCAWorkflow.ts | 2→3 lines | ~49 |
| 14:29 | Session end: 53 writes across 14 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 54 reads | ~100079 tok |
| 2026-05-25 | Removed 21 keyword-dict-specific strings from TranslationDict interface/zh/en (dataInput: importExportTitle, importCsvJson, exportCsv, exporting, importHelp, imported, kw, calibrationMode, importedDict, importedDictNoOutcome, dictImportError, exportDictError, noDictLoaded, exportedDict; settings: exportDictSection, exportDictHelp, exportDictNoConditionSet, exportDictBtn, exportDictExporting, exportDictError, exportedDict). Updated calibration_direction descriptions (zh: remove '关键词', en: 'keyword scores' -> 'raw scores'). Added bert_model setting field to zh/en translations. All tsc checks pass. | src/i18n/translations.ts, .wolf/anatomy.md | Clean removal, no TS errors | ~1000 |
| 14:30 | Session end: 53 writes across 14 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 54 reads | ~100079 tok |
| 15:29 | Session end: 53 writes across 14 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 54 reads | ~100079 tok |
| 15:49 | Session end: 53 writes across 14 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 54 reads | ~100079 tok |

## Session: 2026-05-25 15:57

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 16:02 | Edited tests/test_keyword_io.py | modified test_basic_csv_import() | ~55 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_weight_validation() | ~35 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_duplicate_keyword_rejected() | ~37 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_missing_columns() | ~34 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_empty_values_rejected() | ~36 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_default_weight_when_missing() | ~38 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_invalid_weight_string() | ~36 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_basic_json_import() | ~56 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_json_with_outcome() | ~35 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_duplicate_condition_name_rejected() | ~39 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_duplicate_keyword_in_condition_rejected() | ~41 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_weight_out_of_range_rejected() | ~38 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_missing_condition_name_rejected() | ~39 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_export_csv_roundtrip() | ~56 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_export_csv_includes_notes() | ~37 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_export_json_roundtrip() | ~57 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_export_json_without_outcome() | ~38 |
| 16:04 | Edited src/experiment_engine/pyodide_handlers.py | modified handle_embed_calibrate() | ~1518 |
| 16:04 | Edited tests/test_integration.py | modified _make_valid_condition_set() | ~514 |
| 16:04 | Edited tests/test_qca_core.py | modified test_csqca_calibrator_forces_crisp_set() | ~787 |
| 16:04 | Edited tests/test_qca_core.py | modified test_load_from_conditions() | ~192 |
| 16:04 | Edited tests/test_prototype_similarity.py | modified test_keyword_mode_unchanged() | ~599 |
| 16:04 | Edited src/experiment_engine/pyodide_handlers.py | 6→8 lines | ~102 |
| 16:04 | Created src/experiment_engine/text_calibration/calibrator.py | — | ~4838 |
| 16:05 | Edited src/experiment_engine/pyodide_handlers.py | modified enumerate() | ~248 |
| 16:05 | Edited src/experiment_engine/pyodide_handlers.py | inline fix | ~20 |
| 16:05 | Edited src/experiment_engine/pyodide_handlers.py | inline fix | ~8 |
| 2026-05-25 | Added handle_embed_calibrate to pyodide_handlers.py — integrates CosineSimilarityEngine into Pyodide handler pipeline. Loads texts with pre-computed BERT embeddings + condition set JSON, builds condition_prototypes/prototype_embeddings dicts, computes raw cosine-similarity scores via engine, applies calibration via CalibrationStrategyRegistry, outputs MembershipData JSON. Handles edge cases: empty texts, missing prototype_embeddings, missing calibration_params. Ruff clean. | src/experiment_engine/pyodide_handlers.py | 131 lines added. Note: _condition_from_dict does not deserialize prototype_embeddings — handler extracts from raw JSON dict as workaround. | ~3000 |
| 16:06 | Session end: 27 writes across 6 files (test_keyword_io.py, pyodide_handlers.py, test_integration.py, test_qca_core.py, test_prototype_similarity.py) | 12 reads | ~43596 tok |
| 16:07 | Edited src/experiment_engine/text_calibration/condition.py | 19→19 lines | ~214 |
| 16:07 | Edited src/experiment_engine/text_calibration/condition.py | 13→10 lines | ~136 |
| 16:08 | Edited tests/test_prototype_similarity.py | modified test_prototype_calibration_produces_fuzzy_data() | ~1426 |
| 16:08 | Edited src/experiment_engine/text_calibration/condition.py | 13→10 lines | ~123 |
| 16:08 | Edited tests/test_prototype_similarity.py | modified test_prototype_calibration_with_outcome() | ~758 |
| 16:09 | Edited tests/test_prototype_similarity.py | modified test_prototype_calibration_without_embeddings_zeroes_scores() | ~522 |
| 16:09 | Edited tests/test_prototype_similarity.py | modified test_prototype_calibration_without_embeddings_zeroes_scores() | ~96 |
| 16:10 | Edited src/experiment_engine/text_calibration/condition.py | modified build() | ~23 |
| 16:11 | Edited src/experiment_engine/text_calibration/condition.py | modified _condition_from_dict() | ~30 |
| 16:11 | Phase 2: refactored calibrator.py — removed ChineseKeywordDictionary and PrototypeSimilarityEngine, integrated CosineSimilarityEngine, added text_embeddings/prototype_embeddings params to process/process_with_outcome/calibrate_one, rewrote _precompute_kw_context as _precompute_scores | src/experiment_engine/text_calibration/calibrator.py, tests/test_prototype_similarity.py | 513 passed, 21 skipped, 6 xfailed | ~3600 |
| 16:12 | Session end: 36 writes across 7 files (test_keyword_io.py, pyodide_handlers.py, test_integration.py, test_qca_core.py, test_prototype_similarity.py) | 12 reads | ~50310 tok |
| 16:13 | Session end: 36 writes across 7 files (test_keyword_io.py, pyodide_handlers.py, test_integration.py, test_qca_core.py, test_prototype_similarity.py) | 12 reads | ~50310 tok |
| 16:16 | Session end: 36 writes across 7 files (test_keyword_io.py, pyodide_handlers.py, test_integration.py, test_qca_core.py, test_prototype_similarity.py) | 13 reads | ~80937 tok |
| 16:24 | Session end: 36 writes across 7 files (test_keyword_io.py, pyodide_handlers.py, test_integration.py, test_qca_core.py, test_prototype_similarity.py) | 13 reads | ~80937 tok |

## Session: 2026-05-25 16:30

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 16:48 | Edited src/types/qca.ts | expanded (+21 lines) | ~991 |
| 16:48 | Edited src/services/pyodide.worker.ts | added 1 import(s) | ~46 |
| 16:48 | Edited src/services/pyodide.worker.ts | 4→5 lines | ~58 |
| 16:48 | Edited src/services/pyodide.worker.ts | expanded (+15 lines) | ~204 |
| 16:49 | Edited src/services/pyodide.worker.ts | added error handling | ~1054 |
| 16:49 | Edited src/services/pyodide.ts | 15→16 lines | ~102 |
| 16:49 | Edited src/services/pyodide.ts | modified initBert() | ~795 |
| 16:50 | Edited src/types/qca.ts | 6→8 lines | ~182 |
| 16:50 | Edited src/types/qca.ts | 1→5 lines | ~89 |
| 16:55 | Phase 3 — Worker protocol extension for BERT+Prototype | src/types/qca.ts (+BERT msg types), src/services/pyodide.worker.ts (+5 BERT handlers), src/services/pyodide.ts (+5 bridge methods) | npm run build passes, 662 lines delta | ~1800 |
| 16:55 | Session end: 9 writes across 3 files (qca.ts, pyodide.worker.ts, pyodide.ts) | 11 reads | ~3521 tok |
| 16:55 | Edited src/types/qca.ts | 18→22 lines | ~127 |
| 16:56 | Edited src/types/qca.ts | expanded (+6 lines) | ~399 |
| 16:56 | Edited src/store/QCAPipelineContext.tsx | CSS: status, embeddings | ~268 |
| 16:56 | Edited src/store/QCAPipelineContext.tsx | added nullish coalescing | ~149 |
| 16:57 | Edited src/types/qca.ts | 4→5 lines | ~38 |
| 16:57 | Edited src/types/qca.ts | 3→4 lines | ~22 |
| 16:57 | Edited src/store/QCAPipelineContext.tsx | CSS: bertEmbeddingsReady | ~25 |
| 16:57 | Edited src/store/QCAPipelineContext.tsx | 4→9 lines | ~105 |
| 16:57 | Edited src/store/QCAPipelineContext.tsx | expanded (+26 lines) | ~362 |
| 16:57 | Edited src/store/QCAPipelineContext.tsx | CSS: setBertStatus | ~56 |
| 16:57 | Edited src/hooks/useQCAWorkflow.ts | 7→8 lines | ~56 |
| 16:57 | Edited src/hooks/useQCAWorkflow.ts | expanded (+9 lines) | ~104 |
| 16:58 | Edited src/hooks/useQCAWorkflow.ts | 16→21 lines | ~125 |
| 16:58 | Edited src/hooks/useQCAWorkflow.ts | added error handling | ~968 |
| 16:58 | Edited src/pages/DataInput.tsx | 8→10 lines | ~72 |
| 16:58 | Edited src/pages/DataInput.tsx | 2→6 lines | ~99 |
| 16:58 | Edited src/pages/DataInput.tsx | added 1 condition(s) | ~650 |
| 16:59 | Edited src/pages/DataInput.tsx | inline fix | ~27 |
| 16:59 | Edited src/experiment_engine/models/qca.py | modified ScoringSource() | ~88 |
| 16:59 | Edited src/pages/DataInput.tsx | modified t() | ~965 |
| 16:59 | Edited src/types/index.ts | 2→1 lines | ~7 |
| 16:59 | Edited src/experiment_engine/text_calibration/__init__.py | removed 14 lines | ~17 |
| 16:59 | Edited src/experiment_engine/models/__init__.py | 3→2 lines | ~21 |
| 16:59 | Edited src/pages/Settings.tsx | modified t() | ~796 |
| 16:59 | Edited src/types/qca.ts | removed 7 lines | ~10 |
| 17:00 | Edited src/experiment_engine/text_calibration/__init__.py | reduced (-7 lines) | ~130 |
| 17:00 | Edited src/experiment_engine/models/__init__.py | 2→1 lines | ~6 |
| 17:00 | Edited src/experiment_engine/pyodide_handlers.py | removed 87 lines | ~6 |
| 17:00 | Edited src/services/pyodide.worker.ts | reduced (-11 lines) | ~38 |
| 17:00 | Edited src/services/pyodide.worker.ts | removed 47 lines | ~23 |
| 17:00 | Edited src/services/pyodide.ts | removed 51 lines | ~22 |
| 17:00 | Edited src/pyodide/engine.ts | 2→1 lines | ~23 |
| 17:00 | Edited src/experiment_engine/text_calibration/training.py | expanded (+11 lines) | ~378 |
| 17:01 | Edited src/experiment_engine/text_calibration/training.py | 6→5 lines | ~63 |
| 17:01 | Edited src/experiment_engine/text_calibration/training.py | modified _compute_raw_scores() | ~208 |
| 17:01 | Edited src/types/qca.ts | removed 3 lines | ~7 |
| 17:01 | Edited src/types/qca.ts | removed 5 lines | ~10 |
| 17:01 | Edited src/i18n/translations.ts | expanded (+15 lines) | ~145 |
| 17:02 | Edited src/i18n/translations.ts | expanded (+15 lines) | ~171 |
| 17:02 | Edited src/i18n/translations.ts | expanded (+15 lines) | ~241 |
| 17:03 | Edited src/pages/Settings.tsx | 4→4 lines | ~63 |
| 17:03 | Edited src/experiment_engine/models/__init__.py | 2→3 lines | ~39 |
| 17:03 | Edited src/experiment_engine/models/__init__.py | 4→5 lines | ~40 |
| 17:03 | Edited src/pages/Settings.tsx | 2→2 lines | ~47 |
| 17:04 | Edited src/i18n/translations.ts | 4→7 lines | ~36 |
| 17:04 | Edited src/hooks/useQCAWorkflow.ts | removed 26 lines | ~10 |
| 17:04 | Edited src/hooks/useQCAWorkflow.ts | 5→3 lines | ~19 |
| 17:04 | Edited src/i18n/translations.ts | 2→5 lines | ~37 |
| 17:04 | Edited src/i18n/translations.ts | 2→5 lines | ~50 |
| 17:04 | Edited src/hooks/useQCAWorkflow.ts | removed 20 lines | ~34 |
| 17:05 | Edited src/hooks/useQCAWorkflow.ts | expanded (+16 lines) | ~184 |
| 17:07 | Edited src/hooks/useQCAWorkflow.ts | modified useCallback() | ~229 |
| 17:08 | Edited src/hooks/useQCAWorkflow.ts | added 1 import(s) | ~41 |
| 17:10 | Edited src/pages/DataInput.tsx | 8→5 lines | ~27 |
| 17:12 | Session end: 63 writes across 14 files (qca.ts, pyodide.worker.ts, pyodide.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts) | 24 reads | ~50801 tok |
| 17:14 | Edited src/hooks/useQCAWorkflow.ts | removed 28 lines | ~6 |
| 17:14 | Edited src/hooks/useQCAWorkflow.ts | 4→2 lines | ~12 |
| 17:14 | Edited src/pages/DataInput.tsx | — | ~0 |
| 17:14 | Edited src/pages/Settings.tsx | — | ~0 |
| 17:15 | Edited src/pages/Settings.tsx | 3→2 lines | ~32 |
| 17:17 | Fix Phase 4/5 merge conflict: removed dangling importKeywords/exportKeywords from useQCAWorkflow.ts (callbacks + return obj), removed FIXME-BERT keyword import/export section from DataInput.tsx, removed Export Keyword Dictionary UI + unused useQCAWorkflow import from Settings.tsx | useQCAWorkflow.ts, DataInput.tsx, Settings.tsx | npm build passes | ~2000 |
| 17:20 | Edited src/experiment_engine/text_calibration/condition.py | inline fix | ~16 |
| 17:39 | Edited src/services/pyodide.ts | expanded (+6 lines) | ~143 |
| 17:41 | Edited src/hooks/useQCAWorkflow.ts | reduced (-11 lines) | ~20 |
| 17:41 | Edited src/hooks/useQCAWorkflow.ts | removed 17 lines | ~11 |
| 17:41 | Edited src/hooks/useQCAWorkflow.ts | removed 26 lines | ~10 |
| 17:42 | Session end: 73 writes across 15 files (qca.ts, pyodide.worker.ts, pyodide.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts) | 33 reads | ~69138 tok |
| 17:42 | Edited src/hooks/useQCAWorkflow.ts | 4→2 lines | ~12 |
| 17:43 | Edited src/pages/DataInput.tsx | CSS: sum, c | ~45 |
| 17:44 | Fixed remaining TS build errors: added explicit types to reduce() callback params in DataInput.tsx line 426 | src/pages/DataInput.tsx | build passes (31s, 0 errors) | ~50 |
| 17:45 | Phase 5: Cleanup old keyword code — deleted keyword_dict.py, keyword_io.py, prototype_similarity.py + tests. Removed KEYWORD/HYBRID from ScoringSource. Updated calibrator/similarity to PROTOTYPE-only. Cleaned pyodide handlers, worker, bridge, hook, and UI of keyword methods. Build passes, 515 tests pass. | src/experiment_engine/text_calibration/*, src/experiment_engine/models/qca.py, src/types/qca.ts, src/services/*.ts, src/hooks/useQCAWorkflow.ts, src/pages/{DataInput,Settings}.tsx, tests/* | 26 files, +2425/-675 | ~1200 tok |
| 17:46 | Session end: 75 writes across 15 files (qca.ts, pyodide.worker.ts, pyodide.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts) | 33 reads | ~70957 tok |
| 17:52 | Session end: 75 writes across 15 files (qca.ts, pyodide.worker.ts, pyodide.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts) | 33 reads | ~70957 tok |
| 18:13 | Session end: 75 writes across 15 files (qca.ts, pyodide.worker.ts, pyodide.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts) | 33 reads | ~78614 tok |

## Session: 2026-05-25 18:22

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 18:27 | Edited src/hooks/useQCAWorkflow.ts | 6→7 lines | ~38 |
| 18:27 | Edited src/hooks/useQCAWorkflow.ts | expanded (+9 lines) | ~109 |
| 18:27 | Edited src/hooks/useQCAWorkflow.ts | 3→8 lines | ~46 |
| 18:28 | Edited src/hooks/useQCAWorkflow.ts | added error handling | ~186 |
| 18:28 | Edited src/hooks/useQCAWorkflow.ts | added error handling | ~816 |
| 18:28 | Edited src/hooks/useQCAWorkflow.ts | 2→4 lines | ~24 |
| 18:29 | Phase A: add initBert() + runEmbedCalibrate() to useQCAWorkflow hook | src/hooks/useQCAWorkflow.ts | 6 edits, tsc clean | ~400 |
| 18:31 | Session end: 6 writes across 1 files (useQCAWorkflow.ts) | 5 reads | ~30457 tok |
| 18:36 | Edited src/hooks/useQCAWorkflow.ts | modified catch() | ~80 |
| 18:36 | Edited src/hooks/useQCAWorkflow.ts | 16→18 lines | ~144 |
| 18:36 | Edited src/hooks/useQCAWorkflow.ts | 3→3 lines | ~33 |
| 18:39 | Session end: 9 writes across 1 files (useQCAWorkflow.ts) | 9 reads | ~40113 tok |
| 18:40 | Edited src/pages/DataInput.tsx | 5→7 lines | ~37 |
| 18:40 | Edited src/pages/DataInput.tsx | 2→4 lines | ~73 |
| 18:40 | Edited src/pages/DataInput.tsx | 4→2 lines | ~10 |
| 18:40 | Edited src/pages/DataInput.tsx | 3→3 lines | ~69 |
| 18:40 | Edited src/pages/DataInput.tsx | inline fix | ~22 |
| 18:41 | Edited src/pages/DataInput.tsx | 4→4 lines | ~70 |
| 18:41 | Edited src/pages/DataInput.tsx | 2→1 lines | ~23 |
| 18:41 | Edited src/pages/DataInput.tsx | 2→2 lines | ~67 |
| 18:41 | Edited src/pages/DataInput.tsx | 2→2 lines | ~76 |
| 18:42 | Edited src/pages/DataInput.tsx | added error handling | ~386 |
| 18:42 | Edited src/pages/DataInput.tsx | expanded (+48 lines) | ~635 |
| 18:42 | Edited src/pages/Settings.tsx | added error handling | ~193 |
| 18:42 | Edited src/pages/Settings.tsx | modified t() | ~763 |
| 18:42 | Edited src/pages/DataInput.tsx | inline fix | ~24 |
| 2026-05-25 16:00 | Phase C: Added BERT model selector and status display to Settings page — model select dropdown, bertStatus/bertMessage display, load button with useQCAWorkflow.initBert integration. TypeScript build passes. | src/pages/Settings.tsx | Modified: added BERT section in Engine Status card, bertModel state, handleLoadBert callback | ~500 |
| 18:44 | Phase B: BERT controls integration — added initBert/runEmbedCalibrate to hook destructuring, BERT state (isBertLoading/isEmbedding), BERT handlers (handleLoadBert/handleBertCalibrate), BERT UI section after calibration mode selector, cleaned 2 FIXME-BERT comments, updated 4 keyword→prototypes refs, updated button disabled logic | src/pages/DataInput.tsx | ts compilation clean, 4 FIXME-BERT comments remain | ~800 |
| 18:46 | Edited src/pages/DataInput.tsx | modified if() | ~71 |
| 18:46 | Edited src/pages/DataInput.tsx | 6→5 lines | ~72 |
| 18:46 | Edited src/pages/DataInput.tsx | 2→1 lines | ~40 |
| 18:46 | Edited src/pages/DataInput.tsx | 2→1 lines | ~47 |
| 18:49 | Session end: 27 writes across 3 files (useQCAWorkflow.ts, DataInput.tsx, Settings.tsx) | 9 reads | ~44426 tok |
| 18:52 | Session end: 27 writes across 3 files (useQCAWorkflow.ts, DataInput.tsx, Settings.tsx) | 9 reads | ~44426 tok |
| 18:56 | Session end: 27 writes across 3 files (useQCAWorkflow.ts, DataInput.tsx, Settings.tsx) | 9 reads | ~44426 tok |
| 19:54 | Session end: 27 writes across 3 files (useQCAWorkflow.ts, DataInput.tsx, Settings.tsx) | 9 reads | ~44426 tok |
| 19:58 | designqc: captured 6 screenshots (25KB, ~15000 tok) | /, /Dashboard, /DataInput, /Results, /Settings | ready for eval | ~0 |
| 20:00 | Session end: 27 writes across 3 files (useQCAWorkflow.ts, DataInput.tsx, Settings.tsx) | 9 reads | ~44426 tok |
| 20:01 | Session end: 27 writes across 3 files (useQCAWorkflow.ts, DataInput.tsx, Settings.tsx) | 9 reads | ~44426 tok |

## Session: 2026-05-25 20:01

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 20:44 | Debugged browser hang: killed 8 zombie Vite/node processes (PIDs 38952,34576,27884,16868,19328,33628 + 2 orphan node.exe) occupying ports 3000-3002, started fresh Vite on port 3000. All endpoints respond HTTP 200. | .wolf/memory.md, .wolf/buglog.json | FIXED — app now serves at http://localhost:3000 | ~2000 |
| 21:40 | Edited src/hooks/usePyodide.ts | 3→3 lines | ~27 |
| 21:48 | Edited vite.config.ts | 4→5 lines | ~19 |
| 21:55 | Edited vite.config.ts | 5→5 lines | ~21 |
| 21:57 | Session end: 3 writes across 2 files (usePyodide.ts, vite.config.ts) | 54 reads | ~59859 tok |
| 21:57 | Session end: 3 writes across 2 files (usePyodide.ts, vite.config.ts) | 55 reads | ~59859 tok |
| 22:18 | Session end: 3 writes across 2 files (usePyodide.ts, vite.config.ts) | 56 reads | ~59859 tok |
| 22:24 | Session end: 3 writes across 2 files (usePyodide.ts, vite.config.ts) | 62 reads | ~67642 tok |
| 22:27 | Edited src/i18n/translations.ts | expanded (+13 lines) | ~164 |
| 22:27 | Edited src/i18n/translations.ts | expanded (+13 lines) | ~165 |
| 22:27 | Edited src/i18n/translations.ts | expanded (+13 lines) | ~222 |
| 22:28 | Edited src/pages/DataInput.tsx | modified t() | ~588 |
| 22:28 | Edited src/pages/Settings.tsx | 20 → 10 | ~4 |
| 22:28 | Edited src/pages/Settings.tsx | 4→4 lines | ~84 |
| 22:28 | Edited src/pages/Settings.tsx | modified t() | ~216 |
| 22:28 | Edited src/pages/Settings.tsx | inline fix | ~25 |
| 22:28 | Edited src/pages/Settings.tsx | modified t() | ~131 |
| 22:29 | Edited src/pages/Settings.tsx | inline fix | ~19 |
| 22:29 | Edited src/pages/Settings.tsx | added error handling | ~151 |
| 22:29 | Edited src/pages/Settings.tsx | added error handling | ~160 |
| 22:29 | Edited src/pages/Settings.tsx | added 2 condition(s) | ~308 |
| 2026-05-25 | E2E bug fixes: Bug 1 (BERT i18n)→DataInput.tsx+Settings.tsx, Bug 2 (localStorage read-on-mount)→Settings.tsx, Bug 3 (BERT model persistence)→Settings.tsx, Bug 4 (keyword export stub)→Settings.tsx, Bug 5 (N-Cut max:20→10)→Settings.tsx. 14 new i18n keys added to translations.ts. tsc --noEmit PASS | translations.ts, DataInput.tsx, Settings.tsx | All 5 bugs fixed, type-safe | ~8000 |
| 22:32 | Edited src/pages/DataInput.tsx | added 2 condition(s) | ~324 |
| 22:34 | Session end: 17 writes across 5 files (usePyodide.ts, vite.config.ts, translations.ts, DataInput.tsx, Settings.tsx) | 62 reads | ~70866 tok |
| 22:48 | Session end: 17 writes across 5 files (usePyodide.ts, vite.config.ts, translations.ts, DataInput.tsx, Settings.tsx) | 62 reads | ~70866 tok |

## Session: 2026-05-25 23:06

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 23:27 | Edited vite.config.ts | workers() → importScripts() | ~50 |
| 23:27 | Edited src/services/pyodide.ts | 4→3 lines | ~26 |
| 23:28 | Edited src/i18n/translations.ts | 4→5 lines | ~36 |
| 23:28 | Edited src/i18n/translations.ts | 3→4 lines | ~32 |
| 23:28 | Edited src/i18n/translations.ts | 4→5 lines | ~43 |
| 23:28 | Edited src/i18n/translations.ts | 3→4 lines | ~40 |
| 23:28 | Edited src/pages/Dashboard.tsx | modified t() | ~79 |
| 23:28 | Edited src/pages/Dashboard.tsx | 2→2 lines | ~54 |
| 23:28 | Edited src/pages/Dashboard.tsx | modified t() | ~187 |
| 23:28 | Edited src/services/pyodide.ts | modified switch() | ~296 |
| 23:28 | Edited src/services/pyodide.ts | added 1 condition(s) | ~450 |
| 23:34 | Edited src/pages/Dashboard.tsx | 5→4 lines | ~72 |
| 23:34 | Edited src/services/pyodide.worker.ts | 2→2 lines | ~46 |
| 23:34 | Edited src/pages/Dashboard.css | 3→7 lines | ~38 |
| 23:36 | Session end: 14 writes across 6 files (vite.config.ts, pyodide.ts, translations.ts, Dashboard.tsx, pyodide.worker.ts) | 17 reads | ~51104 tok |
| 23:52 | Edited vite.config.ts | importScripts() → import() | ~31 |
| 23:52 | Edited src/services/pyodide.ts | 3→4 lines | ~34 |
| 23:52 | Edited src/services/pyodide.worker.ts | 9→9 lines | ~126 |
| 23:52 | Edited src/services/pyodide.worker.ts | 2→3 lines | ~68 |
| 23:58 | Edited src/i18n/translations.ts | 2→3 lines | ~22 |
| 23:58 | Edited src/i18n/translations.ts | 2→3 lines | ~22 |
| 23:58 | Edited vite.config.ts | inline fix | ~24 |
| 23:59 | Session end: 21 writes across 6 files (vite.config.ts, pyodide.ts, translations.ts, Dashboard.tsx, pyodide.worker.ts) | 21 reads | ~51989 tok |
| 00:16 | Session end: 21 writes across 6 files (vite.config.ts, pyodide.ts, translations.ts, Dashboard.tsx, pyodide.worker.ts) | 21 reads | ~51989 tok |

## Session: 2026-05-25 00:16

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 00:23 | Created tmp/verify-load-engine.mjs | — | ~2084 |
| 00:28 | Edited tmp/verify-load-engine.mjs | inline fix | ~22 |
| 00:31 | Session end: 2 writes across 1 files (verify-load-engine.mjs) | 7 reads | ~2256 tok |
| 00:41 | Edited src/vite-env.d.ts | modified loadPyodide() | ~65 |
| 00:43 | Session end: 3 writes across 2 files (verify-load-engine.mjs, vite-env.d.ts) | 36 reads | ~42832 tok |
| 00:43 | Created DEPLOY-CHECKLIST.md | — | ~5434 |
| 00:44 | Session end: 4 writes across 3 files (verify-load-engine.mjs, vite-env.d.ts, DEPLOY-CHECKLIST.md) | 36 reads | ~48654 tok |
| 00:45 | Session end: 4 writes across 3 files (verify-load-engine.mjs, vite-env.d.ts, DEPLOY-CHECKLIST.md) | 36 reads | ~48654 tok |
| 01:04 | Edited src/services/pyodide.worker.ts | added optional chaining | ~454 |
| 01:05 | Created public/404.html | — | ~278 |
| 01:05 | Edited src/main.tsx | 5→5 lines | ~54 |
| 01:05 | Edited src/main.tsx | CSS: replace | ~442 |
| 01:05 | Edited src/main.tsx | 3→4 lines | ~29 |
| 01:05 | Edited src/experiment_engine/io/__init__.py | expanded (+10 lines) | ~225 |
| 2026-05-26 | Fix 3 critical deployment blockers: (1) Worker now fetches experiment_engine.tar.gz instead of non-existent /pyodide-modules.json, extracts via tarfile. (2) Created public/404.html + RedirectRestorer component in main.tsx for SPA routing fallback. (3) io/__init__.py db imports wrapped in try/except ImportError. Build passes clean. | pyodide.worker.ts, main.tsx, 404.html, io/__init__.py | tsc + vite build clean, verified tar.gz extraction code and spa-redirect in dist bundles | ~8000 |
| 01:10 | Session end: 10 writes across 7 files (verify-load-engine.mjs, vite-env.d.ts, DEPLOY-CHECKLIST.md, pyodide.worker.ts, 404.html) | 38 reads | ~51079 tok |
| 01:11 | Session end: 10 writes across 7 files (verify-load-engine.mjs, vite-env.d.ts, DEPLOY-CHECKLIST.md, pyodide.worker.ts, 404.html) | 38 reads | ~51079 tok |
| 01:21 | Session end: 10 writes across 7 files (verify-load-engine.mjs, vite-env.d.ts, DEPLOY-CHECKLIST.md, pyodide.worker.ts, 404.html) | 38 reads | ~51079 tok |
| 01:26 | Session end: 10 writes across 7 files (verify-load-engine.mjs, vite-env.d.ts, DEPLOY-CHECKLIST.md, pyodide.worker.ts, 404.html) | 38 reads | ~51079 tok |
| 01:32 | Session end: 10 writes across 7 files (verify-load-engine.mjs, vite-env.d.ts, DEPLOY-CHECKLIST.md, pyodide.worker.ts, 404.html) | 38 reads | ~51079 tok |
| 01:42 | Session end: 10 writes across 7 files (verify-load-engine.mjs, vite-env.d.ts, DEPLOY-CHECKLIST.md, pyodide.worker.ts, 404.html) | 38 reads | ~51079 tok |
| 01:48 | Session end: 10 writes across 7 files (verify-load-engine.mjs, vite-env.d.ts, DEPLOY-CHECKLIST.md, pyodide.worker.ts, 404.html) | 38 reads | ~51079 tok |

## Session: 2026-05-25 02:00

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 02:05 | Edited src/pyodide/types.ts | 1→4 lines | ~87 |
| 02:05 | Edited src/experiment_engine/core/__init__.py | expanded (+8 lines) | ~150 |
| 02:05 | Edited src/experiment_engine/pyodide_handlers.py | expanded (+11 lines) | ~482 |
| 02:06 | Edited package.json | 27→30 lines | ~193 |
| 02:07 | Edited index.html | expanded (+26 lines) | ~485 |
| 02:07 | Edited src/services/pyodide.worker.ts | modified Integrity() | ~479 |
| 02:07 | Edited src/services/pyodide.worker.ts | expanded (+6 lines) | ~92 |
| 18:06 | ARCH cleanup: deleted dead src/pyodide/engine.ts, fixed broken re-export in types.ts, wrapped parallel imports in core/__init__.py with ImportError guard, wrapped QCALaTeXReporter import in pyodide_handlers.py | engine.ts, types.ts, core/__init__.py, pyodide_handlers.py | tsc clean, 522 tests passing | ~300 |
| 02:07 | Edited src/services/pyodide.worker.ts | added error handling | ~449 |
| 02:07 | Edited src/services/bert-engine.ts | modified Integrity() | ~383 |
| 02:09 | Session end: 9 writes across 7 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 12 reads | ~18989 tok |
| 02:10 | Edited package.json | inline fix | ~8 |
| 02:20 | SEC-1/2/3 fixes: protobufjs 6.11.6 → 7.5.9 via overrides (9 CVEs resolved), CSP meta tag added to index.html, CDN SRI comments + Pyodide version check in workers | package.json, package-lock.json, index.html, pyodide.worker.ts, bert-engine.ts | npm audit: 6→2 vulns, build passes | ~1200 |
| 02:14 | Session end: 10 writes across 7 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 13 reads | ~19482 tok |
| 02:21 | Session end: 10 writes across 7 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 13 reads | ~21539 tok |
| 02:22 | Edited index.html | 17→22 lines | ~335 |
| 02:22 | Edited src/experiment_engine/core/__init__.py | modified __getattr__() | ~306 |
| 02:22 | Edited src/experiment_engine/pyodide_handlers.py | 6→5 lines | ~73 |
| 02:23 | Session end: 13 writes across 7 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 13 reads | ~22762 tok |
| 02:26 | Edited src/experiment_engine/core/__init__.py | modified __getattr__() | ~105 |
| 02:26 | Created src/experiment_engine/core/__init__.py | — | ~368 |
| 02:27 | Session end: 15 writes across 7 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 13 reads | ~23302 tok |
| 02:28 | Session end: 15 writes across 7 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 13 reads | ~23308 tok |
| 02:30 | __getattr__ fix verification — code review + build/tsc/pytest (522) all pass | src/experiment_engine/core/__init__.py | PASS | |  |  |  | ~ |
| 02:30 | __getattr__ fix verification — code review + build/tsc/pytest (522) all pass | src/experiment_engine/core/__init__.py | PASS | ~5 |
| 02:30 | Session end: 15 writes across 7 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 13 reads | ~23308 tok |
| 02:38 | Session end: 15 writes across 7 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 13 reads | ~23308 tok |
| 02:40 | Created tmp/generate_test_data.py | — | ~4821 |
| 02:42 | Edited tmp/generate_test_data.py | 4→4 lines | ~48 |
| 02:42 | Created tmp/verify_pipeline.py | — | ~7631 |
| 02:42 | Edited tmp/verify_pipeline.py | inline fix | ~7 |
| 02:43 | Session end: 19 writes across 9 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 31 reads | ~51967 tok |
| 02:43 | Edited tmp/verify_pipeline.py | added 1 import(s) | ~177 |
| 02:43 | Edited tmp/verify_pipeline.py | 3→4 lines | ~52 |
| 02:43 | Created 4 test data files for QCA text analysis tool (3 CSVs + 1 YAML condition set) | tmp/test_dataset_1_standard.csv, tmp/test_dataset_2_edge_cases.csv, tmp/test_dataset_3_small_n.csv, tmp/test_condition_set.yaml | All files verified: correct row counts, UTF-8 encoding, YAML loads via project module | ~500 |
| 02:44 | Edited tmp/verify_pipeline.py | added 1 import(s) | ~62 |
| 02:44 | Session end: 22 writes across 9 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 31 reads | ~52258 tok |
| 02:44 | Edited tmp/verify_pipeline.py | inline fix | ~19 |
| 02:44 | Edited tmp/verify_pipeline.py | 20→21 lines | ~243 |
| 02:47 | Edited tmp/verify_pipeline.py | modified catch_warnings() | ~742 |
| 02:47 | Edited tmp/verify_pipeline.py | modified term() | ~193 |
| 02:49 | Session end: 26 writes across 9 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 31 reads | ~53455 tok |
| 02:57 | Edited src/experiment_engine/models/qca.py | 2→3 lines | ~55 |
| 02:57 | Edited src/experiment_engine/qca_engine/advanced/robustness.py | modified startswith() | ~365 |
| 02:57 | Edited src/experiment_engine/qca_engine/advanced/robustness.py | added 1 import(s) | ~21 |
| 02:57 | Edited src/experiment_engine/text_calibration/strategies.py | expanded (+15 lines) | ~281 |
| 02:58 | Created tests/test_robustness.py | — | ~2353 |
| 02:59 | Created tests/test_robustness.py | — | ~2150 |
| 03:00 | Edited tests/test_robustness.py | modified _make_fuzzy() | ~616 |
| 03:01 | Created tests/test_robustness.py | — | ~2586 |
| 03:01 | Edited tests/test_robustness.py | modified test_calibration_sensitivity_backward_compat() | ~44 |
| 03:02 | Session end: 35 writes across 13 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 31 reads | ~61926 tok |
| 03:06 | Session end: 35 writes across 13 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 31 reads | ~65573 tok |
| 10:54 | session wrap-up: 安全修复(3)+架构清理(3)+算法验证(3-agent team)+算法bug修复(4). 538 tests. HANDOVER updated. | 21 files changed | all fixes verified by reviewer | ~80000 |
| 10:54 | Session end: 35 writes across 13 files (types.ts, __init__.py, pyodide_handlers.py, package.json, index.html) | 31 reads | ~65573 tok |

## Session: 2026-05-26 10:55

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 11:04 | Edited src/experiment_engine/core/__init__.py | added 1 import(s) | ~132 |
| 11:04 | Edited src/experiment_engine/pyodide_handlers.py | 5→5 lines | ~62 |
| 11:04 | Edited tests/test_robustness.py | 3→2 lines | ~16 |
| 11:04 | Edited tests/test_robustness.py | inline fix | ~15 |
| 11:04 | Edited tests/test_robustness.py | inline fix | ~16 |
| 11:05 | Session end: 5 writes across 3 files (__init__.py, pyodide_handlers.py, test_robustness.py) | 3 reads | ~9663 tok |
| 11:15 | Session end: 5 writes across 3 files (__init__.py, pyodide_handlers.py, test_robustness.py) | 5 reads | ~14758 tok |
| 11:17 | Edited .gitignore | expanded (+9 lines) | ~45 |
| 11:18 | Session end: 6 writes across 4 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore) | 5 reads | ~14806 tok |
| 11:21 | Session end: 6 writes across 4 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore) | 5 reads | ~14806 tok |
| 11:37 | Edited src/i18n/translations.ts | inline fix | ~22 |
| 11:37 | Edited src/i18n/translations.ts | "zh" → "en" | ~11 |
| 11:37 | Edited src/i18n/translations.ts | 2→3 lines | ~21 |
| 11:37 | Edited src/i18n/translations.ts | 2→3 lines | ~38 |
| 11:37 | Edited src/i18n/translations.ts | 2→3 lines | ~78 |
| 11:37 | Edited src/pages/Dashboard.tsx | 2→3 lines | ~42 |
| 11:37 | Edited src/pages/Dashboard.css | CSS: line-height, max-width | ~68 |
| 11:39 | Session end: 13 writes across 7 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore, translations.ts) | 16 reads | ~28078 tok |
| 11:43 | Session end: 13 writes across 7 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore, translations.ts) | 16 reads | ~28078 tok |
| 11:45 | Session end: 13 writes across 7 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore, translations.ts) | 16 reads | ~28078 tok |
| 12:00 | Session end: 13 writes across 7 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore, translations.ts) | 17 reads | ~28078 tok |
| 12:10 | Session end: 13 writes across 7 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore, translations.ts) | 18 reads | ~28078 tok |
| 12:16 | Session end: 13 writes across 7 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore, translations.ts) | 18 reads | ~28078 tok |
| 12:17 | Edited index.html | "zh-CN" → "en" | ~5 |
| 12:37 | Edited .github/workflows/deploy.yml | 146→143 lines | ~1806 |
| 12:39 | Created public/.nojekyll | — | ~0 |
| 12:45 | Session end: 16 writes across 10 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore, translations.ts) | 25 reads | ~41220 tok |
| 14:16 | Edited .github/workflows/deploy.yml | 4→5 lines | ~41 |
| 14:17 | Session end: 17 writes across 10 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore, translations.ts) | 25 reads | ~41261 tok |
| 14:22 | Session end: 17 writes across 10 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore, translations.ts) | 25 reads | ~41261 tok |
| 14:25 | Session end: 17 writes across 10 files (__init__.py, pyodide_handlers.py, test_robustness.py, .gitignore, translations.ts) | 25 reads | ~41261 tok |

## Session: 2026-05-26 14:25

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:54 | Edited .github/workflows/deploy.yml | — | ~0 |
| 14:58 | Fixed deploy pipeline: removed invalid administration:write permission. Push-triggered workflow now succeeds (50s, 14/14 steps). Site live at HTTP 200. | .github/workflows/deploy.yml, buglog | deployment fixed | ~3000 |
| 14:59 | Session end: 1 writes across 1 files (deploy.yml) | 2 reads | ~1806 tok |
| 15:52 | Session end: 1 writes across 1 files (deploy.yml) | 2 reads | ~1806 tok |

## Session: 2026-05-26 15:53

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 15:53 | 上下文优化: memory.md 1408→496行 (归档 916行至 memory-archive.md, -65%); cerebrum.md Do-Not-Repeat 10→5条 (合并 6条 agent 虚构条目) | memory.md, memory-archive.md, cerebrum.md, anatomy.md | ~50K tokens saved from context window | ~3000 |
| 15:53 | CLAUDE.md 迁移: 全局 105行采集规则 → 6条独特规则补充到 National-Policy-Database/CLAUDE.md，全局 CLAUDE.md 精简为 22行通用规则 | ~/.claude/CLAUDE.md, National-Policy-Database/CLAUDE.md | 全局 CLAUDE.md: 105→22行 (-79%); QCA session 不再加载无关采集规则 | ~2000 |
| 16:06 | Edited ../National-Policy-Database/CLAUDE.md | expanded (+6 lines) | ~171 |
| 16:06 | Created ../.claude/CLAUDE.md | — | ~212 |
| 16:06 | Edited ../National-Policy-Database/CLAUDE.md | inline fix | ~15 |
| 16:07 | Session end: 3 writes across 1 files (CLAUDE.md) | 2 reads | ~427 tok |

## Session: 2026-05-26 16:07

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 16:16 | Created HACK.md | — | ~1849 |
| 16:16 | Created FIXME.md | — | ~3123 |
| 16:16 | Created TODO.md | — | ~3464 |
| 16:16 | Re-synced HACK.md with actual codebase: 6 resolved (HACK-1,14,15,16,17,18), updated HACK-13 desc, stats 10/18 resolved | HACK.md, .wolf/anatomy.md | done | ~800 |
| 16:17 | Re-synced TODO.md with actual codebase state: P0-BERT all done (12/12), P1-BERT 4 remaining, P1 functional 9 remaining, P2 23 remaining. Total 36 remaining. | TODO.md | written full file | ~300 tok |
| 16:17 | Re-synced FIXME.md with actual codebase state: 8 resolved items moved to strikethrough, 6 MOOT items removed (keyword-related files deleted), 3 open items remain (all 🟢 suggestions). Updated FIXME-32 description for prototype presets. | FIXME.md | 0 🔴 + 0 🟡 + 3 🟢 remaining, 5 MOOT removed | ~500 |
| 16:19 | Updated cerebrum.md: fixed domain model description (removed keyword references, updated to prototype/CosineSimilarityEngine), fixed file table, updated FIXME.md stats in quick-start, fixed Bigram knowledge entry | cerebrum.md, anatomy.md | 5 edits applied | ~100 |
| 2026-05-26 14:00 | Rewrote cerebrum.md to reflect actual BERT+Prototype codebase state: keyword matching removed, cosine_similarity.py is primary, updated architecture/sections 2-5/9-11, new work order | .wolf/cerebrum.md | complete, 420 lines | ~12K chars |
| 16:20 | Codebase audit + 4-agent parallel dispatch: coordinated TODO/FIXME/HACK/cerebrum resync. Reviewer launched in background. | TODO.md, FIXME.md, HACK.md, cerebrum.md, memory.md | 4/4 agent writes verified, reviewer pending | ~3000 |
| 16:22 | Session end: 3 writes across 3 files (HACK.md, FIXME.md, TODO.md) | 4 reads | ~15441 tok |
| 16:26 | Session end: 3 writes across 3 files (HACK.md, FIXME.md, TODO.md) | 4 reads | ~15441 tok |
| 16:34 | Session end: 3 writes across 3 files (HACK.md, FIXME.md, TODO.md) | 13 reads | ~37576 tok |
| 16:35 | Edited src/experiment_engine/cli.py | modified items() | ~114 |
| 16:35 | Step 1f: Updated CLI list_conditions to display prototype counts (n+/n-) instead of keyword counts | src/experiment_engine/cli.py | success | ~50 |
| 16:35 | Session end: 4 writes across 4 files (HACK.md, FIXME.md, TODO.md, cli.py) | 13 reads | ~38428 tok |
| 16:35 | Created src/experiment_engine/text_calibration/domains.py | — | ~4022 |
| 16:37 | P1-B3: Refactored domains.py from keyword presets to prototype text templates across all 5 domains. Each condition now has 2 ConceptPrototype entries (positive/negative) instead of KeywordEntry lists. | domains.py | OK, all 5 domains verified | ~3500 |
| 16:37 | Session end: 5 writes across 5 files (HACK.md, FIXME.md, TODO.md, cli.py, domains.py) | 13 reads | ~42450 tok |
| 16:37 | Edited src/experiment_engine/models/qca.py | removed 16 lines | ~1 |
| 16:37 | Edited src/experiment_engine/models/qca.py | removed 2 lines | ~1 |
| 16:38 | Edited src/experiment_engine/models/__init__.py | removed 2 lines | ~1 |
| 16:38 | Edited src/experiment_engine/models/__init__.py | removed 2 lines | ~1 |
| 16:38 | P1-B6 steps 2a-2b: Removed KeywordEntry class and keywords field from ConditionDefinition in qca.py, also removed re-exports from __init__.py | src/experiment_engine/models/qca.py, src/experiment_engine/models/__init__.py | Verified — no remaining KeywordEntry references, keywords field returns False | ~50 |
| 16:39 | Session end: 9 writes across 7 files (HACK.md, FIXME.md, TODO.md, cli.py, domains.py) | 13 reads | ~42419 tok |
| 16:39 | Edited src/experiment_engine/text_calibration/condition.py | 2→1 lines | ~16 |
| 16:39 | Edited src/experiment_engine/text_calibration/condition.py | 3→1 lines | ~16 |
| 16:39 | Edited src/experiment_engine/text_calibration/condition.py | removed 7 lines | ~7 |
| 16:39 | Edited src/experiment_engine/text_calibration/condition.py | modified scoring() | ~50 |
| 16:39 | Edited src/experiment_engine/text_calibration/condition.py | modified _condition_to_dict() | ~102 |
| 16:40 | Edited tests/test_integration.py | 5→5 lines | ~84 |
| 16:41 | P1-B6 steps 2c-2d: removed KeywordEntry from models/__init__.py (linter already removed import/__all__) + removed all keyword residual code from condition.py (add_keyword, _kw_to_dict, _hybrid_*_weight, keywords serialization) + fixed test_list_conditions assertion (keywords->prototypes) — 531 tests pass | models/__init__.py, condition.py, test_integration.py | success | ~0 |
| 16:42 | Session end: 15 writes across 9 files (HACK.md, FIXME.md, TODO.md, cli.py, domains.py) | 14 reads | ~42694 tok |
| 16:46 | Edited TODO.md | inline fix | ~35 |
| 16:46 | Edited TODO.md | inline fix | ~56 |
| 16:46 | Edited TODO.md | inline fix | ~18 |
| 16:46 | Edited TODO.md | 36 → 34 | ~6 |
| 16:46 | Edited TODO.md | 4→3 lines | ~23 |
| 16:47 | Edited pyproject.toml | "src/experiment_engine/tex" → "src/experiment_engine/tex" | ~26 |
