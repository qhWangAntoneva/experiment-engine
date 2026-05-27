# QCA Analysis Tool — Project Status (2026-05-27)

> Handover from session that debugged calibration execution failure and identified root cause.

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| HEAD | `a414d03` — fix: 移除 useQCAWorkflow 防御性解包（Python 端已扁平化） |
| 分支 | `master` |
| 代码改动（未提交） | `src/types/qca.ts`, `src/utils/conditionSetToYaml.ts`, `.wolf/` 文档文件 |
| 本地测试 | Calibrate 执行仍然失败，Pipeline 被阻塞 |

## 2. 本轮发现的 Bug：Calibrate 执行失败 — 非 BERT 路径退化

### 根因

"Calibrate (Text to Fuzzy-Set)" 按钮触发 `DataInput.tsx` → `runCalibrateOnly()` → `bridge.calibrate()`（非 BERT 路径）。该路径调用 Python `handle_calibrate()`，后者使用 `TextCalibrationStage`。

`TextCalibrationStage._precompute_scores()` 检测到无 BERT embedding 时，回退到 `_fallback_text_scores()`（基于文本长度的归一化）。当输入文本长度相近时，该回退产生退化分数（min==max），导致 DirectCalibration 抛出 ValueError。

### 数据流

```
DataInput.tsx handleCalibrate
  → useQCAWorkflow.ts runCalibrateOnly
    → bridge.calibrate()   ← 非 BERT 路径！
      → pyodide.worker.ts handleCalibrate
        → pyodide_handlers.py handle_calibrate
          → TextCalibrationStage.process()
            → _fallback_text_scores()   ← 退化风险

正确路径（但未被按钮调用）：
  → bridge.embedCalibrate()
    → pyodide.worker.ts handleEmbedCalibrate
      → pyodide_handlers.py handle_embed_calibrate
        → CosineSimilarityEngine.compute_scores()  ← 语义相似度
```

### 核心问题

`useQCAWorkflow.ts` 中有两个独立的校准函数：
- **`handleCalibrate` (line ~208)**：BERT 路径 — 先调用 `bridge.computeEmbeddings()` 获取 JS BERT 嵌入，再调用 `bridge.embedCalibrate()`
- **`runCalibrateOnly` (line ~254)**：非 BERT 路径 — 直接调用 `bridge.calibrate()` → Python fallback

**DataInput.tsx 按钮绑定了 `runCalibrateOnly`**，导致校准始终走退化回退路径。

### 验证状态

Playwright 验证：
```
上次记录: 6/8 Passed, 2/8 Failed
❌ Calibrate execution    ← 非 BERT 路径退化
❌ Pipeline execution      ← 阻塞在校准
```

本次分析已确认根因。修复方案：将 DataInput.tsx 按钮改为调用 BERT 路径（`handleCalibrate`）或修复 `runCalibrateOnly` 使用 `bridge.embedCalibrate()`。

### 未决问题

- 校准失败的根本原因已定位，但**尚未修复**。
- 修复 #1-#4（YAML 缩进匹配）已验证 TS build clean，但校准执行本身不依赖这些修复。

## 3. 关键文件变更

| 文件 | 变更 | 状态 |
|------|------|------|
| `src/types/qca.ts` | DEFAULT_CONDITION_SET_YAML: keywords → prototypes | ✅ 未提交 |
| `src/utils/conditionSetToYaml.ts` | 3 处缩进修复 + 1 处 null 检查修复 | ✅ 未提交 |

## 4. 下次 session 要做

1. **修复校准路径**：将 DataInput.tsx 的 handleCalibrate 改为调用 BERT 路径（`bridge.embedCalibrate()` 或 useQCAWorkflow 的 `handleCalibrate`）
2. **重新运行验证**：
   ```bash
   BASE_URL=http://localhost:5173/ node tmp/verify_deployed.mjs
   ```
3. **提交并推送**所有修复
4. **触发 CI 部署**，在部署后再次运行验证

## 5. 调试笔记

**校准流程数据路径**：
1. 前端按钮 → `DataInput.tsx handleCalibrate` → `runCalibrateOnly` → `bridge.calibrate()`
2. Worker `handleCalibrate` → Python `handle_calibrate` → `TextCalibrationStage.process()`
3. 无 BERT embeddings → `_fallback_text_scores()` → 文本长度归一化 → DirectCalibration

**BERT 路径（未使用）**：
1. `bridge.computeEmbeddings()` → JS Transformers.js BERT 推理
2. `bridge.embedCalibrate()` → Python `handle_embed_calibrate` → `CosineSimilarityEngine`
3. 语义相似度 → 软max → 正常校准

**关键文件**：
- `src/pages/DataInput.tsx:713` — handleCalibrate 按钮 handler
- `src/hooks/useQCAWorkflow.ts:208` — BERT 路径的 handleCalibrate
- `src/hooks/useQCAWorkflow.ts:254` — 非 BERT 路径的 runCalibrateOnly
- `src/experiment_engine/text_calibration/calibrator.py:80` — _precompute_scores
- `src/experiment_engine/text_calibration/calibrator.py:162` — _fallback_text_scores
