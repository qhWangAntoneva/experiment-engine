# Handover — 2026-05-26 Session (P1-8/9 + P2-20/22 + end-of-file-fixer fix)

> 本轮完成 4 项轻量级 TODO + end-of-file-fixer 根因修复。CI 确认为稳定状态。
> 下一次 session 继续 P1 功能需求或 P1-B7/B8。

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| HEAD | `271d45b` — feat: P2-20 + P2-22 — k configurable + --variant for train/robustness |
| 远程 | `origin/master` (已推送) |
| Python 测试 | 532 passed, 1 skipped, 6 xfailed |
| TypeScript build | `npm run build` clean |
| Dev server | `http://127.0.0.1:3000`（必须用 127.0.0.1，不用 localhost） |
| 生产部署 | ✅ 上线 — HTTP 200 |
| CI | ✅ 稳定 — administration:write 问题已在 de01621 修复 |

## 2. 本 Session 完成的工作

### 2.1 end-of-file-fixer 根因修复 (ba36d86)

`JSON.stringify()` 不会在末尾追加换行符。Wolf hook 的 `writeJSON()` 写出的 JSON 文件缺少 trailing newline，导致 pre-commit 的 end-of-file-fixer 每次提交均报错。

**修复**: `.wolf/hooks/shared.js` 中 `writeJSON()` 的两处 `JSON.stringify()` 调用均追加 `+ '\n'`（原子写入路径 + 回退路径）。

### 2.2 CI 失败邮件分析

确认 CI 已稳定：历史失败根因（`administration: write` 非法权限 + 旧版 Pages 部署）均已在前序 commit 中修复。最近 4 次 CI 全部成功。无需改动。

### 2.3 P1-8（隐私声明）+ P1-9（Recent Runs 真实数据） (1186356)

**P1-8**: Dashboard 底部新增隐私声明区块 + "清除所有本地数据"按钮。清除 `qca-settings`、`qca-params`、`qca-bert-model`、`qca-recent-runs`（保留 `qca-language`）。含中英双语 i18n。

**P1-9**: Dashboard Recent Runs 现在从 localStorage (`qca-recent-runs`) 读取真实数据。`QCAPipelineContext` 在 `finishAnalysis`/`finishPrototypeAnalysis` 时写入新记录（最多 20 条）。通过 `recent-runs-updated` 自定义事件实时刷新。

**已知小问题**: `RECENT_RUNS_KEY` 常量在 `Dashboard.tsx` 和 `QCAPipelineContext.tsx` 中重复定义，应提取到共享常量文件。

### 2.4 P2-20（steepness 可配置）+ P2-22（CLI --variant 补全） (271d45b)

**P2-20**: `CalibrationParams` 新增可选字段 `steepness: float | None` (0.1-100.0)。`IndirectCalibration.calibrate()` 读取 `params.steepness if params.steepness is not None else 10.0`。向后兼容——不设置时行为不变。TypeScript 接口已同步。新增测试 `test_calibrate_indirect_custom_steepness`。

**P2-22**: `qca train` 和 `qca robustness` CLI 命令新增 `--variant fsqca|csqca` 选项。`calibrate`/`analyze`/`run` 在更早前已完成。全部 9 个命令中 5 个现支持 --variant。

## 3. 关键提交记录

```
271d45b feat: P2-20 + P2-22 — k configurable + --variant for train/robustness  ← 本次
1186356 feat: P1-8 + P1-9 — Privacy section + Recent Runs from localStorage     ← 本次
ba36d86 fix: add trailing newline to writeJSON output in shared.js              ← 本次
63c9fce chore: update handover + wolf files for session handoff
7ac38d8 feat: P1-B3 + P1-B6 — remove KeywordEntry, refactor domains.py to prototypes
4c0461a chore: re-sync planning docs with actual codebase state (2026-05-26)
de01621 fix: remove invalid administration:write permission from deploy.yml
b8fc27e fix: switch to Actions-based Pages deployment + add .nojekyll
```

## 4. 当前 TODO 状态

| 优先级 | 剩余 | 备注 |
|--------|------|------|
| P0 | **0** | 全部完成 |
| P1 | **9** | P1-BERT 清理 2 项（P1-B7/B8）+ 功能需求 7 项（P1-5/6/7/10/11/12/13） |
| P2 | **21** | 全部未开始 |
| **合计** | **32** | ↓ 从 34 |

**下一步推荐**:
- P1-10（校准参数即时预览，M）— UX 影响大，投入适中
- P1-5（个案级校准结果展示，M）— 用户可查看每条文本的隶属度分数
- P1-B7+B8（模型切换支持 + 性能监控面板）

## 5. 需要了解的重要架构状态

### 评分管道（当前）
```
文本输入 → BertEngine (Transformers.js) → BERT CLS 嵌入
                                               ↓
ConditionDefinition.prototypes → CosineSimilarityEngine → 原始分数 [0,1]
                                               ↓
CalibrationStrategyRegistry → 校准 → 模糊隶属度
                                               ↓
QCA 引擎 → 真值表 → QM 最小化 → 解
```

### 已删除文件（不再存在）
- `keyword_dict.py` — 关键字匹配引擎
- `keyword_io.py` — 关键字导入/导出
- `prototype_similarity.py` — 旧版 bigram Jaccard 相似度
- `KeywordEntry` 类 — 已从 models/qca.py 移除

### 现有领域预置
`domains.py` 包含 5 个领域 × 5 个条件（co_production 为 4 个）的原型文本模板，每个条件 2 个原型（1 正例 + 1 反例），用于 BERT CLS 余弦相似度评分。

## 6. 活跃问题 / 注意事项

| 项目 | 严重程度 | 备注 |
|------|----------|------|
| **CI 稳定性** | Info | deploy.yml 已修复，最近 4 次全部成功 |
| **end-of-file-fixer** | Info | writeJSON() 现已追加 `\n`，新 JSON 文件应通过 pre-commit |
| **RECENT_RUNS_KEY 重复** | Minor | 字符串字面量在 Dashboard.tsx 和 QCAPipelineContext.tsx 中重复，应提取到共享常量文件 |
| **FIXME-28** | 建议 | `TextCase.outcome` 是 `int`，fsQCA 连续型结果应为 `float` |
| **FIXME-32** | 建议 | domains.py 原型预置为硬编码，用户可能希望在线编辑并持久化到 localStorage |

## 7. 快速验证命令

```bash
npm run build              # TypeScript + Vite 构建
uv run pytest --tb=no -q   # Python 测试 (532 passed)
uv run ruff check src/     # 应为干净状态
npm run dev                # 启动开发服务器 (127.0.0.1:3000)
gh run list -b master -l 3 --workflow deploy.yml  # 查看部署状态
```

## 8. 已知注意事项

- **Dev server**: 必须使用 `http://127.0.0.1:3000`，不能使用 `localhost`（Pyodide worker 跨域问题）
- **Worker 类型**: ES 模块 Worker (`{ type: 'module' }`)
- **Pyodide**: CDN 加载 (v0.26.4)，不自托管
- **GitHub Actions 权限**: 仅 `contents/pages/id-token`。`administration` 不存在
- **Python 编码**: 所有 `open()` 调用必须显式指定 `encoding='utf-8'`
- **Python 运行器**: 始终使用 `uv run python`，不要使用裸 `python`
- **RUF001 误报**: domains.py 中的中文标点（，）是合法的原型文本
- **Agent 可靠性**: Agent 声称完成不可信——始终用 `git diff --stat`、Grep、Read 验证变更
- **共享文件竞争**: 修改共享文件的 Agent 必须串行运行

## 9. 未跟踪文件

```
?? .wolf/memory-archive.md    — 归档的旧 session 日志（2026-05-25 之前）
?? experiment-engine/          — 嵌套 git 仓库/旧 worktree。不要 touch。
```
