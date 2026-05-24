/**
 * Pipeline Status Indicator — shows current stage, progress bar, elapsed time,
 * and the sequential stage pipeline so users can see where they are in the QCA workflow.
 */

import React from 'react';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import type { PipelineStage } from '../types/qca';

function stageLabel(stage: PipelineStage): string {
  switch (stage) {
    case 'idle': return 'Ready';
    case 'loading-pyodide': return 'Loading Engine...';
    case 'pyodide-ready': return 'Engine Ready';
    case 'loading-texts': return 'Loading Texts...';
    case 'calibrating': return 'Calibrating...';
    case 'calibrated': return 'Calibrated';
    case 'analyzing': return 'Analyzing...';
    case 'analyzed': return 'Analyzed';
    case 'prototype-analyzing': return 'Analyzing Prototype...';
    case 'prototype-analyzed': return 'Prototype Analyzed';
    case 'running-robustness': return 'Robustness...';
    case 'robustness-done': return 'Robustness Done';
    case 'exporting': return 'Exporting...';
    case 'done': return 'Complete';
    case 'error': return 'Error';
    default: return stage;
  }
}

export default function PipelineStatus() {
  const { state, reset } = useQCAPipeline();

  const elapsed = state.startTime ? (state.elapsedMs / 1000).toFixed(1) : null;

  return (
    <div className="card" style={{ padding: '16px' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              display: 'inline-block',
              width: 8,
              height: 8,
              borderRadius: '50%',
              background:
                state.stage === 'error'
                  ? 'var(--color-error)'
                  : state.stage === 'done'
                    ? 'var(--color-success)'
                    : state.stage === 'idle'
                      ? 'var(--color-text-secondary)'
                      : 'var(--color-accent)',
            }}
          />
          <span style={{ fontWeight: 600 }}>
            {stageLabel(state.stage)}
          </span>
          {elapsed && (
            <span className="mono" style={{ color: 'var(--color-text-secondary)', fontSize: '0.75rem' }}>
              {elapsed}s
            </span>
          )}
        </div>

        {state.stage !== 'idle' && state.stage !== 'loading-pyodide' && (
          <button className="btn btn-secondary" onClick={reset} style={{ fontSize: '0.75rem', padding: '4px 8px' }}>
            Reset
          </button>
        )}
      </div>

      {/* Progress bar */}
      {(state.stage !== 'idle' && state.stage !== 'done' && state.stage !== 'error') && (
        <div
          style={{
            height: 4,
            background: 'var(--color-border)',
            borderRadius: 2,
            overflow: 'hidden',
            marginBottom: '8px',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${state.progress}%`,
              background: 'var(--color-accent)',
              borderRadius: 2,
              transition: 'width 300ms ease',
            }}
          />
        </div>
      )}

      {/* Message / Error */}
      {state.stage === 'error' && (
        <div
          style={{
            padding: '8px 12px',
            background: 'var(--color-error-bg)',
            color: 'var(--color-error)',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.8125rem',
            fontFamily: 'var(--font-mono)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {state.error}
        </div>
      )}

      {state.message && state.stage !== 'error' && (
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
          {state.message}
        </p>
      )}
    </div>
  );
}
