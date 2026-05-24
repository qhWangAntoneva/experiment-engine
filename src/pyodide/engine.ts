// =============================================================================
// Pyodide Engine — loads the QCA Python analysis engine into the browser
// =============================================================================
// Architecture:
//   1. Load Pyodide WebAssembly runtime from CDN (jsdelivr).
//   2. Install Python dependencies (numpy, pydantic, pyyaml) via micropip.
//   3. Fetch and extract the experiment_engine Python package from the
//      deployment's static assets.
//   4. Expose a `runPython()` bridge for the React UI to call analysis
//      functions directly.
//
// CDN strategy:
//   Pyodide ~50 MB assets are served from jsdelivr CDN, NOT self-hosted.
//   The npm `pyodide` package (~50 KB) provides the TypeScript loader;
//   actual .asm.js + .whl files are fetched at runtime with browser cache.
//   Only the experiment_engine.tar.gz (~80 KB) is self-hosted in the
//   GitHub Pages deployment.
//
// Pyodide version: 0.26.4 (pinned in deploy.yml `workflow_dispatch` default)
// =============================================================================

import type { PyodideInterface } from "pyodide"

// ── Constants ───────────────────────────────────────────────────────────────

/** jsdelivr CDN URL for Pyodide full build (stdlib + numpy + common pkgs). */
const PYODIDE_INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"

/** Python packages to install via Pyodide's micropip. */
const REQUIRED_PACKAGES: string[] = ["numpy", "pydantic", "pyyaml"]

/** Path to the self-hosted Python source tar.gz (relative to Vite's base). */
const PYTHON_BUNDLE_PATH = "py/experiment_engine.tar.gz"

// Matches the Pyodide version from deploy.yml workflow_dispatch default.
const EXPECTED_PYODIDE_VERSION = "0.26.4"

// ── Engine status types ─────────────────────────────────────────────────────

export type EngineState = "idle" | "loading" | "ready" | "error"

export interface EngineStatus {
  state: EngineState
  /** 0–100 progress percentage. */
  progress: number
  /** Human-readable status message. */
  message: string
  /** Error message when state === 'error'. */
  error?: string
  /** Pyodide version string (set after load). */
  pyodideVersion?: string
}

/** Status update callback type. */
export type StatusCallback = (status: EngineStatus) => void

// ── Engine class ────────────────────────────────────────────────────────────

/**
 * Singleton engine that manages the Pyodide WebAssembly runtime and provides
 * a bridge between the React frontend and the Python QCA analysis engine.
 *
 * Usage:
 *   const engine = getPyodideEngine()
 *   engine.onStatus((s) => console.log(s.message))
 *   await engine.initialize()
 *   const result = await engine.runPython("1 + 1")
 */
export class PyodideEngine {
  private _pyodide: PyodideInterface | null = null
  private _status: EngineStatus = { state: "idle", progress: 0, message: "Engine not started" }
  private _listeners: Set<StatusCallback> = new Set()

  // ── public read-only ────────────────────────────────────────────────────

  /** Current engine status snapshot. */
  get status(): EngineStatus {
    return { ...this._status }
  }

  /** True once `initialize()` has completed successfully. */
  get isReady(): boolean {
    return this._status.state === "ready"
  }

  /** Subscribe to status changes. Returns an unsubscribe function. */
  onStatus(cb: StatusCallback): () => void {
    this._listeners.add(cb)
    // Push current status immediately.
    cb({ ...this._status })
    return () => {
      this._listeners.delete(cb)
    }
  }

  // ── initialization ──────────────────────────────────────────────────────

  /**
   * Initialize the Pyodide runtime and load the QCA Python engine.
   * Safe to call multiple times — subsequent calls are no-ops if already
   * loaded, or re-throw the error if initialization failed.
   */
  async initialize(): Promise<void> {
    if (this._status.state === "ready") return
    if (this._status.state === "loading") {
      // Wait for the in-flight initialization to complete by polling.
      return new Promise((resolve, reject) => {
        const unsub = this.onStatus((s) => {
          if (s.state === "ready") {
            unsub()
            resolve()
          } else if (s.state === "error") {
            unsub()
            reject(new Error(s.error ?? "Initialization failed"))
          }
        })
      })
    }

    this._setStatus({ state: "loading", progress: 0, message: "Loading Pyodide WebAssembly runtime..." })
    try {
      // Load Pyodide from CDN. The npm `pyodide` package's `loadPyodide`
      // function fetches pyodide.js + pyodide.asm.js + stdlib from the
      // indexURL. This is the ~50 MB payload — first load takes 5-30s
      // depending on connection speed. Subsequent loads hit browser cache.
      this._pyodide = await this._loadPyodideRuntime()

      this._setStatus({
        state: "loading",
        progress: 25,
        message: `Pyodide v${this._pyodide.version} loaded. Installing Python packages...`,
        pyodideVersion: this._pyodide.version,
      })

      // Install Python dependencies.
      await this._installDependencies()

      this._setStatus({
        state: "loading",
        progress: 55,
        message: "Packages installed. Loading experiment-engine module...",
      })

      // Fetch and mount the QCA Python package.
      await this._mountPythonPackage()

      this._setStatus({ state: "loading", progress: 85, message: "Verifying module imports..." })

      // Smoke-test: import core modules to catch load failures early.
      await this._verifyImports()

      this._setStatus({
        state: "ready",
        progress: 100,
        message: "QCA engine ready.",
        pyodideVersion: this._pyodide.version,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      this._setStatus({ state: "error", progress: 0, message: "Initialization failed", error: message })
      throw err
    }
  }

  // ── Python bridge ────────────────────────────────────────────────────────

  /**
   * Run arbitrary Python code in the Pyodide runtime and return the result.
   * The result is converted from Python to JavaScript via Pyodide's FFI.
   *
   * For complex data, prefer returning JSON strings and calling JSON.parse()
   * on the JS side — this avoids FFI conversion edge cases with numpy arrays.
   */
  async runPython(code: string): Promise<unknown> {
    if (!this._pyodide) throw new Error("Pyodide not initialized. Call initialize() first.")
    const result = this._pyodide.runPython(code)
    // Convert Python objects to JS via Pyodide's foreign function interface.
    // This handles: int, float, str, bool, None, list, dict, set, bytes.
    // numpy arrays are returned as JS TypedArrays via toJs().
    if (result && typeof result.toJs === "function") {
      return result.toJs({ dict_converter: Object.fromEntries })
    }
    return result
  }

  /**
   * Run Python code asynchronously (required for code with `await` / micropip).
   */
  async runPythonAsync(code: string): Promise<unknown> {
    if (!this._pyodide) throw new Error("Pyodide not initialized. Call initialize() first.")
    const result = await this._pyodide.runPythonAsync(code)
    if (result && typeof result.toJs === "function") {
      return result.toJs({ dict_converter: Object.fromEntries })
    }
    return result
  }

  /** Get the underlying PyodideInterface for advanced use. */
  getPyodide(): PyodideInterface {
    if (!this._pyodide) throw new Error("Pyodide not initialized.")
    return this._pyodide
  }

  // ── private helpers ──────────────────────────────────────────────────────

  private _setStatus(status: EngineStatus): void {
    this._status = status
    for (const cb of this._listeners) {
      try {
        cb({ ...status })
      } catch {
        // Don't let a listener error break the engine.
      }
    }
  }

  /**
   * Load the Pyodide runtime. Uses a dynamic import so Vite does not try to
   * bundle the pyodide npm package (it's a CDN loader only).
   */
  private async _loadPyodideRuntime(): Promise<PyodideInterface> {
    // Dynamic import — Vite treats pyodide as external (see vite.config.ts
    // optimizeDeps.exclude). At runtime, loadPyodide() fetches the actual
    // WebAssembly artifacts from PYODIDE_INDEX_URL.
    const { loadPyodide } = await import("pyodide")

    const pyodide = await loadPyodide({
      indexURL: PYODIDE_INDEX_URL,
      // fullStdLib: true includes the full Python stdlib (tarfile, json, etc.)
      // which we need for extracting the Python package tarball.
      fullStdLib: true,
    })

    const versionMatch = pyodide.version.includes(EXPECTED_PYODIDE_VERSION)
    if (!versionMatch) {
      console.warn(
        `Pyodide version mismatch: expected ${EXPECTED_PYODIDE_VERSION}, got ${pyodide.version}. ` +
          `Update PYODIDE_INDEX_URL and EXPECTED_PYODIDE_VERSION in engine.ts.`,
      )
    }

    return pyodide
  }

  /** Install required Python packages from Pyodide's package index. */
  private async _installDependencies(): Promise<void> {
    if (!this._pyodide) throw new Error("Pyodide not initialized.")

    // `numpy` is a Pyodide built-in — use loadPackage for fast install.
    await this._pyodide.loadPackage("numpy")

    // `pydantic` and `pyyaml` are pure-Python wheels — install via micropip.
    await this._pyodide.runPythonAsync(`
import micropip
await micropip.install(${JSON.stringify(REQUIRED_PACKAGES.filter((p) => p !== "numpy"))})
    `)
  }

  /** Fetch the self-hosted experiment_engine.tar.gz and extract it into Pyodide's filesystem. */
  private async _mountPythonPackage(): Promise<void> {
    if (!this._pyodide) throw new Error("Pyodide not initialized.")

    const baseUrl = import.meta.env.BASE_URL
    const tarUrl = `${baseUrl}${PYTHON_BUNDLE_PATH}`

    const response = await fetch(tarUrl)
    if (!response.ok) {
      throw new Error(`Failed to fetch Python package: HTTP ${response.status} ${response.statusText}`)
    }

    const buffer = await response.arrayBuffer()
    const uint8 = new Uint8Array(buffer)

    // Write to Pyodide's virtual filesystem (MEMFS — in-memory).
    this._pyodide.FS.writeFile("/tmp/experiment_engine.tar.gz", uint8)

    // Extract using Python's tarfile (stdlib, always available with fullStdLib).
    await this._pyodide.runPythonAsync(`
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

import experiment_engine
print(f"experiment-engine v{experiment_engine.__version__} mounted successfully")
    `)
  }

  /** Import core modules to verify the package is functional. */
  private async _verifyImports(): Promise<void> {
    if (!this._pyodide) throw new Error("Pyodide not initialized.")

    // Run a comprehensive import check. Any ModuleNotFoundError here means
    // a dependency is missing or a forbidden import (matplotlib, click, etc.)
    // was not properly excluded from the bundled tar.
    await this._pyodide.runPythonAsync(`
from experiment_engine.models import MembershipData, TruthTable, QCASolutions
from experiment_engine.pipeline import Pipeline, Stage
from experiment_engine.config import load_config
from experiment_engine.text_calibration.domains import DOMAIN_PRESETS
from experiment_engine.text_calibration.keyword_dict import ChineseKeywordDictionary
from experiment_engine.text_calibration.calibrator import TextCalibrationStage
from experiment_engine.qca_engine.truth_table import TruthTableBuilder
from experiment_engine.qca_engine.consistency import ConsistencyCalculator
from experiment_engine.qca_engine.minimization import QuineMcCluskey
from experiment_engine.qca_engine.necessity import NecessityAnalyzer
from experiment_engine.qca_engine.sufficiency import SufficiencyAnalyzer
from experiment_engine.qca_engine.solution import SolutionFormatter
from experiment_engine.qca_engine.analyzer import QCAnalyzerStage
from experiment_engine.qca_engine.advanced.robustness import RobustnessTester
from experiment_engine.qca_engine.advanced.counterfactual import CounterfactualAnalyzer
from experiment_engine.io.readers import TextCorpusReader, CSVReader
from experiment_engine.io.exporters import JSONExporter
print("All core module imports verified — engine healthy")
    `)
  }
}

// ── Singleton ───────────────────────────────────────────────────────────────

let _instance: PyodideEngine | null = null

/** Get the singleton PyodideEngine instance. */
export function getPyodideEngine(): PyodideEngine {
  if (!_instance) {
    _instance = new PyodideEngine()
  }
  return _instance
}
