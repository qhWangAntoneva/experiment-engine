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
  FuzzySetDataJSON,
  QCAAnalysisResultJSON,
  RobustnessReport,
  CounterfactualReport,
  ConditionSet,
} from '../types/qca';
import { INITIAL_PIPELINE_STATE } from '../types/qca';

// ─── Actions ───────────────────────────────────────────────────────────────

export type PipelineAction =
  | { type: 'RESET' }
  | { type: 'SET_STAGE'; stage: PipelineStage; message?: string }
  | { type: 'SET_PROGRESS'; progress: number; message?: string }
  | { type: 'SET_ERROR'; error: string }
  | { type: 'SET_CONDITION_SET'; conditionSet: ConditionSet }
  | { type: 'SET_FUZZY_DATA'; fuzzyData: FuzzySetDataJSON }
  | { type: 'SET_ANALYSIS_RESULT'; result: QCAAnalysisResultJSON }
  | { type: 'SET_ROBUSTNESS_REPORT'; report: RobustnessReport }
  | { type: 'SET_COUNTERFACTUAL_REPORT'; report: CounterfactualReport }
  | { type: 'SET_EXPORT_FORMATS'; formats: string[] }
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
      return { ...state, fuzzyData: action.fuzzyData };

    case 'SET_ANALYSIS_RESULT':
      return { ...state, analysisResult: action.result };

    case 'SET_ROBUSTNESS_REPORT':
      return { ...state, robustnessReport: action.report };

    case 'SET_COUNTERFACTUAL_REPORT':
      return { ...state, counterfactualReport: action.report };

    case 'SET_EXPORT_FORMATS':
      return { ...state, exportFormats: action.formats };

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
  finishCalibration: (fuzzyData: FuzzySetDataJSON) => void;
  startAnalysis: () => void;
  finishAnalysis: (result: QCAAnalysisResultJSON) => void;
  startRobustness: () => void;
  finishRobustness: (report: RobustnessReport) => void;
  startCounterfactuals: () => void;
  finishCounterfactuals: (report: CounterfactualReport) => void;
  finishExport: (formats: string[]) => void;
  fail: (error: string) => void;
  setProgress: (progress: number, message?: string) => void;
  setConditionSet: (cs: ConditionSet) => void;
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

  const finishCalibration = useCallback((fuzzyData: FuzzySetDataJSON) => {
    dispatch({ type: 'SET_FUZZY_DATA', fuzzyData });
    dispatch({ type: 'SET_STAGE', stage: 'calibrated', message: 'Calibration complete' });
  }, []);

  const startAnalysis = useCallback(() => {
    dispatch({ type: 'SET_STAGE', stage: 'analyzing', message: 'Running QCA analysis...' });
  }, []);

  const finishAnalysis = useCallback((result: QCAAnalysisResultJSON) => {
    dispatch({ type: 'SET_ANALYSIS_RESULT', result });
    dispatch({
      type: 'SET_STAGE',
      stage: 'analyzed',
      message: 'QCA analysis complete',
    });
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
      stage: 'running-robustness',
      message: 'Running counterfactual analysis...',
    });
  }, []);

  const finishCounterfactuals = useCallback((report: CounterfactualReport) => {
    dispatch({ type: 'SET_COUNTERFACTUAL_REPORT', report });
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
    dispatch({ type: 'SET_CONDITION_SET', cs });
  }, []);

  const value: QCAPipelineContextValue = {
    state,
    dispatch,
    reset,
    startCalibration,
    finishCalibration,
    startAnalysis,
    finishAnalysis,
    startRobustness,
    finishRobustness,
    startCounterfactuals,
    finishCounterfactuals,
    finishExport,
    fail,
    setProgress,
    setConditionSet,
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
