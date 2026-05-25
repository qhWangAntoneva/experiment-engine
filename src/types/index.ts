/**
 * Legacy types — kept for backward compatibility with existing UI components.
 * New QCA-specific types are in ./qca.ts
 */

export interface SimulationParams {
  name: string
  description: string
  parameters: Record<string, number | string | boolean>
}

export interface SimulationResult {
  id: string
  timestamp: string
  params: SimulationParams
  outputs: Record<string, number | string>
  status: 'success' | 'failed' | 'running'
  duration: number
}

export interface MetricCardData {
  label: string
  value: string | number
  unit?: string
  trend?: 'up' | 'down' | 'stable'
  change?: number
  status?: 'normal' | 'warning' | 'critical'
}

export interface NavItem {
  label: string
  path: string
  icon: string
}

// Re-export all QCA types
export type {
  TextDomain,
  CalibrationType,
  PipelineStage,
  CalibrationParams,
  ConditionDefinition,
  ConditionSet,
  MembershipDataJSON,
  FuzzySetDataJSON,
  TruthTableRow,
  TruthTableJSON,
  SolutionTerm,
  QCASolution,
  QCASolutions,
  NecessityConditionResult,
  NecessityResults,
  SufficiencyResults,
  QCAAnalysisResultJSON,
  RobustnessTestResult,
  RobustnessReport,
  CounterfactualClassification,
  CounterfactualReport,
  TextCorpusEntry,
  CorpusSource,
  QCAAnalysisParams,
  QCAPipelineState,
  ExportResult,
  SavedAnalysisRun,
} from './qca'

export {
  DEFAULT_QCA_PARAMS,
  INITIAL_PIPELINE_STATE,
  CalibrationMethod,
  QCAVariant,
} from './qca'
