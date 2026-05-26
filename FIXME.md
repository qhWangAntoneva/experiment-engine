# FIXME — QCA Analysis Tool

> 最后更新：2026-05-26
> 严重程度：🔴 = 严重/必须修 | 🟡 = 警告/建议修 | 🟢 = 建议/锦上添花

---

## FIXME-28: models/qca.py:173-186 — `TextCase.outcome` 字段语义过窄

**文件**: `src/experiment_engine/models/qca.py`
**严重程度**: 🟢 建议
**问题**: `TextCase.outcome` 定义为 `int = Field(0, ge=0, le=1)`，字段描述为 "Binary outcome (0 or 1) used directly as crisp-set membership"。但 fsQCA 模式下的 outcome 是连续值（0.0-1.0），当前 validator 拒绝浮点值。raw text 和 prototype text 都可能使用 fsQCA（continuous outcome）或 csQCA（binary outcome），TextCase 的 outcome 字段应支持两种类型。
**修复**: 将 `outcome: int` 改为 `outcome: float`（ge=0.0, le=1.0），字段描述改为 "Outcome membership score (0.0-1.0; use 0/1 for crisp-set, continuous for fuzzy-set)"。或在 fsQCA 模式下使用单独的 `fuzzy_outcome: float` 字段。
**来源**: 需求变更审查, 评审者#2026-05-24

---

## FIXME-32: domains.py — 原型预置数据硬编码，用户无法在线编辑

**文件**: `src/experiment_engine/text_calibration/domains.py`, `src/pages/DataInput.tsx`
**严重程度**: 🟢 建议
**问题**: 5 个领域的原型（prototype）预置数据硬编码在 `domains.py` 的 `DOMAIN_PRESETS` 字典中。关键词相关代码已移除，此 preset 现仅服务于 prototype 相似度引擎。用户只能通过导入外部 CSV/JSON 文件来"间接修改"原型文本，修改后的原型配置不持久化（刷新即丢失），也不保留用户的自定义编辑。
**用户影响**: 研究者在反复调优原型时需：(1) 导出当前原型 → (2) 用外部编辑器修改 → (3) 重新导入 → (4) 再次校准——每次修改需 4 步操作且离开应用。对于原型相似度方法，快速迭代原型文本是核心体验需求。
**修复**: (1) DataInput 页面添加"Edit Preset Prototypes"按钮，打开 inline 编辑表格（condition + prototype text + weight）；(2) 修改保存到 localStorage；(3) 添加"恢复默认原型"按钮。长期可考虑数据库持久化。(@see TODO P1-34)
**来源**: 客户代表#2026-05-24

---

## 统计

| 严重程度 | 数量 | 条目 |
|----------|------|------|
| 🔴 严重 | 0 | — |
| 🟡 警告 | 0 | — |
| 🟢 建议 | 2 | FIXME-28, FIXME-32 |
| **合计** | **2** | |
