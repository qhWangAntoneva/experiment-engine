# Handover — 2026-05-26 Session (planning docs re-sync + P1-B3/P1-B6 cleanup)

> 规划文档已与代码库同步。KeywordEntry 已完全移除。P0-BERT 全部完成。
> 下一次 session 直接进入 P1 功能需求或 P1-B7/B8。

---

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| 分支 | `master` |
| HEAD | `7ac38d8` — feat: P1-B3 + P1-B6 — remove KeywordEntry, refactor domains.py to prototypes |
| 远程 | `origin/master` (已推送) |
| Python 测试 | 531 passed, 1 skipped, 6 xfailed |
| TypeScript build | `npm run build` clean |
| Dev server | `http://127.0.0.1:3000`（必须用 127.0.0.1，不用 localhost） |
| 生产部署 | ✅ 上线 — HTTP 200 |
| Pages 状态 | `"built"` (workflow-based) |

## 2. 本 Session 完成的工作

### 2.1 规划文档与代码库重新同步 ✅

**问题**: TODO.md 将 P0-BERT（12 项任务）标记为 0%，但代码库实际完成约 70-80%。FIXME.md/HACK.md 引用了 6 个已删除文件（keyword_dict.py 等）。cerebrum.md 架构描述仍为旧版关键字匹配系统。

**修复** (`4c0461a`):
- **TODO.md**: 标记 P0-BERT 12/12 完成，P1-BERT 4/8 完成，P1-31 完成。重新统计：52→36→34 项剩余
- **FIXME.md**: 标记 8 项已解决（FIXME-23/24/25/26/27/29/30/31），移除 6 项 MOOT（已删除文件），剩余 3 项（全部为建议）
- **HACK.md**: 标记 6 项已解决（HACK-1/14/15/16/17/18），更新 HACK-13 描述，剩余 8/18 活跃
- **cerebrum.md**: 更新架构图、第 0 节统计、工作顺序、Do-Not-Repeat、决策日志。修复审查发现的 6 项不一致

**审查**: Reviewer agent 验证全部 7 项检查通过，发现并修复 cerebrum.md 快速入门部分 6 项陈旧条目。

### 2.2 P1-B3 + P1-B6：KeywordEntry 移除与 domains.py 重构 ✅

**P1-B3 — domains.py 重构**:
- 将所有 5 个域的关键词预置替换为原型文本模板
- 每个条件现在有 2 个原型：1 个正例（is_member=1）+ 1 个反例（is_member=0）
- 为 BERT 余弦相似度评分提供方向性信号

**P1-B6 — KeywordEntry 移除**:
- 从 `models/qca.py` 中移除 `KeywordEntry` 类 + `ConditionDefinition.keywords` 字段
- 清理 `models/__init__.py` 导入和 `__all__` 导出
- 从 `condition.py` 中移除死代码：`add_keyword()`、`_kw_to_dict()`、`hybrid_keyword_weight`、`hybrid_prototype_weight`
- 从 `pyproject.toml` 中移除过时的 keyword_dict.py per-file-ignore，新增 domains.py RUF001 条目
- 修复 `test_list_conditions`：将 `"keywords"` 断言改为 `"prototypes"`
- 代码库中 `KeywordEntry` 引用数量：**零**

**执行方式**: 8 个 agent 通过 2 个阶段派遣（1 plan + 4 fixer + 1 reviewer）。仅当有共享文件时串行执行阶段（P1-B3 先执行，P1-B6 后执行依赖 P1-B3）。每阶段内部并行执行。

### 2.3 Wolf 文件更新

- `handover.md` — 本文件（完整重写）
- `memory.md` — 追加 session 记录
- `cerebrum.md` — 更新第 0 节、第 9 节、第 11 节

## 3. 关键提交记录

```
7ac38d8 feat: P1-B3 + P1-B6 — remove KeywordEntry, refactor domains.py to prototypes  ← 本次
4c0461a chore: re-sync planning docs with actual codebase state (2026-05-26)           ← 本次
de01621 fix: remove invalid administration:write permission from deploy.yml
b8fc27e fix: switch to Actions-based Pages deployment + add .nojekyll
2d68bac fix: update index.html lang attribute to en for default English locale
```

## 4. 当前 TODO 状态（重新同步后）

| 优先级 | 剩余 | 备注 |
|--------|------|------|
| P0 | **0** | 全部完成。BERT+Prototype 核心重构 12/12 |
| P1 | **11** | P1-BERT 清理 2 项（P1-B7 模型切换, P1-B8 性能监控）+ 功能需求 9 项（P1-5~P1-13） |
| P2 | **23** | 全部未开始 |
| **合计** | **34** | |

**下一步推荐**: P1-5（个案级校准结果展示）或 P1-9（Recent Runs 真实数据）——投入产出比高的小型功能需求。

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

### 剩余关键字残留
- **无。**KeywordEntry 零引用。`ConditionDefinition.keywords` 字段已移除。已清理 condition.py 死代码。

### 现有领域预置
`domains.py` 现在包含 5 个领域 × 5 个条件（co_production 为 4 个）的原型文本模板，每个条件 2 个原型（1 正例 + 1 反例）。用于 BERT CLS 余弦相似度评分的完全自然中文句子。

## 6. 快速验证命令

```bash
npm run build              # TypeScript + Vite 构建
uv run pytest --tb=no -q   # Python 测试 (531 passed)
uv run ruff check src/     # 应为干净状态
npm run dev                # 启动开发服务器 (127.0.0.1:3000)
gh run list -b master -l 3 --workflow deploy.yml  # 查看部署状态
```

## 7. 已知注意事项

- **Dev server**: 必须使用 `http://127.0.0.1:3000`，不能使用 `localhost`（Pyodide worker 跨域问题）
- **Worker 类型**: ES 模块 Worker (`{ type: 'module' }`)
- **Pyodide**: CDN 加载 (v0.26.4)，不自托管
- **GitHub Actions 权限**: 仅 `contents/pages/id-token`。`administration` 不存在
- **Python 编码**: 所有 `open()` 调用必须显式指定 `encoding='utf-8'`
- **Python 运行器**: 始终使用 `uv run python`，不要使用裸 `python`
- **RUF001 误报**: domains.py 中的中文标点（，）是合法的原型文本，已在 pyproject.toml 中添加 per-file-ignore
- **Agent 可靠性**: Agent 声称完成不可信——始终用 `git diff --stat`、Grep、Read 验证变更
- **共享文件竞争**: 修改共享文件的 Agent 必须串行运行（先 P1-B3，后 P1-B6）

## 8. 未跟踪文件

```
?? .wolf/memory-archive.md    — 归档的旧 session 日志（2026-05-25 之前）
?? experiment-engine/          — 嵌套 git 仓库/旧 worktree。不要 touch。
```
