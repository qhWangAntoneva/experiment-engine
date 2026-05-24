/**
 * Main-thread Pyodide bridge — methods called from React components.
 * Internally, all work is delegated to a Web Worker to keep the UI responsive.
 *
 * Usage from a React component:
 *   const bridge = usePyodideBridge();
 *   const fuzzy = await bridge.calibrate(texts, conditionSet);
 */

import type {
  PyodideWorkerRequest,
  PyodideWorkerResponse,
  TextCorpusEntry,
  ConditionSet,
  QCAAnalysisParams,
  QCAAnalysisResultJSON,
  FuzzySetDataJSON,
  RobustnessReport,
  CounterfactualReport,
  ExportResult,
  PyodideWorkerRequest as PWReq,
  PyodideWorkerResponse as PWRes,
} from '../types/qca';

// ─── Types ─────────────────────────────────────────────────────────────────

export type PyodideInitState =
  | { status: 'unloaded' }
  | { status: 'loading'; progress: number; message: string }
  | { status: 'ready'; loadedPackages: string[] }
  | { status: 'error'; error: string };

export type InitCallback = (state: PyodideInitState) => void;

// ─── Observer helpers ─────────────────────────────────────────────────────
export type WorkerLogEntry = {
  ts: number;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
};
export type LogListener = (entry: WorkerLogEntry) => void;

// ─── Timeout helpers ──────────────────────────────────────────────────────
const DEFAULT_TIMEOUT_MS = 300_000; // 5 minutes for heavy computation

class PyodideTimeoutError extends Error {
  constructor(operation: string) {
    super(`Pyodide worker timed out during: ${operation}`);
    this.name = 'PyodideTimeoutError';
  }
}

// ─── Main Bridge Class ─────────────────────────────────────────────────────

export class PyodideBridge {
  private worker: Worker | null = null;
  private initState: PyodideInitState = { status: 'unloaded' };
  private initListeners: Set<InitCallback> = new Set();
  private logListeners: Set<LogListener> = new Set();
  private pendingRequests: Map<
    string,
    {
      resolve: (value: any) => void;
      reject: (reason: any) => void;
      timeout: ReturnType<typeof setTimeout>;
    }
  > = new Map();
  private requestSeq = 0;

  // ─── Initialization ────────────────────────────────────────────────────

  /**
   * Start the Pyodide worker and wait for it to signal readiness.
   * Safe to call multiple times — subsequent calls are no-ops if already loaded.
   */
  async init(packages: string[] = []): Promise<void> {
    if (this.initState.status === 'ready') return;
    if (this.initState.status === 'loading') {
      return new Promise((resolve, reject) => {
        const check = (state: PyodideInitState) => {
          if (state.status === 'ready') resolve();
          else if (state.status === 'error') reject(new Error(state.error));
        };
        this.initListeners.add(check);
      });
    }

    this.setState({ status: 'loading', progress: 0, message: 'Starting worker...' });
    this.createWorker();

    return new Promise<void>((resolve, reject) => {
      const waitForReady = (state: PyodideInitState) => {
        if (state.status === 'ready') {
          this.initListeners.delete(waitForReady);
          resolve();
        } else if (state.status === 'error') {
          this.initListeners.delete(waitForReady);
          reject(new Error(state.error));
        }
      };
      this.initListeners.add(waitForReady);

      // Fire init request
      this.send({ type: 'init', payload: { packages } }).catch(reject);
    });
  }

  getInitState(): PyodideInitState {
    return this.initState;
  }

  onInitChange(cb: InitCallback): () => void {
    this.initListeners.add(cb);
    // Immediately call with current state
    cb(this.initState);
    return () => this.initListeners.delete(cb);
  }

  // ─── Logging ───────────────────────────────────────────────────────────

  onLog(cb: LogListener): () => void {
    this.logListeners.add(cb);
    return () => this.logListeners.delete(cb);
  }

  // ─── QCA Pipeline Methods ──────────────────────────────────────────────

  /**
   * Run text calibration: raw Chinese texts → fuzzy-set membership matrix.
   */
  async calibrate(
    texts: TextCorpusEntry[],
    conditionSet: ConditionSet
  ): Promise<FuzzySetDataJSON> {
    return this.send<FuzzySetDataJSON>(
      { type: 'calibrate', payload: { texts, conditionSet } },
      'calibrate-done',
      'calibrate'
    );
  }

  /**
   * Load a corpus from uploaded file content.
   */
  async loadCorpus(
    source: TextCorpusEntry[] | { type: 'paste'; content: string; format: 'csv' | 'json' | 'txt' }
  ): Promise<TextCorpusEntry[]> {
    if (Array.isArray(source)) {
      // Already parsed by frontend — skip worker
      return source;
    }
    return this.send<TextCorpusEntry[]>(
      { type: 'load_corpus', payload: { source } },
      'corpus-loaded',
      'load-corpus'
    );
  }

  /**
   * Run QCA analysis on calibrated fuzzy-set data.
   */
  async analyze(
    fuzzyData: FuzzySetDataJSON,
    params: QCAAnalysisParams
  ): Promise<QCAAnalysisResultJSON> {
    return this.send<QCAAnalysisResultJSON>(
      { type: 'analyze', payload: { fuzzyData, params } },
      'analyze-done',
      'analyze'
    );
  }

  /**
   * Run robustness/sensitivity tests.
   */
  async runRobustness(
    fuzzyData: FuzzySetDataJSON,
    analysisResult: QCAAnalysisResultJSON
  ): Promise<RobustnessReport> {
    return this.send<RobustnessReport>(
      { type: 'run_robustness', payload: { fuzzyData, analysisResult } },
      'robustness-done',
      'robustness'
    );
  }

  /**
   * Run counterfactual analysis.
   */
  async runCounterfactuals(
    fuzzyData: FuzzySetDataJSON,
    analysisResult: QCAAnalysisResultJSON
  ): Promise<CounterfactualReport> {
    return this.send<CounterfactualReport>(
      { type: 'run_counterfactuals', payload: { fuzzyData, analysisResult } },
      'counterfactuals-done',
      'counterfactuals'
    );
  }

  /**
   * Export results to CSV, JSON, or LaTeX.
   */
  async exportResult(
    format: 'csv' | 'json' | 'latex',
    result: QCAAnalysisResultJSON
  ): Promise<ExportResult> {
    const resp = await this.send<{ data: string; mimeType: string }>(
      { type: 'export_result', payload: { format, result } },
      'export-done',
      `export-${format}`
    );

    const extMap: Record<string, string> = {
      csv: 'csv',
      json: 'json',
      latex: 'tex',
    };

    return {
      data: new Blob([resp.data], { type: resp.mimeType }),
      mimeType: resp.mimeType,
      filename: `qca-analysis.${extMap[format]}`,
    };
  }

  /**
   * Validate a condition set definition for structural correctness.
   */
  async validateConditionSet(
    conditionSet: ConditionSet
  ): Promise<{ valid: boolean; warnings: string[] }> {
    return this.send(
      { type: 'validate_condition_set', payload: { conditionSet } },
      'validate-done',
      'validate'
    );
  }

  /**
   * Query which Python packages are loaded.
   */
  async getPackageStatus(): Promise<Record<string, string>> {
    return this.send(
      { type: 'get_package_status' },
      'package-status',
      'package-status'
    );
  }

  /**
   * Terminate the worker.
   */
  terminate(): void {
    if (this.worker) {
      this.send({ type: 'terminate' }).catch(() => {});
      this.worker.terminate();
      this.worker = null;
      this.setState({ status: 'unloaded' });
    }
  }

  // ─── Internal ──────────────────────────────────────────────────────────

  private createWorker(): void {
    this.worker = new Worker(
      new URL('./pyodide.worker.ts', import.meta.url),
      { type: 'module' }
    );

    this.worker.onmessage = (event: MessageEvent) => {
      const msg = event.data as PyodideWorkerResponse;

      // Handle init progress/lifecycle
      switch (msg.type) {
        case 'init-progress':
          this.setState({ status: 'loading', progress: msg.progress, message: msg.message });
          return;
        case 'init-done':
          this.setState({ status: 'ready', loadedPackages: msg.loadedPackages });
          return;
        case 'init-error':
          this.setState({ status: 'error', error: msg.error });
          return;
        case 'terminated':
          this.setState({ status: 'unloaded' });
          return;
        case 'log':
          this.logListeners.forEach((cb) =>
            cb({ ts: Date.now(), level: msg.level, message: msg.message })
          );
          return;
      }

      // Route response to the pending request that matches this message type
      this.resolveOne(msg);
    };

    this.worker.onerror = (err) => {
      console.error('Pyodide worker error:', err);
      this.setState({
        status: 'error',
        error: err.message || 'Unknown worker error',
      });
    };
  }

  private setState(next: PyodideInitState): void {
    this.initState = next;
    this.initListeners.forEach((cb) => cb(next));
  }

  /**
   * Send a request to the worker and wait for a matching response.
   * Uses a simple correlation by expected response type.
   */
  private send<T>(
    request: PyodideWorkerRequest,
    expectedResponseType?: string,
    timeoutOperation?: string
  ): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      if (!this.worker) {
        reject(new Error('Pyodide worker not initialized'));
        return;
      }

      if (request.type !== 'init' && request.type !== 'terminate' && this.initState.status !== 'ready') {
        reject(new Error(`Pyodide not ready (current: ${this.initState.status})`));
        return;
      }

      const reqId = String(++this.requestSeq);
      const timeout = setTimeout(() => {
        this.pendingRequests.delete(reqId);
        reject(new PyodideTimeoutError(timeoutOperation || request.type));
      }, DEFAULT_TIMEOUT_MS);

      this.pendingRequests.set(reqId, { resolve, reject, timeout });
      this.worker.postMessage(request);
    });
  }

  /**
   * Route a worker response to the oldest matching pending request.
   * Matching is done by response type since requests are sequential.
   */
  private resolveOne(msg: PyodideWorkerResponse): void {
    // Find the earliest pending request
    for (const [reqId, pending] of this.pendingRequests) {
      clearTimeout(pending.timeout);
      this.pendingRequests.delete(reqId);

      // Check if this response is an error variant
      if (msg.type.endsWith('-error') || msg.type === 'corpus-error') {
        pending.reject(new Error((msg as any).error || 'Unknown error'));
        return;
      }

      pending.resolve(msg);
      return;
    }
  }

  /**
   * Clean up all resources.
   */
  destroy(): void {
    this.terminate();
    this.initListeners.clear();
    this.logListeners.clear();
    for (const [, pending] of this.pendingRequests) {
      clearTimeout(pending.timeout);
      pending.reject(new Error('Bridge destroyed'));
    }
    this.pendingRequests.clear();
  }
}

// ─── Singleton ────────────────────────────────────────────────────────────

let _bridge: PyodideBridge | null = null;

export function getPyodideBridge(): PyodideBridge {
  if (!_bridge) {
    _bridge = new PyodideBridge();
  }
  return _bridge;
}
