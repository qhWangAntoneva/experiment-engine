/**
 * Project Serialization (P1-6)
 *
 * Handles serialize, validate, download, and restore of QCAProjectFile.
 * All data is stored as a .qca JSON file for portability.
 */

import type {
  QCAProjectFile,
  QCAProjectPipelineSnapshot,
  QCAProjectTextCorpusSnapshot,
  QCAProjectProtoConditionRow,
  ConditionSet,
  ConditionDefinition,
  MembershipDataJSON,
  QCAAnalysisResultJSON,
  RobustnessReport,
  CounterfactualReport,
  MultiOutcomeReport,
  TextCorpusEntry,
  TextCase,
  QCAAnalysisParams,
  SavedAnalysisRun,
  PipelineStage,
} from '../types/qca';
import { DEFAULT_QCA_PARAMS } from '../types/qca';

// ─── Constants ────────────────────────────────────────────────────────────────

const PROJECT_VERSION = '1.0.0';
const APP_VERSION = '0.2.0';

const AUTOSAVE_KEY = 'qca-project-autosave';
const TEXTCORPUS_KEY = 'qca-project-textcorpus';

/** Transitional stages that should be mapped to their stable equivalents on restore. */
const STAGE_SANITIZE_MAP: Record<string, PipelineStage> = {
  calibrating: 'calibrated',
  'calibrating-embed': 'embed-calibrated',
  'bert-loading': 'pyodide-ready',
  embedding: 'embed-calibrated',
  analyzing: 'analyzed',
  'prototype-analyzing': 'prototype-analyzed',
  'running-robustness': 'robustness-done',
  'running-counterfactuals': 'counterfactuals-done',
  exporting: 'done',
  'loading-pyodide': 'pyodide-ready',
  'loading-texts': 'idle',
};

// ─── Serialize ─────────────────────────────────────────────────────────────────

export interface SerializeOpts {
  pipelineState: {
    stage: PipelineStage;
    conditionSet: ConditionSet | null;
    fuzzyData: MembershipDataJSON | null;
    prototypeFuzzyData: MembershipDataJSON | null;
    analysisResult: QCAAnalysisResultJSON | null;
    prototypeAnalysisResult: QCAAnalysisResultJSON | null;
    robustnessReport: RobustnessReport | null;
    counterfactualReport: CounterfactualReport | null;
    analysisResultB: QCAAnalysisResultJSON | null;
    multiOutcomeReport: MultiOutcomeReport | null;
  };
  recentRuns: SavedAnalysisRun[];
  textCorpusData: {
    texts: TextCorpusEntry[];
    textCases: TextCase[];
    yamlContent: string;
    protoConditions: QCAProjectProtoConditionRow[];
  };
}

/**
 * Strip prototype_embeddings from a ConditionSet to reduce project file size.
 * Embeddings are large (~3KB per prototype) and can be recomputed on restore.
 */
function stripPrototypeEmbeddings(cs: ConditionSet | null): ConditionSet | null {
  if (!cs) return null;

  const stripCondition = (cond: ConditionDefinition): ConditionDefinition => ({
    ...cond,
    prototype_embeddings: null,
    embedding_model: null,
  });

  return {
    ...cs,
    conditions: cs.conditions.map(stripCondition),
    outcome: cs.outcome ? stripCondition(cs.outcome) : null,
  };
}

/** Build a QCAProjectFile from current pipeline state, settings, and text corpus. */
export function serializeProject(opts: SerializeOpts): QCAProjectFile {
  let settings: Record<string, unknown> = {};
  try {
    const raw = localStorage.getItem('qca-settings');
    if (raw) settings = JSON.parse(raw);
  } catch {
    // ignore parse errors
  }

  let params: QCAAnalysisParams = DEFAULT_QCA_PARAMS;
  try {
    const raw = localStorage.getItem('qca-params');
    if (raw) params = JSON.parse(raw);
  } catch {
    // use defaults
  }

  let bertModel: string | undefined;
  try {
    const raw = localStorage.getItem('qca-bert-model');
    if (raw) bertModel = JSON.parse(raw);
  } catch {
    // undefined is fine
  }

  const pipeline: QCAProjectPipelineSnapshot = {
    stage: opts.pipelineState.stage,
    conditionSet: stripPrototypeEmbeddings(opts.pipelineState.conditionSet),
    fuzzyData: opts.pipelineState.fuzzyData,
    prototypeFuzzyData: opts.pipelineState.prototypeFuzzyData,
    analysisResult: opts.pipelineState.analysisResult,
    prototypeAnalysisResult: opts.pipelineState.prototypeAnalysisResult,
    analysisResultB: opts.pipelineState.analysisResultB ?? null,
    robustnessReport: opts.pipelineState.robustnessReport,
    counterfactualReport: opts.pipelineState.counterfactualReport,
    multiOutcomeReport: opts.pipelineState.multiOutcomeReport ?? null,
  };

  const textCorpus: QCAProjectTextCorpusSnapshot = {
    texts: opts.textCorpusData.texts,
    textCases: opts.textCorpusData.textCases,
    yamlContent: opts.textCorpusData.yamlContent,
    protoConditions: opts.textCorpusData.protoConditions,
  };

  return {
    version: PROJECT_VERSION,
    appVersion: APP_VERSION,
    savedAt: new Date().toISOString(),
    pipeline,
    settings,
    params,
    bertModel,
    textCorpus,
    recentRuns: opts.recentRuns,
  };
}

// ─── Validate ──────────────────────────────────────────────────────────────────

export interface ValidationResult {
  valid: boolean;
  project?: QCAProjectFile;
  errors: string[];
}

export function validateProjectFile(data: unknown): ValidationResult {
  const errors: string[] = [];

  if (!data || typeof data !== 'object') {
    return { valid: false, errors: ['Data is not an object'] };
  }

  const obj = data as Record<string, unknown>;

  // Check top-level keys
  if (!obj.version || typeof obj.version !== 'string') {
    errors.push('Missing or invalid "version" field');
  }
  if (!obj.savedAt || typeof obj.savedAt !== 'string') {
    errors.push('Missing or invalid "savedAt" field');
  }
  if (!obj.pipeline || typeof obj.pipeline !== 'object') {
    errors.push('Missing or invalid "pipeline" field');
  }
  if (!obj.settings || typeof obj.settings !== 'object') {
    errors.push('Missing or invalid "settings" field');
  }
  if (!obj.params || typeof obj.params !== 'object') {
    errors.push('Missing or invalid "params" field');
  }
  if (!obj.textCorpus || typeof obj.textCorpus !== 'object') {
    errors.push('Missing or invalid "textCorpus" field');
  }
  if (!Array.isArray(obj.recentRuns)) {
    errors.push('Missing or invalid "recentRuns" field (expected array)');
  }

  // Check pipeline sub-fields
  if (obj.pipeline && typeof obj.pipeline === 'object') {
    const pipeline = obj.pipeline as Record<string, unknown>;
    if (!pipeline.hasOwnProperty('stage')) {
      errors.push('pipeline.stage is missing');
    }
    if (!pipeline.hasOwnProperty('conditionSet')) {
      errors.push('pipeline.conditionSet is missing');
    }
  }

  // Check conditionSet has conditions array
  if (
    obj.pipeline &&
    typeof obj.pipeline === 'object' &&
    (obj.pipeline as Record<string, unknown>).conditionSet &&
    typeof (obj.pipeline as Record<string, unknown>).conditionSet === 'object'
  ) {
    const cs = (obj.pipeline as Record<string, unknown>).conditionSet as Record<string, unknown>;
    if (!cs.conditions || !Array.isArray(cs.conditions)) {
      errors.push('pipeline.conditionSet.conditions is missing or not an array');
    }
  }

  if (errors.length > 0) {
    return { valid: false, errors };
  }

  return { valid: true, project: obj as unknown as QCAProjectFile, errors: [] };
}

// ─── Download ──────────────────────────────────────────────────────────────────

/** Create a Blob and trigger browser download. Filename: qca-project-YYYY-MM-DD-HHmmss.qca */
export function downloadProjectFile(projectData: QCAProjectFile): void {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
  const filename = `qca-project-${ts}.qca`;

  const json = JSON.stringify(projectData, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ─── Read / Restore ────────────────────────────────────────────────────────────

/** Read a .qca file from disk, parse JSON, validate, and return the project. */
export function readProjectFile(file: File): Promise<QCAProjectFile> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const data = JSON.parse(content);
        const result = validateProjectFile(data);
        if (!result.valid || !result.project) {
          reject(new Error(result.errors.join('; ')));
          return;
        }
        resolve(result.project);
      } catch (err: any) {
        reject(new Error(`Failed to parse project file: ${err.message}`));
      }
    };
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    reader.readAsText(file, 'UTF-8');
  });
}

// ─── Stage Sanitization ────────────────────────────────────────────────────────

/**
 * Map transitional stages to stable equivalents for restore.
 * e.g. 'calibrating' -> 'calibrated', 'analyzing' -> 'analyzed'
 */
export function sanitizeStageForRestore(stage: PipelineStage): PipelineStage {
  return STAGE_SANITIZE_MAP[stage] ?? stage;
}

// ─── Auto-Save Helpers ─────────────────────────────────────────────────────────

export function writeAutoSave(projectData: QCAProjectFile): void {
  try {
    const json = JSON.stringify(projectData);
    localStorage.setItem(AUTOSAVE_KEY, json);
  } catch {
    // localStorage full or unavailable
  }
}

export function readAutoSave(): QCAProjectFile | null {
  try {
    const raw = localStorage.getItem(AUTOSAVE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    const result = validateProjectFile(data);
    return result.valid && result.project ? result.project : null;
  } catch {
    return null;
  }
}

export function clearAutoSave(): void {
  try {
    localStorage.removeItem(AUTOSAVE_KEY);
  } catch {
    // ignore
  }
}

/** Save the text corpus data to localStorage for restore. */
export function writeTextCorpus(snapshot: QCAProjectTextCorpusSnapshot): void {
  try {
    localStorage.setItem(TEXTCORPUS_KEY, JSON.stringify(snapshot));
  } catch {
    // ignore
  }
}

export function readTextCorpus(): QCAProjectTextCorpusSnapshot | null {
  try {
    const raw = localStorage.getItem(TEXTCORPUS_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as QCAProjectTextCorpusSnapshot;
  } catch {
    return null;
  }
}

export function clearTextCorpus(): void {
  try {
    localStorage.removeItem(TEXTCORPUS_KEY);
  } catch {
    // ignore
  }
}
