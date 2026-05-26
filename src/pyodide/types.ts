// =============================================================================
// Bridge types for the Pyodide QCA engine
// =============================================================================
// These types define the contract between the React frontend and the Python
// QCA analysis engine running in Pyodide. They mirror the Pydantic models in
// src/experiment_engine/models.py but in TypeScript-friendly form.
//
// All data crossing the JS<->Python boundary is serialized as JSON.
// numpy arrays are transmitted as number[][] (JS) ↔ list[float] (Python).
// =============================================================================

// ── Text Calibration ────────────────────────────────────────────────────────

export interface CalibrationInput {
  /** Raw Chinese text strings to calibrate. */
  texts: string[]
  /** Domain key (one of TextDomain enum values). */
  domain: string
  /** Optional custom condition set. If omitted, uses domain defaults. */
  conditionSet?: Record<string, unknown>
}

export interface FuzzySetRecord {
  caseId: string
  memberships: Record<string, number>
}

export interface CalibrationOutput {
  fuzzySets: FuzzySetRecord[]
  conditionNames: string[]
  metadata: Record<string, unknown>
}

// ── QCA Analysis ────────────────────────────────────────────────────────────

export interface AnalysisInput {
  /** Condition name → array of fuzzy membership scores (one per case). */
  fuzzyData: Record<string, number[]>
  conditionNames: string[]
  outcomeName: string
  /** Consistency threshold for truth table rows (default 0.8). */
  consistencyThreshold?: number
  /** Minimum frequency threshold per truth table row (default 1). */
  frequencyThreshold?: number
}

export interface SolutionTerm {
  /** Condition names in this solution term. */
  conditions: string[]
  rawCoverage: number
  uniqueCoverage: number
  consistency: number
}

export interface TruthTableRow {
  rowId: string
  /** Binary vector of condition presence (length = k). */
  conditionVector: number[]
  nCases: number
  consistency: number
  outcome: number
}

export interface AnalysisOutput {
  truthTable: TruthTableRow[]
  solutions: {
    complex: SolutionTerm[]
    parsimonious: SolutionTerm[]
    intermediate: SolutionTerm[]
  }
  necessity: Record<string, { consistency: number; coverage: number }>
}

// ── Engine API ──────────────────────────────────────────────────────────────

/* ARCH-1 cleanup: EngineState, EngineStatus, StatusCallback were re-exported
   from the now-deleted engine.ts. These types are unused in the current
   architecture — the actual Pyodide engine lives in src/services/pyodide.*.
   If these type names are needed again, define them inline in this file. */
