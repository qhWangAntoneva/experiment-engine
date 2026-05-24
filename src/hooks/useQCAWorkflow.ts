/**
 * Hook that ties the Pyodide bridge to the pipeline state context.
 *
 * Orchestrates the full QCA workflow:
 *   1. Validate condition set
 *   2. Calibrate texts → fuzzy-set membership
 *   3. Analyze (truth table + minimization + necessity/sufficiency)
 *   4. [Optional] Robustness tests
 *   5. [Optional] Counterfactual analysis
 *   6. Export results
 */

import { useCallback } from 'react';
import { usePyodide } from './usePyodide';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import type {
  TextCorpusEntry,
  TextCase,
  ConditionSet,
  QCAAnalysisParams,
} from '../types/qca';
import { DEFAULT_QCA_PARAMS } from '../types/qca';

interface UseQCAWorkflowReturn {
  /** Run the full pipeline end-to-end */
  runFullPipeline: (opts: {
    texts: TextCorpusEntry[];
    conditionSet: ConditionSet;
    params?: Partial<QCAAnalysisParams>;
    runRobustness?: boolean;
    runCounterfactuals?: boolean;
  }) => Promise<void>;

  /** Run only calibration (texts → fuzzy-set data) — keyword mode */
  runCalibrateOnly: (opts: {
    texts: TextCorpusEntry[];
    conditionSet: ConditionSet;
  }) => Promise<void>;

  /** Run prototype-based calibration only */
  runPrototypeCalibration: (opts: {
    texts: TextCase[];
    conditionSet: ConditionSet;
  }) => Promise<void>;

  /** Run full prototype pipeline (calibrate → analyze → robustness → export) */
  runPrototypeFullPipeline: (opts: {
    texts: TextCase[];
    conditionSet: ConditionSet;
    params?: Partial<QCAAnalysisParams>;
    runRobustness?: boolean;
    runCounterfactuals?: boolean;
  }) => Promise<void>;

  /** Run only analysis (fuzzy-set → QCA results), assumes data already calibrated */
  runAnalyzeOnly: (opts: {
    params?: Partial<QCAAnalysisParams>;
  }) => Promise<void>;

  /** Export current results */
  runExport: (format: 'csv' | 'json' | 'latex') => Promise<Blob>;

  /** Load a text corpus from raw content via Python TextCorpusReader */
  loadCorpus: (
    fileName: string,
    content: string,
    format: 'csv' | 'json' | 'txt',
  ) => Promise<TextCorpusEntry[]>;

  /** Abort any running operation */
  abort: () => void;
}

export function useQCAWorkflow(): UseQCAWorkflowReturn {
  const { bridge, init } = usePyodide();
  const {
    state,
    startCalibration,
    finishCalibration,
    startPrototypeCalibration,
    finishPrototypeCalibration,
    startAnalysis,
    finishAnalysis,
    startRobustness,
    finishRobustness,
    startCounterfactuals,
    finishCounterfactuals,
    finishExport,
    fail,
    setConditionSet,
  } = useQCAPipeline();

  const ensureReady = useCallback(async () => {
    if (bridge.getInitState().status !== 'ready') {
      await init();
    }
  }, [bridge, init]);

  const runCalibrateOnly = useCallback(
    async (opts: { texts: TextCorpusEntry[]; conditionSet: ConditionSet }) => {
      try {
        await ensureReady();

        // Validate condition set in Python
        const validation = await bridge.validateConditionSet(opts.conditionSet);
        if (!validation.valid && validation.warnings.length > 0) {
          console.warn('Condition set warnings:', validation.warnings);
        }

        setConditionSet(opts.conditionSet);
        startCalibration();

        const fuzzyData = await bridge.calibrate(opts.texts, opts.conditionSet);
        finishCalibration(fuzzyData);
      } catch (err: any) {
        fail(err.message || 'Calibration failed');
        throw err;
      }
    },
    [ensureReady, bridge, setConditionSet, startCalibration, finishCalibration, fail]
  );

  const runPrototypeCalibration = useCallback(
    async (opts: { texts: TextCase[]; conditionSet: ConditionSet }) => {
      try {
        await ensureReady();

        if (opts.texts.length === 0) {
          throw new Error('No text cases provided for prototype calibration.');
        }

        setConditionSet(opts.conditionSet);
        startPrototypeCalibration();

        const fuzzyData = await bridge.calibratePrototype(opts.texts, opts.conditionSet);
        finishPrototypeCalibration(fuzzyData);
      } catch (err: any) {
        fail(err.message || 'Prototype calibration failed');
        throw err;
      }
    },
    [ensureReady, bridge, setConditionSet, startPrototypeCalibration, finishPrototypeCalibration, fail]
  );

  const runPrototypeFullPipeline = useCallback(
    async (opts: {
      texts: TextCase[];
      conditionSet: ConditionSet;
      params?: Partial<QCAAnalysisParams>;
      runRobustness?: boolean;
      runCounterfactuals?: boolean;
    }) => {
      try {
        await ensureReady();

        if (opts.texts.length === 0) {
          throw new Error('No text cases provided.');
        }

        setConditionSet(opts.conditionSet);

        // 1. Prototype calibration
        startPrototypeCalibration();
        const fuzzyData = await bridge.calibratePrototype(opts.texts, opts.conditionSet);
        finishPrototypeCalibration(fuzzyData);

        // 2. Analyze
        const params: QCAAnalysisParams = {
          ...DEFAULT_QCA_PARAMS,
          ...opts.params,
        };
        startAnalysis();
        const result = await bridge.analyze(fuzzyData, params);
        finishAnalysis(result);

        // 3. Robustness (optional)
        if (opts.runRobustness) {
          startRobustness();
          const robustnessReport = await bridge.runRobustness(fuzzyData, result);
          finishRobustness(robustnessReport);
        }

        // 4. Counterfactuals (optional)
        if (opts.runCounterfactuals) {
          startCounterfactuals();
          const cfReport = await bridge.runCounterfactuals(fuzzyData, result);
          finishCounterfactuals(cfReport);
        }

        finishExport([]);
      } catch (err: any) {
        fail(err.message || 'Prototype pipeline failed');
        throw err;
      }
    },
    [
      ensureReady, bridge, setConditionSet,
      startPrototypeCalibration, finishPrototypeCalibration,
      startAnalysis, finishAnalysis,
      startRobustness, finishRobustness,
      startCounterfactuals, finishCounterfactuals,
      finishExport, fail,
    ]
  );

  const runAnalyzeOnly = useCallback(
    async (opts: { params?: Partial<QCAAnalysisParams> }) => {
      try {
        await ensureReady();

        if (!state.fuzzyData) {
          throw new Error('No fuzzy-set data available. Run calibration first.');
        }

        const params: QCAAnalysisParams = {
          ...DEFAULT_QCA_PARAMS,
          ...opts.params,
        };

        startAnalysis();
        const result = await bridge.analyze(state.fuzzyData, params);
        finishAnalysis(result);
      } catch (err: any) {
        fail(err.message || 'Analysis failed');
        throw err;
      }
    },
    [ensureReady, bridge, state.fuzzyData, startAnalysis, finishAnalysis, fail]
  );

  const runFullPipeline = useCallback(
    async (opts: {
      texts: TextCorpusEntry[];
      conditionSet: ConditionSet;
      params?: Partial<QCAAnalysisParams>;
      runRobustness?: boolean;
      runCounterfactuals?: boolean;
    }) => {
      try {
        await ensureReady();

        // 1. Validate
        const validation = await bridge.validateConditionSet(opts.conditionSet);
        if (!validation.valid && validation.warnings.length > 0) {
          console.warn('Condition set warnings:', validation.warnings);
        }

        setConditionSet(opts.conditionSet);

        // 2. Calibrate
        startCalibration();
        const fuzzyData = await bridge.calibrate(opts.texts, opts.conditionSet);
        finishCalibration(fuzzyData);

        // 3. Analyze
        const params: QCAAnalysisParams = {
          ...DEFAULT_QCA_PARAMS,
          ...opts.params,
        };
        startAnalysis();
        const result = await bridge.analyze(fuzzyData, params);
        finishAnalysis(result);

        // 4. Robustness (optional)
        if (opts.runRobustness) {
          startRobustness();
          const robustnessReport = await bridge.runRobustness(fuzzyData, result);
          finishRobustness(robustnessReport);
        }

        // 5. Counterfactuals (optional)
        if (opts.runCounterfactuals) {
          startCounterfactuals();
          const cfReport = await bridge.runCounterfactuals(fuzzyData, result);
          finishCounterfactuals(cfReport);
        }

        finishExport([]);
      } catch (err: any) {
        fail(err.message || 'Pipeline failed');
        throw err;
      }
    },
    [
      ensureReady, bridge, setConditionSet,
      startCalibration, finishCalibration,
      startAnalysis, finishAnalysis,
      startRobustness, finishRobustness,
      startCounterfactuals, finishCounterfactuals,
      finishExport, fail,
    ]
  );

  const runExport = useCallback(
    async (format: 'csv' | 'json' | 'latex'): Promise<Blob> => {
      if (!state.analysisResult) {
        throw new Error('No analysis result to export');
      }
      const exported = await bridge.exportResult(format, state.analysisResult);
      return exported.data;
    },
    [bridge, state.analysisResult]
  );

  const loadCorpusFn = useCallback(
    async (
      fileName: string,
      content: string,
      format: 'csv' | 'json' | 'txt',
    ): Promise<TextCorpusEntry[]> => {
      await ensureReady();
      return bridge.loadCorpus(fileName, content, format);
    },
    [ensureReady, bridge],
  );

  const abort = useCallback(() => {
    // Web Workers cannot be cancelled mid-operation, but we can terminate and re-create
    bridge.terminate();
    fail('Aborted by user');
  }, [bridge, fail]);

  return {
    runFullPipeline,
    runCalibrateOnly,
    runPrototypeCalibration,
    runPrototypeFullPipeline,
    runAnalyzeOnly,
    runExport,
    loadCorpus: loadCorpusFn,
    abort,
  };
}
