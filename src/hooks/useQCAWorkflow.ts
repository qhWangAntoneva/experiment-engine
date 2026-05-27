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
  EmbedCalibrateTextEntry,
  ConditionSet,
  ConditionDefinition,
  QCAAnalysisParams,
  QCAAnalysisResultJSON,
} from '../types/qca';
import { DEFAULT_QCA_PARAMS, QCAVariant, CalibrationMethod } from '../types/qca';
import { DEFAULT_MODEL } from '../services/bert-engine';

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

/** Read the configured BERT model name from localStorage settings. */
function getBertModelFromSettings(): string {
  try {
    return localStorage.getItem('qca-bert-model') || DEFAULT_MODEL;
  } catch {
    return DEFAULT_MODEL;
  }
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
    captureAsLabel?: 'a' | 'b';
  }) => Promise<void>;

  /** Run full pipeline with multi-outcome comparison */
  runFullPipelineMultiOutcome: (opts: {
    texts: TextCorpusEntry[];
    conditionSet: ConditionSet;
    outcomeBName: string;
    outcomeBDisplayName: string;
    params?: Partial<QCAAnalysisParams>;
    runRobustness?: boolean;
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
    captureAsLabel?: 'a' | 'b';
  }) => Promise<void>;

  /** Run QCA analysis on prototype fuzzy data */
  runAnalyzeOnlyForPrototype: (opts: {
    params?: Partial<QCAAnalysisParams>;
  }) => Promise<void>;

  /** Initialize BERT model for embedding-based calibration */
  initBert: (modelName?: string) => Promise<void>;

  /** Run embedding-based calibration using BERT */
  runEmbedCalibrate: (opts: {
    texts: TextCorpusEntry[];
    conditionSet: ConditionSet;
  }) => Promise<void>;

  /** Export current results */
  runExport: (format: 'csv' | 'json' | 'latex' | 'docx') => Promise<Blob>;

  /** Load a text corpus from raw content via Python TextCorpusReader */
  loadCorpus: (
    fileName: string,
    content: string,
    format: 'csv' | 'json' | 'txt' | 'xlsx',
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
    startAnalysis,
    finishAnalysis,
    startPrototypeAnalysis,
    finishPrototypeAnalysis,
    startRobustness,
    finishRobustness,
    startCounterfactuals,
    finishCounterfactuals,
    startSecondOutcomeAnalysis,
    finishSecondOutcomeAnalysis,
    startMultiOutcomeComparison,
    finishMultiOutcomeComparison,
    finishExport,
    fail,
    setConditionSet,
    startBertLoading,
    finishBertLoading,
    setBertStatus,
    startEmbedding,
    finishEmbedding,
  } = useQCAPipeline();

  const ensureReady = useCallback(async () => {
    if (bridge.getInitState().status !== 'ready') {
      await init();
    }
  }, [bridge, init]);

  const initBert = useCallback(
    async (modelName?: string) => {
      try {
        await ensureReady();
        startBertLoading();
        await bridge.initBert(modelName || getBertModelFromSettings());
        finishBertLoading();
      } catch (err: any) {
        setBertStatus('error', err.message || 'BERT initialization failed');
        fail(err.message || 'BERT initialization failed');
        throw err;
      }
    },
    [ensureReady, bridge, startBertLoading, finishBertLoading, setBertStatus, fail]
  );

  const runEmbedCalibrate = useCallback(
    async (opts: { texts: TextCorpusEntry[]; conditionSet: ConditionSet }) => {
      try {
        await ensureReady();

        // Check BERT is loaded
        const bertStatus = await bridge.getBertStatus();
        if (!bertStatus.loaded) {
          throw new Error('BERT model not loaded. Please load the BERT model first.');
        }

        const conditionSet = ensureQCAVariant(opts.conditionSet);
        setConditionSet(conditionSet);
        startEmbedding();

        // Build prototype texts grouped by condition
        const prototypeTextsByCondition: Record<string, string[]> = {};
        for (const cond of conditionSet.conditions) {
          if (cond.prototypes && cond.prototypes.length > 0) {
            prototypeTextsByCondition[cond.name] = cond.prototypes.map(
              (p) => p.prototype_text
            );
          }
        }

        if (Object.keys(prototypeTextsByCondition).length === 0) {
          throw new Error(
            'No prototype texts found in condition set. ' +
            'Each condition must have at least one prototype text for BERT calibration.'
          );
        }

        // Compute prototype embeddings
        const protoEmbeddings = await bridge.computePrototypeEmbeddings(
          prototypeTextsByCondition
        );

        // Attach prototype embeddings to condition definitions
        const enrichedConditions = conditionSet.conditions.map((cond) => {
          const embResult = protoEmbeddings[cond.name];
          return {
            ...cond,
            prototype_embeddings: embResult ? embResult.embeddings : null,
            embedding_model: embResult ? getBertModelFromSettings() : null,
          };
        });

        const enrichedConditionSet = {
          ...conditionSet,
          conditions: enrichedConditions,
        };

        // Compute text embeddings
        const textStrings = opts.texts.map((t) => t.text);
        const textEmbeddings = await bridge.computeEmbeddings(textStrings);

        finishEmbedding();

        // Build EmbedCalibrateTextEntry[]
        const textsWithEmbeds: EmbedCalibrateTextEntry[] = opts.texts.map(
          (t, i) => ({
            text_id: t.text_id,
            text: t.text,
            embedding: textEmbeddings[i],
          })
        );

        // Run embed calibration
        const result = await bridge.embedCalibrate(
          textsWithEmbeds,
          enrichedConditionSet
        );

        finishCalibration(result.fuzzyData, undefined);
      } catch (err: any) {
        fail(err.message || 'BERT calibration failed');
        throw err;
      }
    },
    [
      ensureReady, bridge, setConditionSet,
      startEmbedding, finishEmbedding, finishCalibration, fail,
    ]
  );

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
    async (opts: { params?: Partial<QCAAnalysisParams>; usePrototype?: boolean; captureAsLabel?: 'a' | 'b' }) => {
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
          finishAnalysis(result, opts.captureAsLabel);
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
      captureAsLabel?: 'a' | 'b';
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
        const result = await bridge.analyze(fuzzyData, params, conditionSet);
        finishAnalysis(result, opts.captureAsLabel);

        // 3b. Analyze (prototype texts) — if prototype data exists
        const protoFuzzy = calResult.prototypeFuzzyData;
        if (protoFuzzy) {
          startPrototypeAnalysis();
          const protoResult = await bridge.analyze(protoFuzzy, params, conditionSet);
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

  const runFullPipelineMultiOutcome = useCallback(
    async (opts: {
      texts: TextCorpusEntry[];
      conditionSet: ConditionSet;
      outcomeBName: string;
      outcomeBDisplayName: string;
      params?: Partial<QCAAnalysisParams>;
      runRobustness?: boolean;
    }) => {
      try {
        await ensureReady();

        const conditionSetA = ensureQCAVariant(opts.conditionSet);

        // 1. Validate
        const validation = await bridge.validateConditionSet(conditionSetA);
        if (!validation.valid && validation.warnings.length > 0) {
          console.warn('Condition set warnings:', validation.warnings);
        }

        setConditionSet(conditionSetA);

        const params: QCAAnalysisParams = {
          ...DEFAULT_QCA_PARAMS,
          ...opts.params,
        };

        // 2. Calibrate + Analyze for Outcome A
        startCalibration();
        const calResult = await bridge.calibrate(opts.texts, conditionSetA);
        const fuzzyDataA = calResult.fuzzyData;
        finishCalibration(fuzzyDataA, calResult.prototypeFuzzyData);

        startAnalysis();
        const resultA = await bridge.analyze(fuzzyDataA, params, conditionSetA);
        finishAnalysis(resultA);

        // 3. Modify condition set for Outcome B
        const existingOutcome = conditionSetA.outcome;
        const protoOutcomeB: ConditionDefinition = {
          name: opts.outcomeBName,
          display_name: opts.outcomeBDisplayName,
          domain: existingOutcome?.domain ?? 'dissatisfaction',
          calibration_type: existingOutcome?.calibration_type ?? CalibrationMethod.DIRECT,
          calibration_params: existingOutcome?.calibration_params ?? {
            threshold_full_in: 0.80,
            threshold_full_out: 0.20,
            crossover_point: 0.50,
            direction: 'ascending',
          },
          description: '',
          scoring_source: 'prototype',
          prototypes: existingOutcome?.prototypes ?? [],
          prototype_embeddings: existingOutcome?.prototype_embeddings ?? null,
          embedding_model: existingOutcome?.embedding_model ?? null,
        };

        const conditionSetB: ConditionSet = {
          ...conditionSetA,
          name: `${conditionSetA.name}-outcome-b`,
          outcome: protoOutcomeB,
        };

        // 4. Calibrate for Outcome B
        // Use the same texts but with Outcome B's condition set
        startCalibration();
        const calResultB = await bridge.calibrate(opts.texts, conditionSetB);
        const fuzzyDataB = calResultB.fuzzyData;
        finishCalibration(fuzzyDataB, calResultB.prototypeFuzzyData);

        // 5. Analyze Outcome B
        let resultB: QCAAnalysisResultJSON | null = null;
        try {
          startSecondOutcomeAnalysis();
          resultB = await bridge.analyze(fuzzyDataB, params, conditionSetB);
          finishSecondOutcomeAnalysis(resultB);
        } catch (errB: any) {
          // If Outcome B analysis fails, preserve Outcome A results
          console.warn('Outcome B analysis failed, preserving Outcome A:', errB.message);
        }

        // 6. Robustness (optional, on Outcome A data)
        if (opts.runRobustness) {
          startRobustness();
          const robustnessReport = await bridge.runRobustness(fuzzyDataA, resultA);
          finishRobustness(robustnessReport);
        }

        // 7. Multi-outcome comparison (only if both succeeded)
        if (resultB) {
          startMultiOutcomeComparison();
          const analyses: Record<string, QCAAnalysisResultJSON> = {};
          const outcomeAName = existingOutcome?.display_name || existingOutcome?.name || 'Outcome A';
          analyses[outcomeAName] = resultA;
          analyses[opts.outcomeBDisplayName || opts.outcomeBName] = resultB;
          const moReport = await bridge.runMultiOutcome(analyses);
          finishMultiOutcomeComparison(moReport);
        }

        finishExport([]);
      } catch (err: any) {
        fail(err.message || 'Multi-outcome pipeline failed');
        throw err;
      }
    },
    [
      ensureReady, bridge, setConditionSet,
      startCalibration, finishCalibration,
      startAnalysis, finishAnalysis,
      startSecondOutcomeAnalysis, finishSecondOutcomeAnalysis,
      startMultiOutcomeComparison, finishMultiOutcomeComparison,
      startRobustness, finishRobustness,
      finishExport, fail,
    ]
  );

  const runExport = useCallback(
    async (format: 'csv' | 'json' | 'latex' | 'docx'): Promise<Blob> => {
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

  const abort = useCallback(() => {
    // Web Workers cannot be cancelled mid-operation, but we can terminate and re-create
    bridge.terminate();
    fail('Aborted by user');
  }, [bridge, fail]);

  return {
    runFullPipeline,
    runFullPipelineMultiOutcome,
    runCalibrateOnly,
    runAnalyzeOnly,
    runAnalyzeOnlyForPrototype,
    initBert,
    runEmbedCalibrate,
    runExport,
    loadCorpus: loadCorpusFn,
    abort,
  };
}
