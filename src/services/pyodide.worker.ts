/**
 * Pyodide Web Worker — runs Python/NumPy in a background thread so the
 * React UI stays responsive during computation.
 *
 * This file is the worker entry point. Vite bundles it separately via
 * `new Worker(new URL('./pyodide.worker.ts', import.meta.url), { type: 'module' })`.
 * Pyodide is loaded via dynamic import() of the ES module build (pyodide.mjs).
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
 *
 * SECURITY NOTE — CDN Subresource Integrity (SRI):
 *   Pyodide is loaded from jsDelivr CDN (~50 MB of .mjs, .data, .whl files).
 *   SRI hashes are NOT applied to these resources because:
 *   1. The total download exceeds 50 MB; computing and maintaining per-file
 *      SRI hashes for 100+ .whl packages is operationally infeasible.
 *   2. Pyodide's dynamic module loader (loadPyodide) fetches files
 *      programmatically, which bypasses <script integrity> checks.
 *   Primary defenses instead:
 *   - Version pinning (v0.26.4 hardcoded in URLs — verified at runtime below).
 *   - Browser CORS and CSP headers restrict script-src to jsDelivr.
 *   - Content-Security-Policy in index.html limits connect-src to jsDelivr.
 */

import type {
  PyodideWorkerRequest,
  PyodideWorkerResponse,
  TextCorpusEntry,
} from '../types/qca';
import { BertEngine } from '../services/bert-engine';

// ─── Module-scoped state (persists across messages) ────────────────────────
let pyodide: any = null;
let isReady = false;
let loadedPackages: string[] = [];
let bertEngine: BertEngine | null = null;

const REQUIRED_PACKAGES = [
  'numpy',
  'pandas',
  'pydantic',
  'pyyaml',
  'micropip',
  'rich',
];

/** Expected Pyodide version loaded from CDN — must match the hardcoded URL. */
const EXPECTED_PYODIDE_VERSION = '0.26.4';

/** Minimum version that satisfies basic API contract (for grace-period detection). */
const MIN_PYODIDE_VERSION = [0, 26, 0];

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
    pyodide.FS.writeFile(path, new TextEncoder().encode(JSON.stringify(data)));
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
        await handleCalibrate(req.payload.texts, req.payload.conditionSet, req.payload.prototypeTexts);
        break;
      case 'load_corpus':
        await handleLoadCorpus(
          req.payload.fileName,
          req.payload.content,
          req.payload.format,
        );
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
      case 'init_bert':
        await handleInitBert(req.payload.modelName);
        break;
      case 'embed_calibrate':
        await handleEmbedCalibrate(req.payload.texts, req.payload.conditionSet);
        break;
      case 'compute_embeddings':
        await handleComputeEmbeddings(req.payload.texts, req.payload.batchSize);
        break;
      case 'compute_prototype_embeddings':
        await handleComputePrototypeEmbeddings(req.payload.prototypes);
        break;
      case 'get_bert_status':
        handleGetBertStatus();
        break;
      case 'get_bert_metrics':
        if (!bertEngine) {
          respond({
            type: 'bert-metrics',
            payload: {
              totalInferences: 0, totalInferenceMs: 0, totalTextsProcessed: 0,
              cacheHits: 0, cacheMisses: 0, lastInferenceBatchMs: 0, modelName: null,
            }
          })
        } else {
          respond({ type: 'bert-metrics', payload: bertEngine.getPerformanceMetrics() })
        }
        break;
      case 'get_package_status':
        respond({
          type: 'package-status',
          packages: Object.fromEntries(
            loadedPackages.map((p) => [p, 'loaded']),
          ),
        });
        break;
      case 'multi_outcome':
        await handleMultiOutcome(req.payload.analyses);
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

// ─── Unhandled promise rejection handler ───────────────────────────────────
// Without this, promise rejections in the worker propagate to self.onerror
// with sanitized messages ("Script error."), making debugging impossible.
self.onunhandledrejection = (event: PromiseRejectionEvent) => {
  const reason = event.reason?.stack || event.reason?.message || String(event.reason) || 'Unhandled promise rejection';
  log('error', `Unhandled rejection in worker: ${reason}`);
  respond({
    type: 'log',
    message: `Unhandled rejection: ${reason}`,
    level: 'error',
  });
  // Prevent the default handler (which would fire self.onerror with a sanitized message)
  event.preventDefault();
};

// ─── Handlers ─────────────────────────────────────────────────────────────

async function handleInit(extraPackages: string[] = []): Promise<void> {
  if (isReady) {
    respond({ type: 'init-done', loadedPackages });
    return;
  }

  respond({ type: 'init-progress', message: 'Downloading Pyodide...', progress: 5 });

  try {
    // Dynamic import of Pyodide ES module build (module workers don't support importScripts)
    const pyodideModule = await import('https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.mjs');
    const { loadPyodide } = pyodideModule;

    respond({ type: 'init-progress', message: 'Loading Pyodide runtime...', progress: 15 });

    pyodide = await loadPyodide({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/',
    });

    // --- Runtime version check (no SRI, so this is the primary integrity defense) ---
    try {
      const loadedVersion: string = pyodide._module?.API?.version || pyodide.version || '';
      if (loadedVersion && loadedVersion !== EXPECTED_PYODIDE_VERSION) {
        const parts = loadedVersion.split('.').map(Number);
        const [minMaj, minMin, minPatch] = MIN_PYODIDE_VERSION;
        const isBelowMin =
          (parts[0] || 0) < minMaj ||
          ((parts[0] || 0) === minMaj && (parts[1] || 0) < minMin) ||
          ((parts[0] || 0) === minMaj && (parts[1] || 0) === minMin && (parts[2] || 0) < minPatch);
        const level = isBelowMin ? 'error' : 'warn';
        respond({
          type: 'log',
          message: `Pyodide version mismatch: expected ${EXPECTED_PYODIDE_VERSION}, got ${loadedVersion}${isBelowMin ? ' — below minimum supported version' : ''}. CDN cache may be stale.`,
          level,
        });
        if (isBelowMin) {
          throw new Error(`Pyodide version ${loadedVersion} is below minimum required ${EXPECTED_PYODIDE_VERSION}`);
        }
      }
    } catch (verr: any) {
      if (verr.message?.includes('below minimum')) throw verr;
      // If the version property isn't available, log a warning but don't block init
      log('warn', `Could not verify Pyodide version at runtime: ${verr.message || String(verr)}`);
    }

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
  // Fetch the Python package bundle (experiment_engine.tar.gz) generated by CI.
  // The tar.gz is extracted into Pyodide's VFS using Python's built-in tarfile.
  // This mirrors the approach in src/pyodide/engine.ts _mountPythonPackage().
  //
  // The base URL is set by Vite at build time: '/' in dev, '/experiment-engine/' in prod.
  const baseUrl = typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL
    ? import.meta.env.BASE_URL
    : '/';
  const tarUrl = `${baseUrl}py/experiment_engine.tar.gz`;

  try {
    const resp = await fetch(tarUrl);
    if (!resp.ok) {
      log('warn', `Python package bundle not found at ${tarUrl} (HTTP ${resp.status}), falling back to inline mount`);
      await mountFromInline();
      return;
    }

    const buffer = await resp.arrayBuffer();
    const uint8 = new Uint8Array(buffer);
    pyodide.FS.writeFile('/tmp/experiment_engine.tar.gz', uint8);

    await pyodide.runPythonAsync(`
import tarfile
import io
import sys
import os

os.makedirs("/home/pyodide", exist_ok=True)

with open("/tmp/experiment_engine.tar.gz", "rb") as f:
    data = f.read()

bio = io.BytesIO(data)
with tarfile.open(fileobj=bio, mode="r:gz") as tar:
    tar.extractall(path="/home/pyodide")

if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
    `);

    log('info', `Python package extracted successfully from ${tarUrl}`);
  } catch (err: any) {
    log('warn', `Failed to load Python package bundle: ${err.message || String(err)}`);
    await mountFromInline();
  }
}

/**
 * Mount project Python modules into Pyodide's virtual filesystem by fetching
 * module source from the Vite dev server (dev) or from the CI-generated
 * /py/modules.json endpoint.
 *
 * In dev mode, the Vite plugin `pyodideModulesPlugin()` serves a dynamically
 * generated JSON object at /py/modules.json containing the content of every
 * .py file under src/experiment_engine/.  This replaces the legacy approach of
 * creating empty package directories, which caused ModuleNotFoundError.
 *
 * In production, this function is normally not reached because mountProjectModules()
 * extracts the tarball first. But when the tarball is unavailable (e.g. dev mode),
 * this fallback provides the actual Python source files.
 */
async function mountFromInline(): Promise<void> {
  try {
    const baseUrl = typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL
      ? import.meta.env.BASE_URL
      : '/';
    const modulesUrl = `${baseUrl}py/modules.json`;

    const resp = await fetch(modulesUrl);
    if (!resp.ok) {
      throw new Error(`modules.json not available (HTTP ${resp.status})`);
    }

    const modules: Record<string, string> = await resp.json();

    // Write each module file to Pyodide VFS using the JS FS API.
    // FS.mkdirTree creates all ancestor directories in one call.
    for (const [filePath, content] of Object.entries(modules)) {
      const fullPath = `/src/${filePath}`;
      const dir = fullPath.substring(0, fullPath.lastIndexOf('/'));
      pyodide.FS.mkdirTree(dir);
      pyodide.FS.writeFile(fullPath, new TextEncoder().encode(content));
    }

    // Add to sys.path — both /src (where modules are mounted) and / (root fallback)
    pyodide.runPython(`
import sys
for _p in ['/src', '/']:
    if _p not in sys.path:
        sys.path.insert(0, _p)
`);

    log('info', `Mounted ${Object.keys(modules).length} Python modules from modules.json`);
    log('info', `Mounted modules: ${Object.keys(modules).join(', ')}`);
  } catch (err: any) {
    log('error', `Inline mount failed: ${err.message || String(err)}`);
    // Last-resort fallback: create empty directories so imports don't crash
    // immediately, giving users a chance to see the real error.
    try {
      await pyodide.runPythonAsync(`
import sys, os
for path in ['/src', '/']:
    if path not in sys.path:
        sys.path.insert(0, path)
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
    } catch (e2: any) {
      log('error', `Empty dir fallback also failed: ${e2.message}`);
    }
    throw err;  // Re-throw so handleInit's catch sends init-error
  }
}

// ─── Calibrate: texts + condition set → fuzzy-set membership ───────────────

async function handleCalibrate(
  texts: TextCorpusEntry[],
  conditionSet: any,
  prototypeTexts?: any[],
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

    let prototypeFuzzyData: any = undefined;
    if (prototypeTexts && prototypeTexts.length > 0) {
      prototypeFuzzyData = await runHandler(
        "from experiment_engine.pyodide_handlers import handle_calibrate_prototype; handle_calibrate_prototype('/tmp/text_cases.json', '/tmp/condition_set.json', '/tmp/calibrate_proto_output.json')",
        [
          ['/tmp/text_cases.json', prototypeTexts],
          ['/tmp/condition_set.json', conditionSet],
        ],
        '/tmp/calibrate_proto_output.json',
      );
    }

    respond({ type: 'calibrate-done', fuzzyData, prototypeFuzzyData });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'calibrate-error', error: `Calibration failed: ${msg}` });
  }
}

// ─── Load Corpus: parse CSV/JSON/TXT/XLSX in Python via TextCorpusReader ─────

async function handleLoadCorpus(
  fileName: string,
  content: string,
  format: 'csv' | 'json' | 'txt' | 'xlsx',
): Promise<void> {
  try {
    // Write the raw content directly to a VFS file path, bypassing the JSON
    // config intermediate step.  This avoids potential encoding/truncation
    // issues when CSV content (Chinese text, special chars) passes through
    // JSON.stringify → fs.writeFile → Python json.load() → f.write() chain.
    // Sanitize fileName to ASCII-only to avoid the {encoding:'utf8'} 0-byte bug
    // in runHandler() when fileName contains Chinese characters.
    // Preserve the original for display purposes.
    const safeFileName = fileName.replace(/[^a-zA-Z0-9._-]/g, '_');
    const vfsFile = `/tmp/${safeFileName}`;
    if (format === 'xlsx') {
      // Binary: base64-decode in Python side
      const config = { fileName, content, format };
      const entries = await runHandler(
        "from experiment_engine.pyodide_handlers import handle_load_corpus; handle_load_corpus('/tmp/corpus_config.json', '/tmp/corpus_output.json')",
        [['/tmp/corpus_config.json', config]],
        '/tmp/corpus_output.json',
      );
      respond({ type: 'corpus-loaded', entries });
    } else {
      // Write CSV/JSON/TXT content directly to VFS via FS.writeFile.
      // DIAG: log content size before writing
      log('debug', `[corpus-diag] content type=${typeof content} length=${content.length} first100=${JSON.stringify(content.substring(0, 100))}`);
      // Use TextEncoder to produce a Uint8Array, bypassing any Emscripten
      // string-to-binary issues with multi-byte UTF-8 (Chinese) characters.
      // FS.writeFile with { encoding: 'utf8' } on a string can produce a
      // 0-byte file in Pyodide v0.26.4 — a Uint8Array avoids this entirely.
      ensureReady();
      const encoder = new TextEncoder();
      const contentBytes = encoder.encode(content);
      pyodide.FS.writeFile(vfsFile, contentBytes);
      // DIAG: verify the file was written correctly
      try {
        ensureReady();
        const stat = pyodide.FS.stat(vfsFile);
        log('debug', `[corpus-diag] after FS.writeFile: size=${stat.size} mode=${stat.mode}`);
        if (stat.size === 0) {
          throw new Error(`Corpus file ${vfsFile} is 0 bytes after FS.writeFile`);
        }
      } catch (statErr: any) {
        const msg = `Corpus file check failed for ${vfsFile}: ${statErr.message || String(statErr)}`;
        log('error', `[corpus-diag] ${msg}`);
        throw new Error(msg);
      }
      // Pass the file path through inputSpecs (JSON) to avoid string
      // interpolation into Python code (code injection risk).
      const entries = await runHandler(
        "from experiment_engine.pyodide_handlers import handle_load_corpus_direct; handle_load_corpus_direct('/tmp/corpus_direct_config.json', '/tmp/corpus_output.json')",
        [['/tmp/corpus_direct_config.json', { vfsFile }]],
        '/tmp/corpus_output.json',
      );
      respond({ type: 'corpus-loaded', entries });
    }
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

async function ensureDocx(): Promise<void> {
  if (!loadedPackages.includes('python-docx')) {
    log('info', 'Installing python-docx via micropip...');
    await pyodide.runPythonAsync(`
import micropip
await micropip.install('python-docx')
    `);
    loadedPackages.push('python-docx');
    log('info', 'python-docx installed successfully');
  }
}

async function handleExport(
  format: 'csv' | 'json' | 'latex' | 'docx',
  resultJson: any,
): Promise<void> {
  try {
    if (format === 'docx') {
      await ensureDocx();
    }
    const { data, mime: mimeType } = await runHandler(
      "from experiment_engine.pyodide_handlers import handle_export; handle_export('/tmp/export_result.json', '/tmp/export_config.json', '/tmp/export_output.json')",
      [
        ['/tmp/export_result.json', resultJson],
        ['/tmp/export_config.json', { format }],
      ],
      '/tmp/export_output.json',
    );
    if (format === 'docx') {
      // data is base64-encoded binary; decode to Uint8Array for blob construction
      const binaryStr = atob(data as string);
      const bytes = new Uint8Array(binaryStr.length);
      for (let i = 0; i < binaryStr.length; i++) {
        bytes[i] = binaryStr.charCodeAt(i);
      }
      respond({ type: 'export-done', data: bytes, mimeType });
    } else {
      respond({ type: 'export-done', data, mimeType });
    }
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

// ─── BERT Handlers ──────────────────────────────────────────────────────────

async function handleInitBert(modelName: string): Promise<void> {
  try {
    bertEngine = new BertEngine();

    bertEngine.onProgress((progress: number, message: string) => {
      respond({ type: 'bert-init-progress', progress, message });
    });

    await bertEngine.loadModel(modelName);
    respond({ type: 'bert-init-done', modelName });
    log('info', `BERT model "${modelName}" loaded successfully`);
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'bert-init-error', error: msg });
    log('error', `BERT init failed: ${msg}`);
  }
}

async function handleEmbedCalibrate(
  texts: Array<{text_id: string; text: string; embedding: number[]}>,
  conditionSet: any,
): Promise<void> {
  ensureReady();

  try {
    const fuzzyData = await runHandler(
      "from experiment_engine.pyodide_handlers import handle_embed_calibrate; handle_embed_calibrate('/tmp/texts.json', '/tmp/condition_set.json', '/tmp/embed_calibrate_output.json')",
      [
        ['/tmp/texts.json', texts],
        ['/tmp/condition_set.json', conditionSet],
      ],
      '/tmp/embed_calibrate_output.json',
    );

    respond({ type: 'embed-calibrate-done', fuzzyData });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'embed-calibrate-error', error: `Embed calibration failed: ${msg}` });
  }
}

async function handleComputeEmbeddings(
  texts: string[],
  batchSize?: number,
): Promise<void> {
  if (!bertEngine || !bertEngine.isReady()) {
    respond({ type: 'embeddings-error', error: 'BERT model not loaded. Call init_bert first.' });
    return;
  }

  try {
    const batch = await bertEngine.extractEmbeddings(texts, batchSize ?? 16);
    const arrays: number[][] = batch.embeddings.map((e) => Array.from(e));
    respond({ type: 'embeddings-computed', embeddings: arrays });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'embeddings-error', error: `Embedding computation failed: ${msg}` });
  }
}

async function handleComputePrototypeEmbeddings(
  prototypes: Record<string, string[]>,
): Promise<void> {
  if (!bertEngine || !bertEngine.isReady()) {
    respond({ type: 'embeddings-error', error: 'BERT model not loaded. Call init_bert first.' });
    return;
  }

  try {
    const result: Record<string, {embeddings: number[][]; labels: number[]; weights: number[]}> = {};

    for (const [conditionName, protoTexts] of Object.entries(prototypes)) {
      if (protoTexts.length === 0) {
        result[conditionName] = { embeddings: [], labels: [], weights: [] };
        continue;
      }

      const batch = await bertEngine.extractEmbeddings(protoTexts, 16);
      result[conditionName] = {
        embeddings: batch.embeddings.map((e) => Array.from(e)),
        labels: protoTexts.map(() => 1),
        weights: protoTexts.map(() => 1.0),
      };
    }

    respond({ type: 'prototype-embeddings-computed', embeddings: result });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'embeddings-error', error: `Prototype embedding failed: ${msg}` });
  }
}

function handleGetBertStatus(): void {
  if (!bertEngine) {
    respond({ type: 'bert-status', loaded: false, modelName: null });
  } else {
    respond({
      type: 'bert-status',
      loaded: bertEngine.isReady(),
      modelName: bertEngine.getModelName(),
    });
  }
}

// ─── Guard ────────────────────────────────────────────────────────────────

function ensureReady(): void {
  if (!isReady || !pyodide) {
    throw new Error('Pyodide not initialized. Call init() first.');
  }
}

// ─── Multi-Outcome Comparison ─────────────────────────────────────────────

async function handleMultiOutcome(analyses: Record<string, any>): Promise<void> {
  try {
    const report = await runHandler(
      "from experiment_engine.pyodide_handlers import handle_multi_outcome; handle_multi_outcome('/tmp/analyses.json', '/tmp/multi_outcome_output.json')",
      [['/tmp/analyses.json', analyses]],
      '/tmp/multi_outcome_output.json',
    );
    respond({ type: 'multi-outcome-done', report });
  } catch (err: any) {
    const msg = err.message || String(err);
    respond({ type: 'multi-outcome-error', error: `Multi-outcome comparison failed: ${msg}` });
  }
}

// ─── Export for type safety (not actually imported by main thread) ────────
export type { PyodideWorkerRequest, PyodideWorkerResponse };
