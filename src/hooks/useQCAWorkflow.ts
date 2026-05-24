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
import { DEFAULT_QCA_PARAMS, QCAVariant } from '../types/qca';

/** Read the configured QCA variant from localStorage settings. */
function getQCAVariantFromSettings(): QCAVariant {
  try {
    const raw = localStorage.getItem('qca-settings');
    if (raw) {
      const settings = JSON.parse(raw);
      if (settings.qca_variant === 'csqca') return QCAVariant.CSQCA;
    }
  } catch {}
  return QCAVariant.FSQCA;
}

/** Ensure conditionSet has qca_variant set, falling back to localStorage. */
function ensureQCAVariant(cs: ConditionSet): ConditionSet {
  if (cs.qca_variant) return cs;
  return { ...cs, qca_variant: getQCAVariantFromSettings() };
}

interface UseQCAWorkflowReturn {
  /** Run the full pipeline end-to-end */
  runFullPipeline: (opts: {
    texts: TextCorpusEntry[];
    conditionSet: ConditionSet;
    params?: Partial<QCAAnalysisParams>;
    runRobustness?: boolean;
    runCounterfactuals?: boolean;
    prototypeTexts?: TextCase[];
  }) => Promise<void>;

  /** Run only calibration (texts → fuzzy-set data) */
  runCalibrateOnly: (opts: {
    texts: TextCorpusEntry[];
    conditionSet: ConditionSet;
    prototypeTexts?: TextCase[];
  }) => Promise<void>;

  /** Run only analysis (fuzzy-set → QCA results), assumes data already calibrated */
  runAnalyzeOnly: (opts: {
    params?: Partial<QCAAnalysisParams>;
    usePrototype?: boolean;
  }) => Promise<void>;

  /** Run QCA analysis on prototype fuzzy data */
  runAnalyzeOnlyForPrototype: (opts: {
    params?: Partial<QCAAnalysisParams>;
  }) => Promise<void>;

  /** Export current results */
  runExport: (format: 'csv' | 'json' | 'latex') => Promise<Blob>;

  /** Load a text corpus from raw content via Python TextCorpusReader */
  loadCorpus: (
    fileName: string,
    content: string,
    format: 'csv' | 'json' | 'txt' | 'xlsx',
  ) => Promise<TextCorpusEntry[]>;

  /** Import a keyword dictionary from CSV/JSON */
  importKeywords: (
    fileName: string,
    content: string,
    format: 'csv' | 'json',
    domain?: string,
  ) => Promise<ConditionSet>;

  /** Export the current condition set keyword dictionary to CSV/JSON */
  exportKeywords: (
    conditionSet: ConditionSet,
    format: 'csv' | 'json',
  ) => Promise<Blob>;

  /** Abort any running operation */
  abort: () => void;
}

export function useQCAWorkflow(): UseQCAWorkflowReturn {
  const { bridge, init } = usePyodide();
  const {
    state,
    startCalibration,
    finishCalibration,
    startAnalysis,
    finishAnalysis,
    startPrototypeAnalysis,
    finishPrototypeAnalysis,
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
    async (opts: { texts: TextCorpusEntry[]; conditionSet: ConditionSet; prototypeTexts?: TextCase[] }) => {
      try {
        await ensureReady();

        const conditionSet = ensureQCAVariant(opts.conditionSet);

        // Validate condition set in Python
        const validation = await bridge.validateConditionSet(conditionSet);
        if (!validation.valid && validation.warnings.length > 0) {
          console.warn('Condition set warnings:', validation.warnings);
        }

        setConditionSet(conditionSet);
        startCalibration();

        const result = await bridge.calibrate(opts.texts, conditionSet, opts.prototypeTexts);
        finishCalibration(result.fuzzyData, result.prototypeFuzzyData);
      } catch (err: any) {
        fail(err.message || 'Calibration failed');
        throw err;
      }
    },
    [ensureReady, bridge, setConditionSet, startCalibration, finishCalibration, fail]
  );


  const runAnalyzeOnly = useCallback(
    async (opts: { params?: Partial<QCAAnalysisParams>; usePrototype?: boolean }) => {
      try {
        await ensureReady();

        const fuzzyData = opts.usePrototype ? state.prototypeFuzzyData : state.fuzzyData;
        if (!fuzzyData) {
          const label = opts.usePrototype ? 'prototype ' : '';
          throw new Error(`No ${label}fuzzy-set data available. Run calibration first.`);
        }

        const params: QCAAnalysisParams = {
          ...DEFAULT_QCA_PARAMS,
          ...opts.params,
        };

        if (opts.usePrototype) {
          startPrototypeAnalysis();
          const result = await bridge.analyze(fuzzyData, params);
          finishPrototypeAnalysis(result);
        } else {
          startAnalysis();
          const result = await bridge.analyze(fuzzyData, params);
          finishAnalysis(result);
        }
      } catch (err: any) {
        fail(err.message || 'Analysis failed');
        throw err;
      }
    },
    [ensureReady, bridge, state.fuzzyData, state.prototypeFuzzyData, startAnalysis, finishAnalysis, startPrototypeAnalysis, finishPrototypeAnalysis, fail]
  );

  const runAnalyzeOnlyForPrototype = useCallback(
    async (opts: { params?: Partial<QCAAnalysisParams> }) => {
      return runAnalyzeOnly({ ...opts, usePrototype: true });
    },
    [runAnalyzeOnly]
  );

  const runFullPipeline = useCallback(
    async (opts: {
      texts: TextCorpusEntry[];
      conditionSet: ConditionSet;
      params?: Partial<QCAAnalysisParams>;
      runRobustness?: boolean;
      runCounterfactuals?: boolean;
      prototypeTexts?: TextCase[];
    }) => {
      try {
        await ensureReady();

        const conditionSet = ensureQCAVariant(opts.conditionSet);

        // 1. Validate
        const validation = await bridge.validateConditionSet(conditionSet);
        if (!validation.valid && validation.warnings.length > 0) {
          console.warn('Condition set warnings:', validation.warnings);
        }

        setConditionSet(conditionSet);

        // 2. Calibrate
        startCalibration();
        const calResult = await bridge.calibrate(opts.texts, conditionSet, opts.prototypeTexts);
        const fuzzyData = calResult.fuzzyData;
        finishCalibration(fuzzyData, calResult.prototypeFuzzyData);

        // 3. Analyze (raw texts)
        const params: QCAAnalysisParams = {
          ...DEFAULT_QCA_PARAMS,
          ...opts.params,
        };
        startAnalysis();
        const result = await bridge.analyze(fuzzyData, params);
        finishAnalysis(result);

        // 3b. Analyze (prototype texts) — if prototype data exists
        const protoFuzzy = calResult.prototypeFuzzyData;
        if (protoFuzzy) {
          startPrototypeAnalysis();
          const protoResult = await bridge.analyze(protoFuzzy, params);
          finishPrototypeAnalysis(protoResult);
        }

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
      startPrototypeAnalysis, finishPrototypeAnalysis,
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
      format: 'csv' | 'json' | 'txt' | 'xlsx',
    ): Promise<TextCorpusEntry[]> => {
      await ensureReady();
      return bridge.loadCorpus(fileName, content, format);
    },
    [ensureReady, bridge],
  );

  const importKeywordsFn = useCallback(
    async (
      fileName: string,
      content: string,
      format: 'csv' | 'json',
      domain: string = 'dissatisfaction',
    ): Promise<ConditionSet> => {
      await ensureReady();
      return bridge.importKeywords(fileName, content, format, domain);
    },
    [ensureReady, bridge],
  );

  const exportKeywordsFn = useCallback(
    async (
      conditionSet: ConditionSet,
      format: 'csv' | 'json',
    ): Promise<Blob> => {
      await ensureReady();
      const exported = await bridge.exportKeywords(conditionSet, format);
      return exported.data;
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
    runAnalyzeOnly,
    runAnalyzeOnlyForPrototype,
    runExport,
    loadCorpus: loadCorpusFn,
    importKeywords: importKeywordsFn,
    exportKeywords: exportKeywordsFn,
    abort,
  };
}
