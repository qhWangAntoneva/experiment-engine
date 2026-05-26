# Memory

> Active sessions: most recent 2. Older sessions (before 2026-05-26 19:10) archived to `memory-archive.md`.

| 2026-05-26 | P1-5 + P1-10: CaseMembershipTable (sort/search/filter/expand, color-coded) + CalibrationPreview (Plotly dual histogram, JS calibration, i18n). P2-20: configurable steepness. P2-22: --variant for train/robustness CLI. P1-8 + P1-9: Privacy section + Clear Data + Recent Runs from localStorage. P1-B7/B8 plan designed. Handover updated. | CalibrationPreview.tsx, CaseMembershipTable.tsx, Results.tsx/Results.css, Settings.tsx/Settings.css, Dashboard.tsx/Dashboard.css, QCAPipelineContext.tsx, cli.py, strategies.py, qca.py, qca.ts, translations.ts | 532 tests pass, build clean | ~25000 |
| 2026-05-26 | Cleaned up .wolf/HANDOVER.md: removed outdated session-specific content, handover framing, commit history, subagent workflow docs. Updated HEAD ref to 60fa11e, refreshed untracked files list. Retained architecture summary, active issues, verification commands, TODO status. | .wolf/HANDOVER.md | n/a | ~200 |
| 2026-05-26 | Design QC: screenshots for all routes captured. Default language finalized as English (detectLanguage always 'en', index.html lang="en"). FIXME.md + HACK.md cleaned (removed resolved/moot entries). Memory contextual optimization: old sessions archived to memory-archive.md. | translations.ts, index.html, FIXME.md, HACK.md, memory.md, memory-archive.md, cerebrum.md | context budget reduced | ~5000 |

> Chronological action log.

## Session: 2026-05-26 19:10

- P1-10: CalibrationPreview component with Plotly dual histogram + JS calibration + i18n keys (zh+en). Integrated into Settings page.
- P1-5: CaseMembershipTable with sort/search/filter/expand + color-coded membership scores. Integrated Cases tab into Results page.
- P2-20: Added steepness field to CalibrationParams, updated IndirectCalibration, TS interface, test (532 pass)
- P2-22: Added --variant flag to train and robustness CLI commands
- P1-8 + P1-9: Privacy section + Clear Data button, Recent Runs from localStorage, run persistence in QCAPipelineContext
- Reviewer found 2 bugs in CaseMembershipTable (hardcoded string "no text", missing i18n key) -- fixed
- TODO.md stats updated (P1-5/8/9/10, P2-20/22 marked done)
- P1-B7/B8 plan designed by Plan agent for next session
- Handover updated
| ~15000 tok |

## Session: 2026-05-26 20:11

- Design QC: captured screenshots of all routes (/, /Dashboard, /DataInput, /Results, /Settings) -- 2 runs
- i18n language switcher confirmed working; language toggle tested (zh<->en)
- Default language finalized as English: detectLanguage() always returns 'en', index.html lang="en"
- FIXME.md cleaned: removed 20 resolved + 5 MOOT entries, kept FIXME-28 and FIXME-32
- HACK.md cleaned: removed 10 resolved entries, kept 8 active, trimmed descriptions
- Memory contextual optimization: archived old session logs to memory-archive.md
| ~5000 tok |
| 20:29 | Session end: 6 writes across 4 files (translations.ts, index.html, FIXME.md, HACK.md) | 10 reads | ~15898 tok |
| 20:30 | Created TODO.md | — | ~1757 |
| 20:31 | Cleaned TODO.md: collapsed P0-BERT to summary, removed commit hashes from all done items, removed fsQCA/csQCA requirement table, removed deprecated P1-34, updated 推进顺序 to reflect current state. File went from ~3300→~2200 tokens (-33%). Stats verified: P0=0, P1=7, P2=21. | TODO.md | done | ~2200 |
| 20:31 | Session end: 7 writes across 5 files (translations.ts, index.html, FIXME.md, HACK.md, TODO.md) | 10 reads | ~17780 tok |
| 20:32 | 5 agent 并行清理过时文档: memory.md (-95%), FIXME.md (-83%), HACK.md (-66%), HANDOVER.md (-38%), TODO.md (-31%) | HANDOVER.md, TODO.md, memory.md, FIXME.md, HACK.md, memory-archive.md | 全部完成 | ~3000 |
| 20:32 | Session end: 7 writes across 5 files (translations.ts, index.html, FIXME.md, HACK.md, TODO.md) | 10 reads | ~17780 tok |
| 20:36 | Session end: 7 writes across 5 files (translations.ts, index.html, FIXME.md, HACK.md, TODO.md) | 10 reads | ~17780 tok |
| 20:37 | Session end: 7 writes across 5 files (translations.ts, index.html, FIXME.md, HACK.md, TODO.md) | 10 reads | ~17780 tok |

## Session: 2026-05-26 20:37

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
