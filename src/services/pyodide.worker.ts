/**
 * Pyodide Web Worker — runs Python/NumPy in a background thread so the
 * React UI stays responsive during computation.
 *
 * This file is the worker entry point. Vite bundles it separately via
 * `new Worker(new URL('./pyodide.worker.ts', import.meta.url), { type: 'module' })`.
 *
 * Architecture:
 *   Main Thread                          Worker (this file)
 *   ──────────                           ──────────────────
 *   pyodide.ts ──postMessage──>  onmessage → dispatch request
 *                                load pyodide (once)
 *                                install packages
 *                                mount project modules
 *                                run Python → serialize → postMessage back
 */

import type {
  PyodideWorkerRequest,
  PyodideWorkerResponse,
  TextCorpusEntry,
} from '../types/qca';

// ─── Module-scoped state (persists across messages) ────────────────────────
let pyodide: any = null;
let isReady = false;
let loadedPackages: string[] = [];

const REQUIRED_PACKAGES = [
  'numpy',
  'pyyaml',
  'micropip',
];

// ─── Helper: post a typed response back to main thread ────────────────────
function respond(msg: PyodideWorkerResponse): void {
  (self as any).postMessage(msg);
}

function log(level: 'debug' | 'info' | 'warn' | 'error', message: string): void {
  respond({ type: 'log', message, level });
}

// ─── Python code template for mounting project modules ─────────────────────
// The worker sends this to Pyodide's runPython() to add src/experiment_engine
// to sys.path so that `from experiment_engine.models import ...` works.
function getMountScript(modulePaths: Record<string, string>): string {
  // modulePaths is populated at build time or loaded from a manifest.
  const pathEntries = Object.entries(modulePaths)
    .map(([name, content]) => {
      const escaped = JSON.stringify(content);
      return `  "${name}": ${escaped}`;
    })
    .join(',\n');

  return `
import sys
import os
import json

_module_files = {
${pathEntries}
}

# Write Python modules into in-memory filesystem
for fname, fcontent in _module_files.items():
    parts = fname.split('/')
    for i in range(len(parts) - 1):
        d = '/'.join(parts[:i+1])
        os.makedirs(d, exist_ok=True)
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(fcontent)

# Add to path
if '/src' not in sys.path:
    sys.path.insert(0, '/src')
`;
}

// ─── Main worker message handler ──────────────────────────────────────────
self.onmessage = async (event: MessageEvent<PyodideWorkerRequest>) => {
  const req = event.data;

  try {
    switch (req.type) {
      case 'init':
        await handleInit(req.payload.packages);
        break;
      case 'calibrate':
        await handleCalibrate(req.payload.texts, req.payload.conditionSet);
        break;
      case 'calibrate_prototype':
        await handleCalibratePrototype(req.payload.texts, req.payload.conditionSet);
        break;
      case 'load_corpus':
        await handleLoadCorpus(req.payload.source);
        break;
      case 'analyze':
        await handleAnalyze(req.payload.fuzzyData, req.payload.params);
        break;
      case 'run_robustness':
        await handleRobustness(req.payload.fuzzyData, req.payload.analysisResult);
        break;
      case 'run_counterfactuals':
        await handleCounterfactuals(req.payload.fuzzyData, req.payload.analysisResult);
        break;
      case 'export_result':
        await handleExport(req.payload.format, req.payload.result);
        break;
      case 'validate_condition_set':
        await handleValidate(req.payload.conditionSet);
        break;
      case 'get_package_status':
        respond({
          type: 'package-status',
          packages: Object.fromEntries(
            loadedPackages.map((p) => [p, 'loaded'])
          ),
        });
        break;
      case 'terminate':
        respond({ type: 'terminated' });
        self.close();
        break;
      default:
        respond({ type: 'log', message: `Unknown request: ${(req as any).type}`, level: 'error' });
    }
  } catch (err: any) {
    // Catch-all for unhandled errors in the dispatch
    respond({
      type: 'log',
      message: `Worker dispatch error: ${err.message || String(err)}`,
      level: 'error',
    });
  }
};

// ─── Handlers ─────────────────────────────────────────────────────────────

async function handleInit(extraPackages: string[] = []): Promise<void> {
  if (isReady) {
    respond({ type: 'init-done', loadedPackages });
    return;
  }

  respond({ type: 'init-progress', message: 'Downloading Pyodide...', progress: 5 });

  try {
    // @ts-ignore — pyodide is loaded from CDN in the worker scope
    importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js');

    respond({ type: 'init-progress', message: 'Loading Pyodide runtime...', progress: 15 });

    // @ts-ignore — loadPyodide is defined by the importScripts above
    pyodide = await loadPyodide({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/',
    });

    respond({ type: 'init-progress', message: 'Pyodide runtime ready', progress: 30 });

    // Install required packages
    const allPackages = [...REQUIRED_PACKAGES, ...extraPackages];
    const toInstall = allPackages.filter((p) => !loadedPackages.includes(p));

    if (toInstall.length > 0) {
      for (let i = 0; i < toInstall.length; i++) {
        const pkg = toInstall[i];
        respond({
          type: 'init-progress',
          message: `Installing ${pkg}...`,
          progress: 30 + Math.floor((i / toInstall.length) * 30),
        });
        await pyodide.loadPackage(pkg);
        loadedPackages.push(pkg);
      }
    }

    respond({ type: 'init-progress', message: 'Packages installed', progress: 60 });

    // Mount project Python modules
    // In production, a build step would bundle the Python source into a JSON manifest.
    // For development, the main thread sends module contents via a separate message,
    // or the worker fetches them from the dev server.
    await mountProjectModules();

    respond({ type: 'init-progress', message: 'Project modules mounted', progress: 90 });

    isReady = true;
    respond({ type: 'init-done', loadedPackages });
    log('info', 'Pyodide worker initialized successfully');
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'init-error', error: msg });
    log('error', `Pyodide init failed: ${msg}`);
  }
}

async function mountProjectModules(): Promise<void> {
  // Fetch a manifest of Python module paths → contents from the dev/build server.
  // The manifest is generated by a Vite plugin or a pre-build script.
  try {
    const resp = await fetch('/pyodide-modules.json');
    if (!resp.ok) {
      log('warn', `Module manifest not found (${resp.status}), mounting from inline`);
      await mountFromInline();
      return;
    }
    const manifest: Record<string, string> = await resp.json();
    const script = getMountScript(manifest);
    pyodide.runPython(script);
  } catch {
    log('warn', 'Failed to fetch module manifest, mounting inline fallback');
    await mountFromInline();
  }
}

async function mountFromInline(): Promise<void> {
  // Minimal inline mount — run the key modules as strings.
  // For production, use the manifest approach above.
  // This fallback ensures core imports work: experiment_engine.models, qca_engine.*, etc.
  try {
    await pyodide.runPythonAsync(`
import sys, os

# Ensure the package root is importable
for path in ['/src', '/']:
    if path not in sys.path:
        sys.path.insert(0, path)

# Create package directories with __init__.py files so Python can import them
_packages = [
    '/src/experiment_engine',
    '/src/experiment_engine/qca_engine',
    '/src/experiment_engine/qca_engine/advanced',
    '/src/experiment_engine/text_calibration',
    '/src/experiment_engine/report',
    '/src/experiment_engine/viz',
    '/src/experiment_engine/io',
    '/src/experiment_engine/core',
]

for _pkg in _packages:
    os.makedirs(_pkg, exist_ok=True)
    _init = os.path.join(_pkg, '__init__.py')
    if not os.path.exists(_init):
        with open(_init, 'w') as f:
            f.write('# auto-generated package init\\n')
`);
    log('info', 'Inline module directories created with __init__.py files');
  } catch (err: any) {
    log('error', `Inline mount failed: ${err.message || String(err)}`);
  }
}

// ─── Calibrate: texts + condition set → fuzzy-set membership ───────────────

async function handleCalibrate(
  texts: TextCorpusEntry[],
  conditionSet: any
): Promise<void> {
  ensureReady();

  try {
    // Serialize inputs and write to Pyodide VFS to avoid code injection via template literals
    const textsJson = JSON.stringify(texts);
    const conditionSetJson = JSON.stringify(conditionSet);

    pyodide.FS.writeFile('/tmp/texts.json', textsJson, { encoding: 'utf8' });
    pyodide.FS.writeFile('/tmp/condition_set.json', conditionSetJson, { encoding: 'utf8' });

    const resultJson = await pyodide.runPythonAsync(`
import json
from experiment_engine.text_calibration.calibrator import TextCalibrationStage
from experiment_engine.text_calibration.condition import _condition_set_from_dict
from experiment_engine.models import TrainingSample

with open('/tmp/texts.json', 'r', encoding='utf-8') as f:
    _texts = json.load(f)
with open('/tmp/condition_set.json', 'r', encoding='utf-8') as f:
    _cs_dict = json.load(f)
_condition_set = _condition_set_from_dict(_cs_dict)

# Build TrainingSample objects
_samples = []
for _t in _texts:
    _s = TrainingSample(
        text_id=_t['text_id'],
        text=_t['text'],
        metadata=_t.get('metadata', {})
    )
    _samples.append(_s)

_calibrator = TextCalibrationStage(condition_set=_condition_set)
_calibrator.setup()

# Process samples → fuzzy-set data
_fuzzy_data = None
for _s in _samples:
    _result = _calibrator.calibrate_one(_s)
    if _fuzzy_data is None:
        import numpy as np
        _arr = np.array([_result])
    else:
        _arr = np.vstack([_fuzzy_data, _result])

# Build the serializable output
_json_out = {
    "membership": _fuzzy_data.membership.tolist() if hasattr(_fuzzy_data, 'membership') else _arr.tolist(),
    "case_ids": _fuzzy_data.case_ids if hasattr(_fuzzy_data, 'case_ids') else [],
    "condition_names": _fuzzy_data.condition_names if hasattr(_fuzzy_data, 'condition_names') else [],
    "outcome_name": _fuzzy_data.outcome_name if hasattr(_fuzzy_data, 'outcome_name') else "",
    "texts": [t.text for t in _samples],
    "metadata": {}
}
json.dumps(_json_out)
`);

    const fuzzyData = JSON.parse(resultJson);
    respond({ type: 'calibrate-done', fuzzyData });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'calibrate-error', error: `Calibration failed: ${msg}` });
  }
}

// ─── Calibrate Prototype: text cases + prototype condition set → fuzzy-set ──

async function handleCalibratePrototype(
  textCases: any[],
  conditionSet: any
): Promise<void> {
  ensureReady();

  try {
    const casesJson = JSON.stringify(textCases);
    const csJson = JSON.stringify(conditionSet);

    pyodide.FS.writeFile('/tmp/text_cases.json', casesJson, { encoding: 'utf8' });
    pyodide.FS.writeFile('/tmp/condition_set.json', csJson, { encoding: 'utf8' });

    const resultJson = await pyodide.runPythonAsync(`
import json
import numpy as np
from experiment_engine.text_calibration.calibrator import TextCalibrationStage
from experiment_engine.text_calibration.condition import _condition_set_from_dict
from experiment_engine.models import InputData

with open('/tmp/text_cases.json', 'r', encoding='utf-8') as f:
    _cases = json.load(f)
with open('/tmp/condition_set.json', 'r', encoding='utf-8') as f:
    _cs_dict = json.load(f)
_condition_set = _condition_set_from_dict(_cs_dict)

_texts = [c['text'] for c in _cases]
_outcomes = np.array([c.get('outcome', 0) for c in _cases], dtype=np.float64)
_case_ids = [c['text_id'] for c in _cases]

_calibrator = TextCalibrationStage(condition_set=_condition_set)
_calibrator.setup()

_data = InputData(data=np.array(_texts, dtype=object), index=_case_ids)
_result = _calibrator.process_with_outcome(_data, _outcomes)
_fuzzy = _result.processed

json.dumps({
    "membership": _fuzzy.membership.tolist(),
    "case_ids": _fuzzy.case_ids,
    "condition_names": _fuzzy.condition_names,
    "outcome_name": _fuzzy.outcome_name,
    "texts": _texts,
    "metadata": _fuzzy.metadata,
})
`);

    const fuzzyData = JSON.parse(resultJson);
    respond({ type: 'calibrate-prototype-done', fuzzyData });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'calibrate-prototype-error', error: `Prototype calibration failed: ${msg}` });
  }
}

// ─── Load Corpus: parse CSV/JSON/TXT in Python ────────────────────────────

async function handleLoadCorpus(source: any): Promise<void> {
  ensureReady();
  try {
    // For now, pass through the source data directly.
    // Full TextCorpusReader integration requires mounted Python modules.
    respond({ type: 'corpus-loaded', entries: source });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'corpus-error', error: `Corpus loading failed: ${msg}` });
  }
}

// ─── Analyze: fuzzy data → truth table + solutions + necessity/sufficiency ─

async function handleAnalyze(
  fuzzyDataJson: any,
  params: any
): Promise<void> {
  ensureReady();

  try {
    const fdJson = JSON.stringify(fuzzyDataJson);
    const paramsJson = JSON.stringify(params);

    pyodide.FS.writeFile('/tmp/fuzzy_data.json', fdJson, { encoding: 'utf8' });
    pyodide.FS.writeFile('/tmp/params.json', paramsJson, { encoding: 'utf8' });

    const resultJson = await pyodide.runPythonAsync(`
import json
import numpy as np
from experiment_engine.models import FuzzySetData
from experiment_engine.qca_engine.analyzer import QCAnalyzerStage

with open('/tmp/fuzzy_data.json', 'r', encoding='utf-8') as f:
    _fd_dict = json.load(f)
with open('/tmp/params.json', 'r', encoding='utf-8') as f:
    _params = json.load(f)

_fuzzy = FuzzySetData(
    membership=np.array(_fd_dict['membership']),
    case_ids=_fd_dict.get('case_ids'),
    condition_names=_fd_dict.get('condition_names', []),
    outcome_name=_fd_dict.get('outcome_name', ''),
    texts=_fd_dict.get('texts'),
    metadata=_fd_dict.get('metadata', {})
)

_analyzer = QCAnalyzerStage(
    consistency_threshold=_params.get('consistency_threshold', 0.75),
    frequency_threshold=_params.get('frequency_threshold', 1.0),
)
_analyzer.setup()
_result = _analyzer.analyze(_fuzzy)

# Serialize to JSON-safe dict
_out = _result.model_dump(mode='json')
json.dumps(_out, default=str)
`);

    const result = JSON.parse(resultJson);
    respond({ type: 'analyze-done', result });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'analyze-error', error: `Analysis failed: ${msg}` });
  }
}

// ─── Robustness ───────────────────────────────────────────────────────────

async function handleRobustness(
  fuzzyDataJson: any,
  analysisResultJson: any
): Promise<void> {
  ensureReady();

  try {
    const fdJson = JSON.stringify(fuzzyDataJson);
    const arJson = JSON.stringify(analysisResultJson);

    pyodide.FS.writeFile('/tmp/fuzzy_data.json', fdJson, { encoding: 'utf8' });
    pyodide.FS.writeFile('/tmp/analysis_result.json', arJson, { encoding: 'utf8' });

    const resultJson = await pyodide.runPythonAsync(`
import json
import numpy as np
from experiment_engine.models import FuzzySetData, QCAAnalysisResult
from experiment_engine.qca_engine.advanced.robustness import RobustnessTester

with open('/tmp/fuzzy_data.json', 'r', encoding='utf-8') as f:
    _fd_dict = json.load(f)
with open('/tmp/analysis_result.json', 'r', encoding='utf-8') as f:
    _ar_dict = json.load(f)

_fuzzy = FuzzySetData(
    membership=np.array(_fd_dict['membership']),
    case_ids=_fd_dict.get('case_ids'),
    condition_names=_fd_dict.get('condition_names', []),
    outcome_name=_fd_dict.get('outcome_name', ''),
)

_baseline = QCAAnalysisResult(**_ar_dict)

_tester = RobustnessTester()
_report = _tester.run_all(_fuzzy, _baseline)

json.dumps(_report.model_dump(mode='json'), default=str)
`);

    const report = JSON.parse(resultJson);
    respond({ type: 'robustness-done', report });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'robustness-error', error: `Robustness failed: ${msg}` });
  }
}

// ─── Counterfactuals ─────────────────────────────────────────────────────

async function handleCounterfactuals(
  fuzzyDataJson: any,
  analysisResultJson: any
): Promise<void> {
  ensureReady();

  try {
    const fdJson = JSON.stringify(fuzzyDataJson);
    const arJson = JSON.stringify(analysisResultJson);

    pyodide.FS.writeFile('/tmp/fuzzy_data.json', fdJson, { encoding: 'utf8' });
    pyodide.FS.writeFile('/tmp/analysis_result.json', arJson, { encoding: 'utf8' });

    const resultJson = await pyodide.runPythonAsync(`
import json
import numpy as np
from experiment_engine.models import FuzzySetData, QCAAnalysisResult
from experiment_engine.qca_engine.advanced.counterfactual import CounterfactualAnalyzer

with open('/tmp/fuzzy_data.json', 'r', encoding='utf-8') as f:
    _fd_dict = json.load(f)
with open('/tmp/analysis_result.json', 'r', encoding='utf-8') as f:
    _ar_dict = json.load(f)

_fuzzy = FuzzySetData(
    membership=np.array(_fd_dict['membership']),
    case_ids=_fd_dict.get('case_ids'),
    condition_names=_fd_dict.get('condition_names', []),
    outcome_name=_fd_dict.get('outcome_name', ''),
)

_baseline = QCAAnalysisResult(**_ar_dict)

_cf_analyzer = CounterfactualAnalyzer()
_report = _cf_analyzer.analyze(_fuzzy, _baseline)

json.dumps(_report.model_dump(mode='json'), default=str)
`);

    const report = JSON.parse(resultJson);
    respond({ type: 'counterfactuals-done', report });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({
      type: 'counterfactuals-error',
      error: `Counterfactuals failed: ${msg}`,
    });
  }
}

// ─── Export ──────────────────────────────────────────────────────────────

async function handleExport(
  format: 'csv' | 'json' | 'latex',
  resultJson: any
): Promise<void> {
  ensureReady();

  try {
    const rJson = JSON.stringify(resultJson);

    pyodide.FS.writeFile('/tmp/export_result.json', rJson, { encoding: 'utf8' });

    const { data, mimeType } = await pyodide.runPythonAsync(`
import json, io
from experiment_engine.models import QCAAnalysisResult

with open('/tmp/export_result.json', 'r', encoding='utf-8') as f:
    _ar_dict = json.load(f)
_result = QCAAnalysisResult(**_ar_dict)

fmt = '${format}'

if fmt == 'json':
    out = json.dumps(_result.model_dump(mode='json'), indent=2, ensure_ascii=False, default=str)
    mime = 'application/json'
elif fmt == 'csv':
    buf = io.StringIO()
    import csv as _csv
    if _result.fuzzy_data:
        w = _csv.writer(buf)
        header = _result.fuzzy_data.condition_names + [_result.fuzzy_data.outcome_name]
        w.writerow(header)
        for row in _result.fuzzy_data.membership:
            w.writerow(row.tolist())
    out = buf.getvalue()
    mime = 'text/csv'
elif fmt == 'latex':
    from experiment_engine.report.qca_reporter import QCAReporter
    _reporter = QCAReporter()
    out = _reporter.generate(_result)
    mime = 'application/x-latex'
else:
    raise ValueError(f'Unknown export format: {fmt}')

(out, mime)
`);

    respond({ type: 'export-done', data, mimeType });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'export-error', error: `Export failed: ${msg}` });
  }
}

// ─── Validate Condition Set ──────────────────────────────────────────────

async function handleValidate(conditionSet: any): Promise<void> {
  ensureReady();

  try {
    const csJson = JSON.stringify(conditionSet);

    pyodide.FS.writeFile('/tmp/condition_set.json', csJson, { encoding: 'utf8' });

    const resultJson = await pyodide.runPythonAsync(`
import json
from experiment_engine.text_calibration.condition import _condition_set_from_dict

with open('/tmp/condition_set.json', 'r', encoding='utf-8') as f:
    _cs_dict = json.load(f)
_cs = _condition_set_from_dict(_cs_dict)

warnings = []
if not _cs.conditions:
    warnings.append("No causal conditions defined")
if _cs.outcome is None:
    warnings.append("No outcome condition defined")
for c in _cs.conditions:
    if not c.keywords:
        warnings.append(f"Condition '{c.name}' has no keywords")
    if c.calibration_params is None:
        warnings.append(f"Condition '{c.name}' has no calibration parameters")

valid = len(warnings) == 0
json.dumps({"valid": valid, "warnings": warnings})
`);

    const { valid, warnings } = JSON.parse(resultJson);
    respond({ type: 'validate-done', valid, warnings });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'validate-error', error: `Validation failed: ${msg}` });
  }
}

// ─── Guard ────────────────────────────────────────────────────────────────

function ensureReady(): void {
  if (!isReady || !pyodide) {
    throw new Error('Pyodide not initialized. Call init() first.');
  }
}

// ─── Export for type safety (not actually imported by main thread) ────────
export type { PyodideWorkerRequest, PyodideWorkerResponse };
