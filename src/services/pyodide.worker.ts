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
 *
 * Python logic lives in experiment_engine.pyodide_handlers (testable).
 * This file only handles VFS I/O and message passing.
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

// ─── Generic Pyodide handler runner ────────────────────────────────────────

/**
 * Template for all handlers:
 *   1. ensureReady()
 *   2. Write each input JSON file to Pyodide VFS via FS.writeFile
 *   3. Call the Python handler via runPythonAsync (import + single function call)
 *   4. Read the output JSON file from Pyodide VFS via FS.readFile
 *   5. Return parsed result
 *
 * @param handlerExpr - Python statement: import + function call.
 *   e.g. "from experiment_engine.pyodide_handlers import handle_analyze; handle_analyze('/tmp/a.json', '/tmp/b.json', '/tmp/out.json')"
 * @param inputSpecs - Array of [vfsPath, jsonData] pairs to write before running.
 * @param outputPath - VFS path where the Python handler writes its JSON result.
 * @returns Parsed JSON output from the Python handler.
 */
async function runHandler(
  handlerExpr: string,
  inputSpecs: Array<[string, any]>,
  outputPath: string,
): Promise<any> {
  ensureReady();

  for (const [path, data] of inputSpecs) {
    pyodide.FS.writeFile(path, JSON.stringify(data), { encoding: 'utf8' });
  }

  await pyodide.runPythonAsync(handlerExpr);
  const raw = pyodide.FS.readFile(outputPath, { encoding: 'utf8' });
  return JSON.parse(raw);
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
            loadedPackages.map((p) => [p, 'loaded']),
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
  conditionSet: any,
): Promise<void> {
  try {
    const fuzzyData = await runHandler(
      "from experiment_engine.pyodide_handlers import handle_calibrate; handle_calibrate('/tmp/texts.json', '/tmp/condition_set.json', '/tmp/calibrate_output.json')",
      [
        ['/tmp/texts.json', texts],
        ['/tmp/condition_set.json', conditionSet],
      ],
      '/tmp/calibrate_output.json',
    );
    respond({ type: 'calibrate-done', fuzzyData });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'calibrate-error', error: `Calibration failed: ${msg}` });
  }
}

// ─── Calibrate Prototype: text cases + prototype condition set → fuzzy-set ──

async function handleCalibratePrototype(
  textCases: any[],
  conditionSet: any,
): Promise<void> {
  try {
    const fuzzyData = await runHandler(
      "from experiment_engine.pyodide_handlers import handle_calibrate_prototype; handle_calibrate_prototype('/tmp/text_cases.json', '/tmp/condition_set.json', '/tmp/calibrate_proto_output.json')",
      [
        ['/tmp/text_cases.json', textCases],
        ['/tmp/condition_set.json', conditionSet],
      ],
      '/tmp/calibrate_proto_output.json',
    );
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
  params: any,
): Promise<void> {
  try {
    const result = await runHandler(
      "from experiment_engine.pyodide_handlers import handle_analyze; handle_analyze('/tmp/fuzzy_data.json', '/tmp/params.json', '/tmp/analyze_output.json')",
      [
        ['/tmp/fuzzy_data.json', fuzzyDataJson],
        ['/tmp/params.json', params],
      ],
      '/tmp/analyze_output.json',
    );
    respond({ type: 'analyze-done', result });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'analyze-error', error: `Analysis failed: ${msg}` });
  }
}

// ─── Robustness ───────────────────────────────────────────────────────────

async function handleRobustness(
  fuzzyDataJson: any,
  analysisResultJson: any,
): Promise<void> {
  try {
    const report = await runHandler(
      "from experiment_engine.pyodide_handlers import handle_robustness; handle_robustness('/tmp/fuzzy_data.json', '/tmp/analysis_result.json', '/tmp/robustness_output.json')",
      [
        ['/tmp/fuzzy_data.json', fuzzyDataJson],
        ['/tmp/analysis_result.json', analysisResultJson],
      ],
      '/tmp/robustness_output.json',
    );
    respond({ type: 'robustness-done', report });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'robustness-error', error: `Robustness failed: ${msg}` });
  }
}

// ─── Counterfactuals ─────────────────────────────────────────────────────

async function handleCounterfactuals(
  fuzzyDataJson: any,
  analysisResultJson: any,
): Promise<void> {
  try {
    const report = await runHandler(
      "from experiment_engine.pyodide_handlers import handle_counterfactuals; handle_counterfactuals('/tmp/fuzzy_data.json', '/tmp/analysis_result.json', '/tmp/counterfactuals_output.json')",
      [
        ['/tmp/fuzzy_data.json', fuzzyDataJson],
        ['/tmp/analysis_result.json', analysisResultJson],
      ],
      '/tmp/counterfactuals_output.json',
    );
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
  resultJson: any,
): Promise<void> {
  try {
    const { data, mime: mimeType } = await runHandler(
      "from experiment_engine.pyodide_handlers import handle_export; handle_export('/tmp/export_result.json', '/tmp/export_config.json', '/tmp/export_output.json')",
      [
        ['/tmp/export_result.json', resultJson],
        ['/tmp/export_config.json', { format }],
      ],
      '/tmp/export_output.json',
    );
    respond({ type: 'export-done', data, mimeType });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'export-error', error: `Export failed: ${msg}` });
  }
}

// ─── Validate Condition Set ──────────────────────────────────────────────

async function handleValidate(conditionSet: any): Promise<void> {
  try {
    const { valid, warnings } = await runHandler(
      "from experiment_engine.pyodide_handlers import handle_validate; handle_validate('/tmp/condition_set.json', '/tmp/validate_output.json')",
      [['/tmp/condition_set.json', conditionSet]],
      '/tmp/validate_output.json',
    );
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
