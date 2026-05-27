# OpenWolf

@.wolf/OPENWOLF.md

This project uses OpenWolf for context management. Read and follow .wolf/OPENWOLF.md every session. Check .wolf/cerebrum.md before generating code. Check .wolf/anatomy.md before reading files.

## fsQCA Domain Invariants

### Outcome 列必须是模糊值

fsQCA 中 outcome 列（如 `high_dissatisfaction`）必须是 (0,1) 区间内的连续模糊值，**不是**二元 0/1：
- `process()` — 所有列（含 outcome）走正常文本评分 → 模糊校准，产生连续值
- `process_with_outcome()` — ⚠️ 用外部 0/1 值**覆盖** outcome 列，导致退化
- 在用户面向的 Web 端始终用 `process()`，`process_with_outcome()` 仅限 CLI/研究者场景
- 怀疑 outcome 退化时检查：`len(np.unique(membership[:, -1])) > 2` 是否成立

### API 设计原则

- 优先单方法 + 显式枚举参数，避免双方法 API。例如：`process(data, outcome_handling=OutcomeHandling.CALIBRATE_FROM_TEXT)` 好于两个分别的 `process()` 和 `process_with_outcome()`，因为后者让 agent 容易选错方法而类型系统无法阻止。

### 测试惯例

- 校准管线修改后必须运行语义正确性测试：验证 outcome 列的唯一值 > 2 且包含非 0/1 的模糊值
- CSV 端到端集成测试必须覆盖 CLI 和 Web 两条路径
- 新加的校准测试必须包含值域不变性断言，不能只有"不崩溃"断言
