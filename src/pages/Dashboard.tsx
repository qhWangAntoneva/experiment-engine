/**
 * Dashboard — QCA pipeline overview with pipeline status widget,
 * metric cards, and a quick-start panel.
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import PipelineStatus from '../components/PipelineStatus';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { usePyodide } from '../hooks/usePyodide';
import type { MetricCardData, SavedAnalysisRun } from '../types/index';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const { state } = useQCAPipeline();
  const { initState, init } = usePyodide();
  const [recentRuns] = useState<SavedAnalysisRun[]>([]);

  // Compute metrics from actual pipeline state
  const metrics: MetricCardData[] = [
    {
      label: 'Pyodide Status',
      value: initState.status === 'ready' ? 'Ready' : initState.status === 'loading' ? 'Loading...' : 'Not Loaded',
      status: initState.status === 'ready' ? 'normal' : initState.status === 'error' ? 'critical' : 'warning',
    },
    {
      label: 'Pipeline Stage',
      value: state.stage,
      status: state.stage === 'error' ? 'critical' : state.stage === 'done' ? 'normal' : 'normal',
    },
    {
      label: 'Cases Analyzed',
      value: state.fuzzyData?.membership?.length ?? 0,
      trend: 'up',
      status: 'normal',
    },
    {
      label: 'Conditions Defined',
      value: state.conditionSet?.conditions?.length ?? 0,
      status: 'normal',
    },
  ];

  const handleLoadEngine = useCallback(async () => {
    try {
      await init();
    } catch (err: any) {
      console.error('Failed to load Pyodide:', err);
    }
  }, [init]);

  const handleStartAnalysis = useCallback(() => {
    navigate('/input');
  }, [navigate]);

  return (
    <div className="dashboard">
      <div className="page-header">
        <h2 className="page-title">Dashboard</h2>
        <p className="page-subtitle">QCA Text Analysis Pipeline Overview</p>
      </div>

      {/* Pipeline Status Widget */}
      <div style={{ marginBottom: '20px' }}>
        <PipelineStatus />
      </div>

      {/* Metric Grid */}
      <div className="metric-grid">
        {metrics.map((m) => (
          <div
            key={m.label}
            className={`metric-card card ${m.status === 'warning' ? 'metric-warning' : ''} ${m.status === 'critical' ? 'metric-critical' : ''}`}
          >
            <div className="metric-header">
              <span className="metric-label">{m.label}</span>
            </div>
            <div className="metric-value">
              <span className="metric-number" style={m.status === 'critical' ? { color: 'var(--color-error)' } : {}}>
                {m.value}
              </span>
              {m.unit && <span className="metric-unit">{m.unit}</span>}
            </div>
            {m.trend && (
              <div className="metric-trend">
                <span className={`trend-arrow trend-${m.trend}`}>
                  {m.trend === 'up' ? 'arrow_upward' : m.trend === 'down' ? 'arrow_downward' : 'horizontal_rule'}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Quick-Start Panel */}
      <div className="dashboard-section">
        <h3 className="section-title">Quick Start</h3>
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Step 1: Load engine */}
            <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span className="badge badge-success" style={{ width: 24, height: 24, justifyContent: 'center' }}>1</span>
                <h4 style={{ fontSize: '0.875rem' }}>Load Analysis Engine</h4>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                Start Pyodide (Python in browser). First load takes ~30s. Subsequent loads are cached.
              </p>
              <button
                className="btn btn-primary"
                onClick={handleLoadEngine}
                disabled={initState.status === 'ready' || initState.status === 'loading'}
                style={{ fontSize: '0.8125rem' }}
              >
                {initState.status === 'ready' ? 'Engine Ready' : initState.status === 'loading' ? 'Loading...' : 'Load Engine'}
              </button>
              {initState.status === 'loading' && (
                <div style={{ marginTop: '8px' }}>
                  <div style={{ width: '100%', height: 3, background: 'var(--color-border)', borderRadius: 2 }}>
                    <div
                      style={{
                        width: `${(initState as any).progress || 0}%`,
                        height: '100%',
                        background: 'var(--color-accent)',
                        borderRadius: 2,
                        transition: 'width 200ms ease',
                      }}
                    />
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                    {(initState as any).message || 'Loading...'}
                  </p>
                </div>
              )}
            </div>

            {/* Step 2: Input data */}
            <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span className="badge badge-success" style={{ width: 24, height: 24, justifyContent: 'center' }}>2</span>
                <h4 style={{ fontSize: '0.875rem' }}>Upload Data & Define Conditions</h4>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                Upload Chinese text corpus (CSV/JSON/TXT) and define fuzzy-set calibration conditions.
              </p>
              <button
                className="btn btn-primary"
                onClick={handleStartAnalysis}
                disabled={initState.status !== 'ready'}
                style={{ fontSize: '0.8125rem' }}
              >
                Go to Data Input
              </button>
            </div>

            {/* Step 3: Analyze */}
            <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span className="badge badge-success" style={{ width: 24, height: 24, justifyContent: 'center' }}>3</span>
                <h4 style={{ fontSize: '0.875rem' }}>Run QCA Analysis</h4>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                Truth table construction, Quine-McCluskey minimization, necessity & sufficiency tests.
              </p>
            </div>

            {/* Step 4: Review */}
            <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span className="badge badge-success" style={{ width: 24, height: 24, justifyContent: 'center' }}>4</span>
                <h4 style={{ fontSize: '0.875rem' }}>Review & Export Results</h4>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                View truth tables, solution formulas, necessity/sufficiency metrics. Export to CSV, JSON, or LaTeX.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Runs */}
      {recentRuns.length > 0 && (
        <div className="dashboard-section">
          <h3 className="section-title">Recent Analysis Runs</h3>
          <div className="card table-container">
            <table>
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Cases</th>
                  <th>Conditions</th>
                  <th>Duration</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {recentRuns.map((run) => (
                  <tr key={run.id}>
                    <td className="mono">{run.id}</td>
                    <td>{run.name}</td>
                    <td>
                      <span className={`badge ${run.status === 'success' ? 'badge-success' : run.status === 'running' ? 'badge-warning' : 'badge-error'}`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="mono">{run.caseCount}</td>
                    <td className="mono">{run.conditionCount}</td>
                    <td className="mono">{run.duration.toFixed(1)}s</td>
                    <td>{run.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {recentRuns.length === 0 && state.stage === 'idle' && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--color-text-secondary)' }}>
          <p style={{ fontSize: '0.875rem' }}>No analysis runs yet.</p>
          <p style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
            Load the engine and upload data to start your first QCA analysis.
          </p>
        </div>
      )}
    </div>
  );
}
