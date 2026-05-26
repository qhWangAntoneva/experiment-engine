/**
 * QCA-specific TypeScript interfaces mirroring experiment_engine/models.py.
 * All models are JSON-serializable (no numpy arrays — those stay in Pyodide
 * and are serialized via `.tolist()` before crossing the bridge).
 */

// ─── Enums ────────────────────────────────────────────────────────────────

export type TextDomain =
  | 'dissatisfaction'
  | 'policy_demand'
  | 'co_production'
  | 'trust'
  | 'gov_responsiveness';

export enum CalibrationMethod {
  DIRECT = "direct",
  INDIRECT = "indirect",
  FUZZY_DIRECT = "fuzzy_direct",
  PASSTHROUGH = "passthrough",
  CRISP_SET = "crisp_set",
}

/** Backward-compatibility alias */
export type CalibrationType = CalibrationMethod;

export enum QCAVariant {
  FSQCA = "fsqca",
  CSQCA = "csqca",
}

export type ScoringSource = 'prototype';

export type PipelineStage =
  | 'idle'
  | 'loading-pyodide'
  | 'pyodide-ready'
  | 'loading-texts'
  | 'calibrating'
  | 'calibrated'
  | 'bert-loading'
  | 'embedding'
  | 'calibrating-embed'
  | 'embed-calibrated'
  | 'analyzing'
  | 'analyzed'
  | 'prototype-analyzing'
  | 'prototype-analyzed'
  | 'running-robustness'
  | 'robustness-done'
  | 'running-counterfactuals'
  | 'counterfactuals-done'
  | 'exporting'
  | 'done'
  | 'error';

// ─── Calibration ───────────────────────────────────────────────────────────

export interface CalibrationParams {
  threshold_full_in: number;   // >= crossover
  threshold_full_out: number;  // <= crossover
  crossover_point: number;     // where membership = 0.5
  direction: 'ascending' | 'descending';
  steepness?: number;          // steepness factor for indirect calibration (default 10.0)
}

export interface ConceptPrototype {
  prototype_text: string;
  is_member: 0 | 1;
  weight: number;
}

export interface ConditionDefinition {
  name: string;
  display_name: string;
  domain: TextDomain;
  calibration_type: CalibrationMethod;
  calibration_params: CalibrationParams | null;
  description: string;
  scoring_source: ScoringSource;
  prototypes: ConceptPrototype[];
  prototype_embeddings: number[][] | null;
  embedding_model: string | null;
}

export interface ConditionSet {
  name: string;
  description: string;
  conditions: ConditionDefinition[];
  outcome: ConditionDefinition | null;
  domain: TextDomain;
  scoring_source: ScoringSource;
  qca_variant?: QCAVariant;
}

export interface TextCase {
  text_id: string;
  text: string;
  outcome: 0 | 1;
}

// ─── Membership Data (serialized from numpy → list[list[number]]) ───────────

export interface MembershipDataJSON {
  membership: number[][];       // shape (n_cases, n_conditions + 1), last col = outcome
  case_ids: string[];
  condition_names: string[];
  outcome_name: string;
  texts: string[] | null;
  metadata: Record<string, unknown>;
}

/** Backward-compatibility alias */
export type FuzzySetDataJSON = MembershipDataJSON;

// ─── Truth Table ───────────────────────────────────────────────────────────

export interface TruthTableRow {
  config: number[];
  config_label: string;
  frequency: number;
  raw_consistency: number;
  outcome_value: 0 | 1;
  included: boolean;
}

export interface TruthTableJSON {
  rows: TruthTableRow[];
  condition_names: string[];
  outcome_name: string;
  consistency_threshold: number;
  frequency_threshold: number;
  n_cases: number;
}

// ─── QCA Solutions ─────────────────────────────────────────────────────────

export interface SolutionTerm {
  term: string[];               // e.g. ['A', '~B', 'C']
  label: string;                // e.g. 'A*~B*C'
  consistency: number;
  raw_coverage: number;
  unique_coverage: number;
}

export interface QCASolution {
  solution_type: 'complex' | 'parsimonious' | 'intermediate';
  terms: SolutionTerm[];
  formula: string;
  solution_consistency: number;
  solution_coverage: number;
}

export interface QCASolutions {
  complex: QCASolution | null;
  parsimonious: QCASolution | null;
  intermediate: QCASolution | null;
}

// ─── Necessity / Sufficiency ───────────────────────────────────────────────

export interface NecessityConditionResult {
  condition_name: string;
  consistency: number;
  coverage: number;
  is_necessary: boolean;
}

export interface NecessityResults {
  outcome_name: string;
  threshold: number;
  conditions: NecessityConditionResult[];
}

export interface SufficiencyResults {
  outcome_name: string;
  solutions: QCASolutions;
}

// ─── Comprehensive QCA Result ──────────────────────────────────────────────

export interface QCAAnalysisResultJSON {
  fuzzy_data: MembershipDataJSON | null;
  truth_table: TruthTableJSON | null;
  solutions: QCASolutions;
  necessity: NecessityResults | null;
  sufficiency: SufficiencyResults | null;
  condition_set: ConditionSet | null;
  metadata: Record<string, unknown>;
}

// ─── Robustness ────────────────────────────────────────────────────────────

export interface RobustnessTestResult {
  test_name: string;
  parameter_varied: string;
  parameter_values: number[];
  solution_stability: number[];
  coverage_stability: number[];
  passed: boolean;
}

export interface RobustnessReport {
  tests: RobustnessTestResult[];
  overall_robustness: number;
  summary: string;
}

// ─── Counterfactuals ───────────────────────────────────────────────────────

export interface CounterfactualClassification {
  config: number[];
  is_observed: boolean;
  counterfactual_type: string | null;
  theoretical_expectation: string | null;
}

export interface CounterfactualReport {
  classifications: CounterfactualClassification[];
  n_easy_counterfactuals: number;
  n_hard_counterfactuals: number;
  n_logical_remainders: number;
}

// ─── Text Corpus Input ─────────────────────────────────────────────────────

export interface TextCorpusEntry {
  text_id: string;
  text: string;
  metadata?: Record<string, unknown>;
}

export type CorpusSource =
  | { type: 'paste'; content: string; format: 'csv' | 'json' | 'txt' }
  | { type: 'upload'; fileName: string; content: ArrayBuffer; format: 'csv' | 'json' | 'txt' };

// ─── QCA Analysis Parameters ───────────────────────────────────────────────

export interface QCAAnalysisParams {
  consistency_threshold: number;   // default 0.75
  frequency_threshold: number;     // default 1.0
  necessity_threshold: number;     // default 0.9
  n_cut: number;                   // frequency cutoff for truth table, default 1
}

export const DEFAULT_QCA_PARAMS: QCAAnalysisParams = {
  consistency_threshold: 0.75,
  frequency_threshold: 1.0,
  necessity_threshold: 0.9,
  n_cut: 1,
};

// ─── Pipeline State ────────────────────────────────────────────────────────

export interface QCAPipelineState {
  stage: PipelineStage;
  progress: number;               // 0-100
  message: string;
  error: string | null;
  startTime: number | null;       // Date.now()
  elapsedMs: number;              // updated via interval

  // Pipeline artifacts (populated as stages complete)
  conditionSet: ConditionSet | null;
  fuzzyData: MembershipDataJSON | null;
  /** Prototype-based calibration result (populated when prototype texts are provided) */
  prototypeFuzzyData: MembershipDataJSON | null;
  analysisResult: QCAAnalysisResultJSON | null;
  /** Prototype-based QCA analysis result (populated when prototype texts are analyzed) */
  prototypeAnalysisResult: QCAAnalysisResultJSON | null;
  robustnessReport: RobustnessReport | null;
  counterfactualReport: CounterfactualReport | null;
  exportFormats: string[];        // e.g. ['csv', 'json', 'latex']

  // BERT state
  bertStatus: 'unloaded' | 'loading' | 'ready' | 'error';
  bertMessage: string;
  bertEmbeddingsReady: boolean;
}

export const INITIAL_PIPELINE_STATE: QCAPipelineState = {
  stage: 'idle',
  progress: 0,
  message: 'Ready',
  error: null,
  startTime: null,
  elapsedMs: 0,
  conditionSet: null,
  fuzzyData: null,
  prototypeFuzzyData: null,
  analysisResult: null,
  prototypeAnalysisResult: null,
  robustnessReport: null,
  counterfactualReport: null,
  exportFormats: [],
  bertStatus: 'unloaded',
  bertMessage: '',
  bertEmbeddingsReady: false,
};

// ─── BERT Embedding Calibration Input ──────────────────────────────────────

/** Text entry with pre-computed BERT embedding for embed_calibrate. */
export interface EmbedCalibrateTextEntry {
  text_id: string;
  text: string;
  embedding: number[];           // 768-dim float array from BertEngine
}

// ─── Pyodide Worker Messages ───────────────────────────────────────────────

export type PyodideWorkerRequest =
  | { type: 'init'; payload: { packages: string[] } }
  | { type: 'calibrate'; payload: { texts: TextCorpusEntry[]; conditionSet: ConditionSet; prototypeTexts?: TextCase[] } }
  | { type: 'load_corpus'; payload: { fileName: string; content: string; format: 'csv' | 'json' | 'txt' | 'xlsx' } }
  | { type: 'analyze'; payload: { fuzzyData: MembershipDataJSON; params: QCAAnalysisParams } }
  | { type: 'run_robustness'; payload: { fuzzyData: MembershipDataJSON; analysisResult: QCAAnalysisResultJSON } }
  | { type: 'run_counterfactuals'; payload: { fuzzyData: MembershipDataJSON; analysisResult: QCAAnalysisResultJSON } }
  | { type: 'export_result'; payload: { format: 'csv' | 'json' | 'latex'; result: QCAAnalysisResultJSON } }
  | { type: 'validate_condition_set'; payload: { conditionSet: ConditionSet } }
  | { type: 'init_bert'; payload: { modelName: string } }
  | { type: 'embed_calibrate'; payload: { texts: EmbedCalibrateTextEntry[]; conditionSet: any } }
  | { type: 'compute_embeddings'; payload: { texts: string[]; batchSize?: number } }
  | { type: 'compute_prototype_embeddings'; payload: { prototypes: Record<string, string[]> } }
  | { type: 'get_bert_status' }
  | { type: 'get_package_status'; payload?: never }
  | { type: 'terminate'; payload?: never };

export type PyodideWorkerResponse =
  | { type: 'init-progress'; message: string; progress: number }
  | { type: 'init-done'; loadedPackages: string[] }
  | { type: 'init-error'; error: string }
  | { type: 'calibrate-done'; fuzzyData: MembershipDataJSON; prototypeFuzzyData?: MembershipDataJSON }
  | { type: 'calibrate-error'; error: string }
  | { type: 'corpus-loaded'; entries: TextCorpusEntry[] }
  | { type: 'corpus-error'; error: string }
  | { type: 'analyze-done'; result: QCAAnalysisResultJSON }
  | { type: 'analyze-error'; error: string }
  | { type: 'robustness-done'; report: RobustnessReport }
  | { type: 'robustness-error'; error: string }
  | { type: 'counterfactuals-done'; report: CounterfactualReport }
  | { type: 'counterfactuals-error'; error: string }
  | { type: 'export-done'; data: string; mimeType: string }
  | { type: 'export-error'; error: string }
  | { type: 'validate-done'; valid: boolean; warnings: string[] }
  | { type: 'validate-error'; error: string }
  | { type: 'bert-init-progress'; progress: number; message: string }
  | { type: 'bert-init-done'; modelName: string }
  | { type: 'bert-init-error'; error: string }
  | { type: 'embeddings-computed'; embeddings: number[][] }
  | { type: 'embeddings-error'; error: string }
  | { type: 'prototype-embeddings-computed'; embeddings: Record<string, {embeddings: number[][]; labels: number[]; weights: number[]}> }
  | { type: 'embed-calibrate-done'; fuzzyData: MembershipDataJSON }
  | { type: 'embed-calibrate-error'; error: string }
  | { type: 'bert-status'; loaded: boolean; modelName: string | null }
  | { type: 'package-status'; packages: Record<string, string> }
  | { type: 'log'; message: string; level: 'debug' | 'info' | 'warn' | 'error' }
  | { type: 'terminated' };

// ─── Export Result ─────────────────────────────────────────────────────────

export interface ExportResult {
  data: Blob;
  mimeType: string;
  filename: string;
}

// ─── Saved Analysis Run (for recent-runs table) ────────────────────────────

export interface SavedAnalysisRun {
  id: string;
  name: string;
  timestamp: string;
  status: 'success' | 'failed' | 'running';
  duration: number;
  conditionCount: number;
  caseCount: number;
  solutions: QCASolutions | null;
}
