/**
 * React Context for tracking the QCA pipeline lifecycle.
 *
 * Provides:
 *   - pipelineState: current stage, progress, results, errors
 *   - dispatch: action dispatcher for stage transitions
 *   - mutations: high-level methods (startCalibration, startAnalysis, etc.)
 *
 * This is intentionally lightweight — no external state library needed.
 * The pipeline is strictly sequential (calibrate → analyze → robust → export),
 * so a simple reducer with an enum-like stage field is sufficient.
 */

import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useRef,
  useEffect,
  type ReactNode,
  type Dispatch,
} from 'react';
import type {
  QCAPipelineState,
  PipelineStage,
  MembershipDataJSON,
  QCAAnalysisResultJSON,
  RobustnessReport,
  CounterfactualReport,
  MultiOutcomeReport,
  ConditionSet,
  SavedAnalysisRun,
  TextCorpusEntry,
  TextCase,
  QCAProjectProtoConditionRow,
  ParameterSnapshot,
} from '../types/qca';
import { INITIAL_PIPELINE_STATE, DEFAULT_QCA_PARAMS } from '../types/qca';
import { PerformanceMetrics } from '../services/bert-engine';
import { saveSnapshot } from '../utils/snapshotStorage';

// ─── Recent Runs Persistence ─────────────────────────────────────────────────

const RECENT_RUNS_KEY = 'qca-recent-runs';
const RECENT_RUNS_MAX = 20;
const RECENT_RUNS_EVENT = 'recent-runs-updated';
let _runIdCounter = 0;

function persistRecentRun(run: SavedAnalysisRun): void {
  try {
    let runs: SavedAnalysisRun[] = [];
    const saved = localStorage.getItem(RECENT_RUNS_KEY);
    if (saved) {
      runs = JSON.parse(saved);
    }
    runs.unshift(run);
    if (runs.length > RECENT_RUNS_MAX) {
      runs = runs.slice(0, RECENT_RUNS_MAX);
    }
    localStorage.setItem(RECENT_RUNS_KEY, JSON.stringify(runs));
    window.dispatchEvent(new Event(RECENT_RUNS_EVENT));
  } catch {
    // localStorage full or unavailable — silently skip
  }
}

// ─── Actions ───────────────────────────────────────────────────────────────

export type PipelineAction =
  | { type: 'RESET' }
  | { type: 'SET_STAGE'; stage: PipelineStage; message?: string }
  | { type: 'SET_PROGRESS'; progress: number; message?: string }
  | { type: 'SET_ERROR'; error: string }
  | { type: 'SET_CONDITION_SET'; conditionSet: ConditionSet }
  | { type: 'SET_FUZZY_DATA'; fuzzyData: MembershipDataJSON; prototypeFuzzyData?: MembershipDataJSON }
  | { type: 'SET_ANALYSIS_RESULT'; result: QCAAnalysisResultJSON }
  | { type: 'SET_PROTOTYPE_ANALYSIS_RESULT'; result: QCAAnalysisResultJSON }
  | { type: 'SET_ROBUSTNESS_REPORT'; report: RobustnessReport }
  | { type: 'SET_COUNTERFACTUAL_REPORT'; report: CounterfactualReport }
  | { type: 'SET_ANALYSIS_RESULT_B'; result: QCAAnalysisResultJSON }
  | { type: 'SET_MULTI_OUTCOME_REPORT'; report: MultiOutcomeReport }
  | { type: 'SET_EXPORT_FORMATS'; formats: string[] }
  | { type: 'SET_BERT_STATUS'; status: 'unloaded' | 'loading' | 'ready' | 'error'; message?: string }
  | { type: 'SET_EMBEDDINGS_READY'; embeddings: number[][] }
  | { type: 'SET_PERFORMANCE_METRICS'; metrics: PerformanceMetrics }
  | { type: 'SET_TEXT_CORPUS'; entries: TextCorpusEntry[] }
  | { type: 'SET_TEXT_CASES'; cases: TextCase[] }
  | { type: 'SET_YAML_CONTENT'; content: string }
  | { type: 'SET_PROTO_CONDITIONS'; rows: QCAProjectProtoConditionRow[] }
  | { type: 'HYDRATE_FROM_PROJECT'; snapshot: {
      stage: PipelineStage;
      conditionSet: ConditionSet | null;
      fuzzyData: MembershipDataJSON | null;
      prototypeFuzzyData: MembershipDataJSON | null;
      analysisResult: QCAAnalysisResultJSON | null;
      prototypeAnalysisResult: QCAAnalysisResultJSON | null;
      analysisResultB: QCAAnalysisResultJSON | null;
      robustnessReport: RobustnessReport | null;
      counterfactualReport: CounterfactualReport | null;
      multiOutcomeReport: MultiOutcomeReport | null;
  } }
  | { type: 'TICK_ELAPSED' }; // heartbeat for timing

// ─── Reducer ───────────────────────────────────────────────────────────────

function pipelineReducer(
  state: QCAPipelineState,
  action: PipelineAction
): QCAPipelineState {
  switch (action.type) {
    case 'RESET':
      return { ...INITIAL_PIPELINE_STATE };

    case 'SET_STAGE':
      return {
        ...state,
        stage: action.stage,
        message: action.message ?? state.message,
        progress: action.stage === 'idle' ? 0 : state.progress,
        error: null,
      };

    case 'SET_PROGRESS':
      return {
        ...state,
        progress: action.progress,
        message: action.message ?? state.message,
      };

    case 'SET_ERROR':
      return {
        ...state,
        stage: 'error',
        error: action.error,
        message: action.error,
      };

    case 'SET_CONDITION_SET':
      return { ...state, conditionSet: action.conditionSet };

    case 'SET_FUZZY_DATA':
      return {
        ...state,
        fuzzyData: action.fuzzyData,
        prototypeFuzzyData: action.prototypeFuzzyData ?? state.prototypeFuzzyData,
      };

    case 'SET_ANALYSIS_RESULT':
      return { ...state, analysisResult: action.result };

    case 'SET_PROTOTYPE_ANALYSIS_RESULT':
      return { ...state, prototypeAnalysisResult: action.result };

    case 'SET_ROBUSTNESS_REPORT':
      return { ...state, robustnessReport: action.report };

    case 'SET_COUNTERFACTUAL_REPORT':
      return { ...state, counterfactualReport: action.report };

    case 'SET_ANALYSIS_RESULT_B':
      return { ...state, analysisResultB: action.result };

    case 'SET_MULTI_OUTCOME_REPORT':
      return { ...state, multiOutcomeReport: action.report };

    case 'SET_EXPORT_FORMATS':
      return { ...state, exportFormats: action.formats };

    case 'SET_BERT_STATUS':
      return {
        ...state,
        bertStatus: action.status,
        bertMessage: action.message ?? state.bertMessage,
      };

    case 'SET_EMBEDDINGS_READY':
      return { ...state, bertEmbeddingsReady: true };

    case 'SET_PERFORMANCE_METRICS':
      return { ...state, performanceMetrics: action.metrics };

    case 'SET_TEXT_CORPUS':
      return { ...state, textCorpusEntries: action.entries };

    case 'SET_TEXT_CASES':
      return { ...state, textCases: action.cases };

    case 'SET_YAML_CONTENT':
      return { ...state, yamlContent: action.content };

    case 'SET_PROTO_CONDITIONS':
      return { ...state, protoConditions: action.rows };

    case 'HYDRATE_FROM_PROJECT': {
      const snap = action.snapshot;
      return {
        ...INITIAL_PIPELINE_STATE,
        stage: snap.stage,
        conditionSet: snap.conditionSet,
        fuzzyData: snap.fuzzyData,
        prototypeFuzzyData: snap.prototypeFuzzyData,
        analysisResult: snap.analysisResult,
        prototypeAnalysisResult: snap.prototypeAnalysisResult,
        analysisResultB: snap.analysisResultB,
        robustnessReport: snap.robustnessReport,
        counterfactualReport: snap.counterfactualReport,
        multiOutcomeReport: snap.multiOutcomeReport,
      };
    }

    case 'TICK_ELAPSED':
      if (state.startTime === null) return state;
      return { ...state, elapsedMs: Date.now() - state.startTime };

    default:
      return state;
  }
}

// ─── Context Shape ─────────────────────────────────────────────────────────

interface QCAPipelineContextValue {
  state: QCAPipelineState;
  dispatch: Dispatch<PipelineAction>;

  // High-level workflow mutations
  reset: () => void;
  startCalibration: () => void;
  finishCalibration: (fuzzyData: MembershipDataJSON, prototypeFuzzyData?: MembershipDataJSON) => void;
  startAnalysis: () => void;
  finishAnalysis: (result: QCAAnalysisResultJSON, captureAsLabel?: 'a' | 'b') => void;
  startPrototypeAnalysis: () => void;
  finishPrototypeAnalysis: (result: QCAAnalysisResultJSON) => void;
  startRobustness: () => void;
  finishRobustness: (report: RobustnessReport) => void;
  startCounterfactuals: () => void;
  finishCounterfactuals: (report: CounterfactualReport) => void;
  startSecondOutcomeAnalysis: () => void;
  finishSecondOutcomeAnalysis: (result: QCAAnalysisResultJSON) => void;
  startMultiOutcomeComparison: () => void;
  finishMultiOutcomeComparison: (report: MultiOutcomeReport) => void;
  finishExport: (formats: string[]) => void;
  fail: (error: string) => void;
  setProgress: (progress: number, message?: string) => void;
  setConditionSet: (cs: ConditionSet) => void;
  startBertLoading: () => void;
  finishBertLoading: () => void;
  setBertStatus: (status: 'unloaded' | 'loading' | 'ready' | 'error', message?: string) => void;
  startEmbedding: () => void;
  finishEmbedding: () => void;
  setPerformanceMetrics: (metrics: PerformanceMetrics) => void;
  // Text corpus mutations
  setTextCorpus: (entries: TextCorpusEntry[]) => void;
  setTextCases: (cases: TextCase[]) => void;
  setYamlContent: (content: string) => void;
  setProtoConditions: (rows: QCAProjectProtoConditionRow[]) => void;
  // Project save/restore
  hydrateFromProject: (projectSnapshot: {
    stage: PipelineStage;
    conditionSet: ConditionSet | null;
    fuzzyData: MembershipDataJSON | null;
    prototypeFuzzyData: MembershipDataJSON | null;
    analysisResult: QCAAnalysisResultJSON | null;
    prototypeAnalysisResult: QCAAnalysisResultJSON | null;
    analysisResultB: QCAAnalysisResultJSON | null;
    robustnessReport: RobustnessReport | null;
    counterfactualReport: CounterfactualReport | null;
    multiOutcomeReport: MultiOutcomeReport | null;
  }, settings: Record<string, unknown>, params: unknown, bertModel: string | undefined, recentRuns: SavedAnalysisRun[], textCorpusData: { texts: TextCorpusEntry[]; textCases: TextCase[]; yamlContent: string; protoConditions: QCAProjectProtoConditionRow[] }) => void;
}

const QCAPipelineContext = createContext<QCAPipelineContextValue | null>(null);

// ─── Provider ──────────────────────────────────────────────────────────────

export function QCAPipelineProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(pipelineReducer, INITIAL_PIPELINE_STATE);
  const startTimeRef = useRef<number | null>(null);

  // Heartbeat timer for elapsedMs
  useEffect(() => {
    if (state.stage === 'idle' || state.stage === 'done' || state.stage === 'error') {
      return;
    }
    const interval = setInterval(() => {
      dispatch({ type: 'TICK_ELAPSED' });
    }, 100);
    return () => clearInterval(interval);
  }, [state.stage]);

  const reset = useCallback(() => {
    startTimeRef.current = null;
    dispatch({ type: 'RESET' });
  }, []);

  const startCalibration = useCallback(() => {
    startTimeRef.current = Date.now();
    dispatch({ type: 'SET_STAGE', stage: 'calibrating', message: 'Calibrating conditions...' });
  }, []);

  const finishCalibration = useCallback(
    (fuzzyData: MembershipDataJSON, prototypeFuzzyData?: MembershipDataJSON) => {
      dispatch({ type: 'SET_FUZZY_DATA', fuzzyData, prototypeFuzzyData });
      dispatch({ type: 'SET_STAGE', stage: 'calibrated', message: 'Calibration complete' });
    },
    []
  );

  const startAnalysis = useCallback(() => {
    dispatch({ type: 'SET_STAGE', stage: 'analyzing', message: 'Running QCA analysis...' });
  }, []);

  const finishAnalysis = useCallback((result: QCAAnalysisResultJSON, captureAsLabel?: 'a' | 'b') => {
    dispatch({ type: 'SET_ANALYSIS_RESULT', result });
    dispatch({
      type: 'SET_STAGE',
      stage: 'analyzed',
      message: 'QCA analysis complete',
    });
    // Persist to recent runs
    _runIdCounter += 1;
    const run: SavedAnalysisRun = {
      id: `run-${Date.now()}-${_runIdCounter}`,
      name: result.metadata?.run_name as string || `Analysis ${_runIdCounter}`,
      timestamp: new Date().toISOString(),
      status: 'success',
      duration: Date.now() - (startTimeRef.current ?? Date.now()),
      conditionCount: result.condition_set?.conditions?.length ?? 0,
      caseCount: result.fuzzy_data?.membership?.length ?? 0,
      solutions: result.solutions,
    };
    persistRecentRun(run);

    // Capture snapshot if requested (P1-7)
    if (captureAsLabel && result.condition_set) {
      let params = { ...DEFAULT_QCA_PARAMS };
      try {
        const raw = localStorage.getItem('qca-params');
        if (raw) params = JSON.parse(raw);
      } catch {
        // use defaults
      }
      const snapshot: ParameterSnapshot = {
        id: `snap-${Date.now()}`,
        name: result.metadata?.run_name as string || `Run ${_runIdCounter}`,
        timestamp: new Date().toISOString(),
        conditionSet: result.condition_set,
        analysisParams: params,
        result,
      };
      saveSnapshot(captureAsLabel, snapshot);
    }
  }, []);

  const startPrototypeAnalysis = useCallback(() => {
    dispatch({ type: 'SET_STAGE', stage: 'prototype-analyzing', message: 'Running prototype QCA analysis...' });
  }, []);

  const finishPrototypeAnalysis = useCallback((result: QCAAnalysisResultJSON) => {
    dispatch({ type: 'SET_PROTOTYPE_ANALYSIS_RESULT', result });
    dispatch({
      type: 'SET_STAGE',
      stage: 'prototype-analyzed',
      message: 'Prototype QCA analysis complete',
    });
    // Persist to recent runs
    _runIdCounter += 1;
    const run: SavedAnalysisRun = {
      id: `run-${Date.now()}-${_runIdCounter}`,
      name: result.metadata?.run_name as string || `Prototype Analysis ${_runIdCounter}`,
      timestamp: new Date().toISOString(),
      status: 'success',
      duration: Date.now() - (startTimeRef.current ?? Date.now()),
      conditionCount: result.condition_set?.conditions?.length ?? 0,
      caseCount: result.fuzzy_data?.membership?.length ?? 0,
      solutions: result.solutions,
    };
    persistRecentRun(run);
  }, []);

  const startRobustness = useCallback(() => {
    dispatch({
      type: 'SET_STAGE',
      stage: 'running-robustness',
      message: 'Running robustness tests...',
    });
  }, []);

  const finishRobustness = useCallback((report: RobustnessReport) => {
    dispatch({ type: 'SET_ROBUSTNESS_REPORT', report });
    dispatch({
      type: 'SET_STAGE',
      stage: 'robustness-done',
      message: 'Robustness tests complete',
    });
  }, []);

  const startCounterfactuals = useCallback(() => {
    dispatch({
      type: 'SET_STAGE',
      stage: 'running-counterfactuals',
      message: 'Running counterfactual analysis...',
    });
  }, []);

  const finishCounterfactuals = useCallback((report: CounterfactualReport) => {
    dispatch({ type: 'SET_COUNTERFACTUAL_REPORT', report });
    dispatch({
      type: 'SET_STAGE',
      stage: 'counterfactuals-done',
      message: 'Counterfactual analysis complete',
    });
  }, []);

  const startSecondOutcomeAnalysis = useCallback(() => {
    dispatch({ type: 'SET_STAGE', stage: 'analyzing', message: 'Running QCA analysis for Outcome B...' });
  }, []);

  const finishSecondOutcomeAnalysis = useCallback((result: QCAAnalysisResultJSON) => {
    dispatch({ type: 'SET_ANALYSIS_RESULT_B', result });
    dispatch({
      type: 'SET_STAGE',
      stage: 'analyzed',
      message: 'Outcome B QCA analysis complete',
    });
  }, []);

  const startMultiOutcomeComparison = useCallback(() => {
    dispatch({
      type: 'SET_STAGE',
      stage: 'multi-outcome-comparing',
      message: 'Comparing outcomes...',
    });
  }, []);

  const finishMultiOutcomeComparison = useCallback((report: MultiOutcomeReport) => {
    dispatch({ type: 'SET_MULTI_OUTCOME_REPORT', report });
    dispatch({
      type: 'SET_STAGE',
      stage: 'multi-outcome-done',
      message: 'Multi-outcome comparison complete',
    });
  }, []);

  const finishExport = useCallback((formats: string[]) => {
    dispatch({ type: 'SET_EXPORT_FORMATS', formats });
    dispatch({ type: 'SET_STAGE', stage: 'done', message: 'Analysis complete' });
  }, []);

  const fail = useCallback((error: string) => {
    dispatch({ type: 'SET_ERROR', error });
  }, []);

  const setProgress = useCallback((progress: number, message?: string) => {
    dispatch({ type: 'SET_PROGRESS', progress, message });
  }, []);

  const setConditionSet = useCallback((cs: ConditionSet) => {
    dispatch({ type: 'SET_CONDITION_SET', conditionSet: cs });
  }, []);

  const startBertLoading = useCallback(() => {
    dispatch({ type: 'SET_STAGE', stage: 'bert-loading', message: 'Loading BERT model...' });
    dispatch({ type: 'SET_BERT_STATUS', status: 'loading', message: 'BERT model downloading...' });
  }, []);

  const finishBertLoading = useCallback(() => {
    dispatch({ type: 'SET_BERT_STATUS', status: 'ready', message: 'BERT model ready' });
    dispatch({ type: 'SET_STAGE', stage: 'pyodide-ready', message: 'BERT model loaded' });
  }, []);

  const setBertStatusAction = useCallback(
    (status: 'unloaded' | 'loading' | 'ready' | 'error', message?: string) => {
      dispatch({ type: 'SET_BERT_STATUS', status, message });
    },
    []
  );

  const startEmbedding = useCallback(() => {
    dispatch({ type: 'SET_STAGE', stage: 'embedding', message: 'Computing BERT embeddings...' });
  }, []);

  const finishEmbedding = useCallback(() => {
    dispatch({ type: 'SET_EMBEDDINGS_READY', embeddings: [] });
    dispatch({ type: 'SET_STAGE', stage: 'calibrating-embed', message: 'Running embedding-based calibration...' });
  }, []);

  // Text corpus mutations
  const setTextCorpus = useCallback((entries: TextCorpusEntry[]) => {
    dispatch({ type: 'SET_TEXT_CORPUS', entries });
  }, []);

  const setTextCases = useCallback((cases: TextCase[]) => {
    dispatch({ type: 'SET_TEXT_CASES', cases });
  }, []);

  const setYamlContent = useCallback((content: string) => {
    dispatch({ type: 'SET_YAML_CONTENT', content });
  }, []);

  const setProtoConditions = useCallback((rows: QCAProjectProtoConditionRow[]) => {
    dispatch({ type: 'SET_PROTO_CONDITIONS', rows });
  }, []);

  // Project save/restore
  const hydrateFromProject = useCallback((
    projectSnapshot: {
      stage: PipelineStage;
      conditionSet: ConditionSet | null;
      fuzzyData: MembershipDataJSON | null;
      prototypeFuzzyData: MembershipDataJSON | null;
      analysisResult: QCAAnalysisResultJSON | null;
      prototypeAnalysisResult: QCAAnalysisResultJSON | null;
      analysisResultB: QCAAnalysisResultJSON | null;
      robustnessReport: RobustnessReport | null;
      counterfactualReport: CounterfactualReport | null;
      multiOutcomeReport: MultiOutcomeReport | null;
    },
    settings: Record<string, unknown>,
    params: unknown,
    bertModel: string | undefined,
    recentRuns: SavedAnalysisRun[],
    textCorpusData: { texts: TextCorpusEntry[]; textCases: TextCase[]; yamlContent: string; protoConditions: QCAProjectProtoConditionRow[] }
  ) => {
    // 1. Restore settings to localStorage
    try { localStorage.setItem('qca-settings', JSON.stringify(settings)); } catch {}
    try { localStorage.setItem('qca-params', JSON.stringify(params)); } catch {}
    if (bertModel) {
      try { localStorage.setItem('qca-bert-model', JSON.stringify(bertModel)); } catch {}
    }

    // 2. Restore recentRuns
    try { localStorage.setItem(RECENT_RUNS_KEY, JSON.stringify(recentRuns)); } catch {}
    window.dispatchEvent(new Event(RECENT_RUNS_EVENT));

    // 3. Dispatch HYDRATE_FROM_PROJECT
    dispatch({ type: 'HYDRATE_FROM_PROJECT', snapshot: projectSnapshot });

    // 4. Save textCorpus to localStorage
    try {
      localStorage.setItem('qca-project-textcorpus', JSON.stringify(textCorpusData));
      dispatch({ type: 'SET_TEXT_CORPUS', entries: textCorpusData.texts });
      dispatch({ type: 'SET_TEXT_CASES', cases: textCorpusData.textCases });
      dispatch({ type: 'SET_YAML_CONTENT', content: textCorpusData.yamlContent });
      dispatch({ type: 'SET_PROTO_CONDITIONS', rows: textCorpusData.protoConditions });
    } catch {}
  }, []);

  const value: QCAPipelineContextValue = {
    state,
    dispatch,
    reset,
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
    setProgress,
    setConditionSet,
    startBertLoading,
    finishBertLoading,
    setBertStatus: setBertStatusAction,
    startEmbedding,
    finishEmbedding,
    setPerformanceMetrics: (metrics: PerformanceMetrics) => dispatch({ type: 'SET_PERFORMANCE_METRICS', metrics }),
    setTextCorpus,
    setTextCases,
    setYamlContent,
    setProtoConditions,
    hydrateFromProject,
  };

  return (
    <QCAPipelineContext.Provider value={value}>
      {children}
    </QCAPipelineContext.Provider>
  );
}

// ─── Hook ──────────────────────────────────────────────────────────────────

export function useQCAPipeline(): QCAPipelineContextValue {
  const ctx = useContext(QCAPipelineContext);
  if (!ctx) {
    throw new Error('useQCAPipeline must be used within a QCAPipelineProvider');
  }
  return ctx;
}
