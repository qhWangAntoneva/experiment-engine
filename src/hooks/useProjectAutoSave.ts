/**
 * useProjectAutoSave — automatically saves project state to localStorage
 * with 1000ms debounce after any pipeline change.
 */

import { useEffect, useRef } from 'react';
import type { QCAPipelineState } from '../types/qca';
import { serializeProject, writeAutoSave } from '../services/project-serialization';

const RECENT_RUNS_KEY = 'qca-recent-runs';

export function useProjectAutoSave(pipelineState: QCAPipelineState): void {
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Skip saving when stage is 'idle' and no data exists
    if (
      pipelineState.stage === 'idle' &&
      !pipelineState.conditionSet &&
      !pipelineState.fuzzyData &&
      !pipelineState.analysisResult
    ) {
      return;
    }

    // Clear existing debounce
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Debounce 1000ms
    debounceRef.current = setTimeout(() => {
      try {
        let recentRuns: any[] = [];
        const saved = localStorage.getItem(RECENT_RUNS_KEY);
        if (saved) recentRuns = JSON.parse(saved);

        const projectData = serializeProject({
          pipelineState: {
            stage: pipelineState.stage,
            conditionSet: pipelineState.conditionSet,
            fuzzyData: pipelineState.fuzzyData,
            prototypeFuzzyData: pipelineState.prototypeFuzzyData,
            analysisResult: pipelineState.analysisResult,
            prototypeAnalysisResult: pipelineState.prototypeAnalysisResult,
            analysisResultB: pipelineState.analysisResultB,
            robustnessReport: pipelineState.robustnessReport,
            counterfactualReport: pipelineState.counterfactualReport,
            multiOutcomeReport: pipelineState.multiOutcomeReport,
          },
          recentRuns,
          textCorpusData: {
            texts: pipelineState.textCorpusEntries,
            textCases: pipelineState.textCases,
            yamlContent: pipelineState.yamlContent,
            protoConditions: pipelineState.protoConditions,
          },
        });

        writeAutoSave(projectData);
      } catch {
        // Silently skip if save fails
      }
    }, 1000);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [
    pipelineState.stage,
    pipelineState.conditionSet,
    pipelineState.fuzzyData,
    pipelineState.prototypeFuzzyData,
    pipelineState.analysisResult,
    pipelineState.prototypeAnalysisResult,
    pipelineState.robustnessReport,
    pipelineState.counterfactualReport,
    pipelineState.textCorpusEntries,
    pipelineState.textCases,
    pipelineState.yamlContent,
    pipelineState.protoConditions,
  ]);
}
