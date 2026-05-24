/**
 * Dashboard — QCA pipeline overview with pipeline status widget,
 * metric cards, and a quick-start panel.
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import PipelineStatus from '../components/PipelineStatus';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { usePyodide } from '../hooks/usePyodide';
import { useT } from '../i18n/I18nContext';
import type { MetricCardData, SavedAnalysisRun } from '../types/index';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const t = useT();
  const { state } = useQCAPipeline();
  const { initState, init } = usePyodide();
  const [recentRuns] = useState<SavedAnalysisRun[]>([]);

  // Compute metrics from actual pipeline state
  const metrics: MetricCardData[] = [
    {
      label: t('dashboard.pyodideStatus'),
      value: initState.status === 'ready' ? t('dashboard.statusReady') : initState.status === 'loading' ? t('dashboard.statusLoading') : t('dashboard.statusNotLoaded'),
      status: initState.status === 'ready' ? 'normal' : initState.status === 'error' ? 'critical' : 'warning',
    },
    {
      label: t('dashboard.pipelineStage'),
      value: state.stage,
      status: state.stage === 'error' ? 'critical' : state.stage === 'done' ? 'normal' : 'normal',
    },
    {
      label: t('dashboard.casesAnalyzed'),
      value: state.fuzzyData?.membership?.length ?? 0,
      trend: 'up',
      status: 'normal',
    },
    {
      label: t('dashboard.conditionsDefined'),
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
        <h2 className="page-title">{t('dashboard.title')}</h2>
        <p className="page-subtitle">{t('dashboard.subtitle')}</p>
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
        <h3 className="section-title">{t('dashboard.quickStart')}</h3>
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Step 1: Load engine */}
            <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span className="badge badge-success" style={{ width: 24, height: 24, justifyContent: 'center' }}>1</span>
                <h4 style={{ fontSize: '0.875rem' }}>{t('dashboard.step1Title')}</h4>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                {t('dashboard.step1Desc')}
              </p>
              <button
                className="btn btn-primary"
                onClick={handleLoadEngine}
                disabled={initState.status === 'ready' || initState.status === 'loading'}
                style={{ fontSize: '0.8125rem' }}
              >
                {initState.status === 'ready' ? t('dashboard.step1BtnReady') : initState.status === 'loading' ? t('dashboard.step1BtnLoading') : t('dashboard.step1BtnLoad')}
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
                    {(initState as any).message || t('common.loading')}
                  </p>
                </div>
              )}
            </div>

            {/* Step 2: Input data */}
            <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span className="badge badge-success" style={{ width: 24, height: 24, justifyContent: 'center' }}>2</span>
                <h4 style={{ fontSize: '0.875rem' }}>{t('dashboard.step2Title')}</h4>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                {t('dashboard.step2Desc')}
              </p>
              <button
                className="btn btn-primary"
                onClick={handleStartAnalysis}
                disabled={initState.status !== 'ready'}
                style={{ fontSize: '0.8125rem' }}
              >
                {t('dashboard.step2Btn')}
              </button>
            </div>

            {/* Step 3: Analyze */}
            <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span className="badge badge-success" style={{ width: 24, height: 24, justifyContent: 'center' }}>3</span>
                <h4 style={{ fontSize: '0.875rem' }}>{t('dashboard.step3Title')}</h4>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                {t('dashboard.step3Desc')}
              </p>
            </div>

            {/* Step 4: Review */}
            <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span className="badge badge-success" style={{ width: 24, height: 24, justifyContent: 'center' }}>4</span>
                <h4 style={{ fontSize: '0.875rem' }}>{t('dashboard.step4Title')}</h4>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                {t('dashboard.step4Desc')}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Runs */}
      {recentRuns.length > 0 && (
        <div className="dashboard-section">
          <h3 className="section-title">{t('dashboard.recentRuns')}</h3>
          <div className="card table-container">
            <table>
              <thead>
                <tr>
                  <th>{t('dashboard.runId')}</th>
                  <th>{t('dashboard.runName')}</th>
                  <th>{t('dashboard.runStatus')}</th>
                  <th>{t('dashboard.runCases')}</th>
                  <th>{t('dashboard.runConditions')}</th>
                  <th>{t('dashboard.runDuration')}</th>
                  <th>{t('dashboard.runDate')}</th>
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
          <p style={{ fontSize: '0.875rem' }}>{t('dashboard.emptyTitle')}</p>
          <p style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
            {t('dashboard.emptySubtitle')}
          </p>
        </div>
      )}
    </div>
  );
}
