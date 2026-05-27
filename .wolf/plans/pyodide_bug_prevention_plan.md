# Pyodide Import Bug Prevention Plan

> 生成于 2026-05-27 | 基于 rich/pydantic 模块缺失 Bug 修复经验

## 1. Module-Level Import Audit

已完成扫描 tar.gz 中包含的 35 个 Python 文件。当前 REQUIRED_PACKAGES `['numpy', 'pydantic', 'pyyaml', 'micropip', 'rich']` 完全覆盖所有模块级非 stdlib import。

**无新增风险。** 唯一第三方包 `pandas` 在所有文件中均为函数级懒加载（try/except 守卫或 helper 函数内）。

## 2. 关键行动项

### Phase 1 — 立即执行

| # | 风险 | 文件 | 行动 |
|---|------|------|------|
| P1.1 | **HIGH**: 缺失包太晚暴露 | `pyodide.worker.ts` | mount 完成后立即运行 import probe（`import numpy, pydantic, yaml, rich`），失败报 `init-error` 而非 `calibrate-error` |
| P1.2 | **HIGH**: Init 挂起无限 | `pyodide.worker.ts` | 添加 120s 总超时，超时发 `init-error` |
| P1.3 | **LOW**: 依赖清单无 Python 端 | `experiment_engine/pyodide_manifest.py` (NEW) | 创建 Python 侧 manifest 文件，作为依赖列表单一来源 |

### Phase 2 — 下个迭代

| # | 风险 | 文件 | 行动 |
|---|------|------|------|
| P2.1 | **HIGH**: 新代码引入未注册 import | `scripts/check_pyodide_imports.py` (NEW) | AST 解析 tar.gz 中所有 .py 的模块级 import，对比 allowlist |
| P2.2 | **MEDIUM**: Allowlist 漂移 | `configs/pyodide_package_allowlist.json` (NEW) | 共享配置，脚本 + pyodide.worker.ts 引用同一份 |
| P2.3 | **MEDIUM**: CSP 配置错误到生产 | 扩展 CI 脚本 | 验证 dist/index.html CSP 包含必需指令 |

### Phase 3 — 近期

| # | 风险 | 文件 | 行动 |
|---|------|------|------|
| P3.1 | **MEDIUM**: 大数据集 OOM | `pyodide.ts` + `pyodide.worker.ts` | 前端验证数据集大小 + WASM 内存监控 |
| P3.2 | **MEDIUM**: 单包下载挂起 | `pyodide.worker.ts` | 每个 `loadPackage` 加 60s 超时 |

## 3. Import Probe 实现参考

```typescript
// pyodide.worker.ts - after mountProjectModules()
async function verifyImports(): Promise<void> {
  try {
    await pyodide.runPythonAsync(`
import experiment_engine
for mod_name in ['numpy', 'yaml', 'pydantic', 'rich']:
    __import__(mod_name)
print("All module-level imports verified")
`);
  } catch (err: any) {
    throw new Error(`Pyodide init - import verification failed: ${err.message}`);
  }
}
```

## 4. 已验证安全的懒加载模式（供参考）

- `pipeline.py:18-26`: `try: from rich.console import Console; _HAS_RICH=True; except ImportError: _HAS_RICH=False`
- `plugins.py:17-23`: 同上
- `config.py:163`: `from pydantic import ValidationError` 函数体内
- `io/readers.py`: pandas 通过 `_get_pandas()` helper 懒加载
- report 模块：通过 `try/except ImportError` 包裹

## 5. CSP 必需指令清单

| 指令 | 必需值 | 原因 |
|------|--------|------|
| script-src | `'wasm-unsafe-eval'` | WASM 编译 |
| script-src | `https://cdn.jsdelivr.net` | Pyodide ES module |
| worker-src | `'self'` + `blob:` + `https://cdn.jsdelivr.net` | Worker 创建 + Vite bundle + CDN |
| connect-src | `https://cdn.jsdelivr.net` + `https://huggingface.co` + `https://cdn-lfs.huggingface.co` | 包下载 + BERT 模型 |
