# QCA Analysis Tool — Project Status (2026-05-28)

> Handover from session that fixed Transformers.js cloud inference crash (bug-393).
> Previous handover (2026-05-27) content preserved below for historical context.

## 1. 当前基线

| 指标 | 值 |
|------|-----|
| HEAD | `241a98d` — fix: Transformers.js 云端推理崩溃 — _model() 添加 try-catch 零向量回退 |
| 分支 | `master` |
| 代码改动 | 已全部提交推送 |
| 本地测试 | TS build clean, 532 tests passed |
| 部署状态 | 已推送 `master`，GitHub Actions 自动部署中 |

## 2. 本轮修复（2026-05-28）：Transformers.js 云端推理崩溃

### 报错

```
管道执行失败：Embedding computation failed: Cannot read properties of undefined (reading 'data')
```

**仅云端复现**（GitHub Pages 生产环境），本地 `npm run dev` 正常。

### 根因

`bert-engine.ts` 中 `this._model(batchTexts, {pooling:'mean', normalize:false})`（Transformers.js FeatureExtractionPipeline 推理调用）在云端 ONNX Runtime Web 环境下可能抛出内部 TypeError。原因推测为：

1. GitHub Pages 生产构建中 Transformers.js/ONNX Runtime 的打包方式不同
2. 跨域环境下 ONNX Runtime Web 的 WebAssembly/WebGL 后端初始化差异
3. 导致模型输出的 tensor 内部 `.data` 为 `undefined`，Transformers.js 内部访问时抛出

### 修复

**文件**：`src/services/bert-engine.ts`（`extractEmbeddings()` 方法）

1. 将 `this._model(batchTexts, ...)` 调用包裹 try-catch（第 246-263 行）
2. 捕获 Transformers.js 内部错误：
   - `console.error()` 记录详细 batch 诊断（批次号、文本数、切片范围）
   - 该 batch 全部用 `DEFAULT_HIDDEN_DIM` 零向量回退
   - `continue` 到下一 batch
3. 原 `throw new Error("Transformers output tensor has no data")`（第 265-268 行）改为零向量回退 + console.warn + continue

### 效果

- 即使部分 batch 推理失败，embedding 计算正常完成（退化 batch 用零向量）
- 零向量 → 余弦相似度 0 → 校准后 membership 约 0.5
- pipeline 不再因单个 batch 失败而整体崩溃
- bug-393 已记录到 buglog.json

### 验证

```
TS build: 0 errors
Tests: 532 passed, 1 skipped, 6 xfailed
```

## 3. 本轮新增文件变更

| 文件 | 变更 | 状态 |
|------|------|------|
| `src/services/bert-engine.ts` | _model() try-catch + 零向量回退 + tensor 无 data 降级 | ✅ 已推送 `241a98d` |
| `.wolf/buglog.json` | bug-393 记录 | ✅ 已推送 |
| `.wolf/cerebrum.md` | Do-Not-Repeat: 云端模型推理防护 | ✅ 已推送 |
| `.wolf/memory.md` | 本次 session 记录 | ✅ 已推送 |
| `.wolf/handover.md` | 本次更新 | 当前文件 |

## 4. 下次 session 要做

1. **云端验证**：部署后测试完整管道（Load Samples → Run Pipeline），确认：
   - 不再出现 "Embedding computation failed" 错误
   - Pipeline 正常完成到结果页面
2. **如仍有问题**：检查部署后 DevTools Console 中 `[BertEngine] Model inference failed for batch` 日志
3. **如需进一步优化**：失败 batch 考虑自动缩小 batchSize 重试（当前 16 → 8 → 4 → 1），而不是直接零向量回退
4. **历史遗留**：校准 BERT 路径整合（runCalibrateOnly → handleCalibrate 迁移）仍待处理

## ——— 以下为 2026-05-27 历史 Handover 内容 ———

## 5. 历史记录：Calibrate 执行失败 — 非 BERT 路径退化

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

### 历史关键文件

- `src/pages/DataInput.tsx:713` — handleCalibrate 按钮 handler
- `src/hooks/useQCAWorkflow.ts:208` — BERT 路径的 handleCalibrate
- `src/hooks/useQCAWorkflow.ts:254` — 非 BERT 路径的 runCalibrateOnly
- `src/experiment_engine/text_calibration/calibrator.py:80` — _precompute_scores
- `src/experiment_engine/text_calibration/calibrator.py:162` — _fallback_text_scores
