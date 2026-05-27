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
  TextCase,
  ConditionSet,
  QCAAnalysisParams,
  QCAAnalysisResultJSON,
  MembershipDataJSON,
  RobustnessReport,
  CounterfactualReport,
  MultiOutcomeReport,
  ExportResult,
  EmbedCalibrateTextEntry,
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
          if (state.status === 'ready') {
            this.initListeners.delete(check);
            resolve();
          } else if (state.status === 'error') {
            this.initListeners.delete(check);
            reject(new Error(state.error));
          }
        };
        this.initListeners.add(check);
      });
    }

    // Cleanup any previous zombie worker before creating a new one
    if (this.worker) {
      try { this.worker.terminate(); } catch {}
      this.worker = null;
    }

    this.setState({ status: 'loading', progress: 0, message: 'Starting worker...' });

    try {
      this.createWorker();
    } catch (workerErr: any) {
      this.setState({ status: 'error', error: workerErr.message || 'Failed to create worker' });
      throw workerErr;
    }

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
   * Optionally also runs prototype-based calibration when prototypeTexts is provided.
   *
   * @returns The calibrate-done response, which includes both fuzzyData (from raw texts)
   *          and optionally prototypeFuzzyData (from prototype texts if provided).
   */
  async calibrate(
    texts: TextCorpusEntry[],
    conditionSet: ConditionSet,
    prototypeTexts?: TextCase[]
  ): Promise<{ fuzzyData: MembershipDataJSON; prototypeFuzzyData?: MembershipDataJSON }> {
    return this.send<{ fuzzyData: MembershipDataJSON; prototypeFuzzyData?: MembershipDataJSON }>(
      { type: 'calibrate', payload: { texts, conditionSet, prototypeTexts } },
      'calibrate-done',
      'calibrate'
    ).then((result) => {
      console.log(`[pyodide] calibrate done: fuzzyData shape=${result.fuzzyData.membership?.length}x${result.fuzzyData.condition_names?.length}`);
      return result;
    }).catch((err: any) => {
      console.error(`[pyodide] calibrate failed:`, err);
      throw err;
    });
  }

  /**
   * Load a corpus from raw file content via Python TextCorpusReader.
   *
   * The worker writes the raw content to a VFS file, calls
   * TextCorpusReader.read(), and returns parsed TextCorpusEntry[].
   */
  async loadCorpus(
    fileName: string,
    content: string,
    format: 'csv' | 'json' | 'txt' | 'xlsx',
  ): Promise<TextCorpusEntry[]> {
    if (!content || (typeof content === 'string' && !content.trim())) {
      console.error(`[pyodide] loadCorpus failed: content is empty`);
      throw new Error('Corpus content is empty — nothing to parse');
    }
    console.log(`[pyodide] loadCorpus: file=${fileName}, content length=${content.length}, preview="${content.slice(0, 50)}"`);
    try {
      const resp = await this.send<{ entries: TextCorpusEntry[] }>(
        { type: 'load_corpus', payload: { fileName, content, format } },
        'corpus-loaded',
        'load-corpus'
      );
      return resp.entries;
    } catch (err: any) {
      console.error(`[pyodide] loadCorpus failed:`, err);
      throw err;
    }
  }

  /**
   * Run QCA analysis on calibrated fuzzy-set data.
   */
  async analyze(
    fuzzyData: MembershipDataJSON,
    params: QCAAnalysisParams,
    conditionSet?: ConditionSet
  ): Promise<QCAAnalysisResultJSON> {
    console.log(`[pyodide] analyze: fuzzyData shape=${fuzzyData.membership?.length}x${fuzzyData.condition_names?.length}, conditionSet=${conditionSet ? 'provided' : 'none'}`);
    return this.send<QCAAnalysisResultJSON>(
      { type: 'analyze', payload: { fuzzyData, params, conditionSet } },
      'analyze-done',
      'analyze'
    ).then((resp: any) => {
      const result = resp?.result ?? resp;
      console.log('[pyodide] analyze result received:', {
        hasSolutions: !!result?.solutions,
        hasComplex: !!result?.solutions?.complex,
        solution_consistency: result?.solutions?.complex?.solution_consistency,
        solution_coverage: result?.solutions?.complex?.solution_coverage,
        hasConditionSet: !!result?.condition_set,
        conditionNames: result?.condition_set?.conditions?.map((c: any) => c.name),
      });
      return result;
    }).catch((err: any) => {
      console.error(`[pyodide] analyze failed:`, err);
      throw err;
    });

  /**
   * Run robustness/sensitivity tests.
   */
  async runRobustness(
    fuzzyData: MembershipDataJSON,
    analysisResult: QCAAnalysisResultJSON
  ): Promise<RobustnessReport> {
    return this.send<RobustnessReport>(
      { type: 'run_robustness', payload: { fuzzyData, analysisResult } },
      'robustness-done',
      'robustness'
    ).then((resp: any) => {
      // resolveOne returns { type, report }; extract the inner report
      return resp?.report ?? resp;
    }).catch((err: any) => {
      console.error(`[pyodide] robustness failed:`, err);
      throw err;
    });
  }

  /**
   * Run counterfactual analysis.
   */
  async runCounterfactuals(
    fuzzyData: MembershipDataJSON,
    analysisResult: QCAAnalysisResultJSON
  ): Promise<CounterfactualReport> {
    return this.send<CounterfactualReport>(
      { type: 'run_counterfactuals', payload: { fuzzyData, analysisResult } },
      'counterfactuals-done',
      'counterfactuals'
    ).then((resp: any) => {
      // resolveOne returns { type, report }; extract the inner report
      return resp?.report ?? resp;
    }).catch((err: any) => {
      console.error(`[pyodide] counterfactuals failed:`, err);
      throw err;
    });
  }

  /**
   * Export results to CSV, JSON, LaTeX, or DOCX (Word).
   */
  async exportResult(
    format: 'csv' | 'json' | 'latex' | 'docx',
    result: QCAAnalysisResultJSON
  ): Promise<ExportResult> {
    const resp = await this.send<{ data: string | Uint8Array; mimeType: string }>(
      { type: 'export_result', payload: { format, result } },
      'export-done',
      `export-${format}`
    );

    const extMap: Record<string, string> = {
      csv: 'csv',
      json: 'json',
      latex: 'tex',
      docx: 'docx',
    };

    return {
      data: new Blob([resp.data as BlobPart], { type: resp.mimeType }),
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
    return this.send<{ valid: boolean; warnings: string[] }>(
      { type: 'validate_condition_set', payload: { conditionSet } },
      'validate-done',
      'validate'
    ).catch((err: any) => {
      console.error(`[pyodide] validateConditionSet failed:`, err);
      throw err;
    });
  }

  /**
   * Initialise the BERT model in the worker for embedding extraction.
   *
   * The model is lazily loaded on first call; subsequent calls with the
   * same model name are no-ops. Progress events are forwarded as
   * bert-init-progress worker responses.
   */
  async initBert(modelName: string): Promise<void> {
    console.log(`[pyodide] initBert: model=${modelName}`);
    return this.send<void>(
      { type: 'init_bert', payload: { modelName } },
      'bert-init-done',
      'init-bert'
    ).catch((err: any) => {
      console.error(`[pyodide] initBert failed:`, err);
      throw err;
    });
  }

  /**
   * Run embed-based calibration: texts with pre-computed BERT embeddings
   * are scored against condition prototypes via CosineSimilarityEngine
   * (Python side) and then calibrated to fuzzy-set memberships.
   */
  async embedCalibrate(
    texts: EmbedCalibrateTextEntry[],
    conditionSet: any,
  ): Promise<{ fuzzyData: MembershipDataJSON }> {
    console.log(`[pyodide] embedCalibrate: ${texts.length} texts, conditionSet conditions=${conditionSet.conditions?.length}, conditions have prototype_embeddings:`,
      conditionSet.conditions?.map((c: any) => ({
        name: c.name,
        hasPrototypeEmbeddings: c.prototype_embeddings !== null && c.prototype_embeddings !== undefined,
        prototypesCount: c.prototypes?.length ?? 0
      }))
    );
    return this.send<{ fuzzyData: MembershipDataJSON }>(
      { type: 'embed_calibrate', payload: { texts, conditionSet } },
      'embed-calibrate-done',
      'embed-calibrate'
    ).then((result) => {
      console.log(`[pyodide] embedCalibrate done: fuzzyData shape=${result.fuzzyData.membership?.length}x${result.fuzzyData.condition_names?.length}`);
      return result;
    }).catch((err: any) => {
      console.error(`[pyodide] embedCalibrate failed:`, err);
      throw err;
    });
  }

  /**
   * Extract BERT CLS embeddings for a list of texts.
   *
   * @param texts - Input strings to embed.
   * @param batchSize - Max texts per pipeline call (default 16).
   * @returns Array of 768-dim embedding vectors as plain number arrays.
   */
  async computeEmbeddings(
    texts: string[],
    batchSize?: number,
  ): Promise<number[][]> {
    try {
      const resp = await this.send<{ embeddings: number[][] }>(
        { type: 'compute_embeddings', payload: { texts, batchSize } },
        'embeddings-computed',
        'compute-embeddings'
      );
      return resp.embeddings;
    } catch (err: any) {
      console.error(`[pyodide] computeEmbeddings failed:`, err);
      throw err;
    }
  }

  /**
   * Compute BERT embeddings for prototype texts, grouped by condition name.
   *
   * @param prototypes - Record mapping condition names to arrays of prototype texts.
   * @returns Embeddings grouped by condition with labels (default all 1) and weights (default all 1.0).
   */
  async computePrototypeEmbeddings(
    prototypes: Record<string, string[]>,
  ): Promise<Record<string, {embeddings: number[][]; labels: number[]; weights: number[]}>> {
    console.log(`[pyodide] computePrototypeEmbeddings: ${Object.keys(prototypes).length} conditions`);
    try {
      const resp = await this.send<{
        embeddings: Record<string, {embeddings: number[][]; labels: number[]; weights: number[]}>;
      }>(
        { type: 'compute_prototype_embeddings', payload: { prototypes } },
        'prototype-embeddings-computed',
        'compute-prototype-embeddings'
      );
      return resp.embeddings;
    } catch (err: any) {
      console.error(`[pyodide] computePrototypeEmbeddings failed:`, err);
      throw err;
    }
  }

  /**
   * Run multi-outcome comparison on analyses from different outcomes.
   *
   * @param analyses - Record mapping outcome_name → QCAAnalysisResultJSON.
   * @returns MultiOutcomeReport with shared/unique conditions and pairwise similarity.
   */
  async runMultiOutcome(
    analyses: Record<string, QCAAnalysisResultJSON>
  ): Promise<MultiOutcomeReport> {
    return this.send<MultiOutcomeReport>(
      { type: 'multi_outcome', payload: { analyses } },
      'multi-outcome-done',
      'multi-outcome'
    );
  }

  /**
   * Query the current BERT model loading status.
   */
  async getBertStatus(): Promise<{ loaded: boolean; modelName: string | null }> {
    return this.send<{ loaded: boolean; modelName: string | null }>(
      { type: 'get_bert_status' },
      'bert-status',
      'bert-status'
    ).catch((err: any) => {
      console.error(`[pyodide] getBertStatus failed:`, err);
      throw err;
    });
  }

  /**
   * Get BERT engine performance metrics from the worker.
   */
  async getBertMetrics(): Promise<import('../services/bert-engine').PerformanceMetrics> {
    return this.send<import('../services/bert-engine').PerformanceMetrics>(
      { type: 'get_bert_metrics', payload: undefined as any },
      'bert-metrics',
      'bert-metrics'
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
      { type: 'module' },
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
          break;
        case 'init-error':
          this.setState({ status: 'error', error: msg.error });
          break;
        case 'terminated':
          this.setState({ status: 'unloaded' });
          return;
        case 'log':
          this.logListeners.forEach((cb) =>
            cb({ ts: Date.now(), level: msg.level, message: msg.message })
          );
          return;
        // BERT lifecycle — progress events must not resolve the initBert promise
        case 'bert-init-progress':
          return;
        case 'bert-init-done':
        case 'bert-init-error':
          break;
      }

      // Route response to the pending request that matches this message type
      this.resolveOne(msg);
    };

    this.worker.onerror = (err: ErrorEvent) => {
      // err.message is often sanitized for cross-origin workers.
      // err.error?.stack gives the actual JS stack trace when available.
      const detail = err.error?.stack || err.error?.message || err.message || 'Unknown worker error';
      console.error('Pyodide worker error:', detail);
      this.setState({
        status: 'error',
        error: detail,
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
        const op = timeoutOperation || request.type;
        console.error(`[PyodideBridge] Worker timed out for ${op}`);
        reject(new PyodideTimeoutError(op));
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
        const errMsg = (msg as any).error || 'Unknown error';
        console.error(`[PyodideBridge] Worker returned error type="${msg.type}":`, errMsg);
        pending.reject(new Error(errMsg));
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
