/**
 * Dashboard — QCA pipeline overview with pipeline status widget,
 * metric cards, project save/load, and a quick-start panel.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import PipelineStatus from '../components/PipelineStatus';
import PerformancePanel from '../components/PerformancePanel';
import TemplateLibrary from '../components/TemplateLibrary';
import ShareImportModal from '../components/ShareImportModal';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { usePyodide } from '../hooks/usePyodide';
import { useT } from '../i18n/I18nContext';
import {
  serializeProject,
  downloadProjectFile,
  readProjectFile,
  readAutoSave,
  clearAutoSave,
  readTextCorpus,
  clearTextCorpus,
  sanitizeStageForRestore,
} from '../services/project-serialization';
import { useProjectAutoSave } from '../hooks/useProjectAutoSave';
import type { MetricCardData, SavedAnalysisRun } from '../types/index';
import './Dashboard.css';

const RECENT_RUNS_KEY = 'qca-recent-runs';
const RECENT_RUNS_MAX = 20;
const RECENT_RUNS_EVENT = 'recent-runs-updated';

export default function Dashboard() {
  const navigate = useNavigate();
  const t = useT();
  const { state, hydrateFromProject } = useQCAPipeline();
  const { initState, init } = usePyodide();
  const fileLoadRef = useRef<HTMLInputElement>(null);

  // Auto-save project to localStorage
  useProjectAutoSave(state);

  const [recentRuns, setRecentRuns] = useState<SavedAnalysisRun[]>(() => {
    try {
      const saved = localStorage.getItem(RECENT_RUNS_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Project save/load state
  const [projectMessage, setProjectMessage] = useState<string | null>(null);
  const [projectMessageType, setProjectMessageType] = useState<'success' | 'error'>('success');

  // Auto-restore banner state
  const [autoSaveBanner, setAutoSaveBanner] = useState<{
    project: any;
    timestamp: string;
  } | null>(null);

  // Check for auto-save on mount
  useEffect(() => {
    try {
      const saved = readAutoSave();
      if (saved && state.stage === 'idle' && !state.conditionSet) {
        setAutoSaveBanner({
          project: saved,
          timestamp: (() => {
            try {
              // Format the timestamp for display
              const d = new Date(saved.savedAt);
              return d.toLocaleString();
            } catch {
              return saved.savedAt || t('common.notLoaded');
            }
          })(),
        });
      }
    } catch {
      // No valid auto-save found
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Listen for analysis-completed events from QCAPipelineContext
  useEffect(() => {
    const handleRunsUpdated = () => {
      try {
        const saved = localStorage.getItem(RECENT_RUNS_KEY);
        setRecentRuns(saved ? JSON.parse(saved) : []);
      } catch {}
    };
    window.addEventListener(RECENT_RUNS_EVENT, handleRunsUpdated);
    return () => window.removeEventListener(RECENT_RUNS_EVENT, handleRunsUpdated);
  }, []);

  // Compute metrics from actual pipeline state
  const metrics: MetricCardData[] = [
    {
      label: t('dashboard.pyodideStatus'),
      value: initState.status === 'ready'
        ? t('dashboard.statusReady')
        : initState.status === 'loading'
        ? t('dashboard.statusLoading')
        : initState.status === 'error'
        ? t('dashboard.statusError')
        : t('dashboard.statusNotLoaded'),
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

  const handleClearData = useCallback(() => {
    if (!window.confirm(t('dashboard.clearDataConfirm'))) return;
    // Keep qca-language (user's language preference)
    const keysToRemove = [
      'qca-settings',
      'qca-params',
      'qca-bert-model',
      RECENT_RUNS_KEY,
      'qca-project-autosave',
      'qca-project-textcorpus',
    ];
    for (const key of keysToRemove) {
      try { localStorage.removeItem(key); } catch {}
    }
    setRecentRuns([]);
    setAutoSaveBanner(null);
  }, [t]);

  // ─── Project Save ──────────────────────────────────────────────────────────

  const handleSaveProject = useCallback(() => {
    if (!state.conditionSet) {
      setProjectMessage(t('projectSave.saveProjectNoData'));
      setProjectMessageType('error');
      return;
    }

    try {
      let recentRunsData: SavedAnalysisRun[] = [];
      const saved = localStorage.getItem(RECENT_RUNS_KEY);
      if (saved) recentRunsData = JSON.parse(saved);

      const projectData = serializeProject({
        pipelineState: {
          stage: state.stage,
          conditionSet: state.conditionSet,
          fuzzyData: state.fuzzyData,
          prototypeFuzzyData: state.prototypeFuzzyData,
          analysisResult: state.analysisResult,
          prototypeAnalysisResult: state.prototypeAnalysisResult,
          analysisResultB: state.analysisResultB,
          robustnessReport: state.robustnessReport,
          counterfactualReport: state.counterfactualReport,
          multiOutcomeReport: state.multiOutcomeReport,
        },
        recentRuns: recentRunsData,
        textCorpusData: {
          texts: state.textCorpusEntries,
          textCases: state.textCases,
          yamlContent: state.yamlContent,
          protoConditions: state.protoConditions,
        },
      });

      downloadProjectFile(projectData);

      const now = new Date();
      const pad = (n: number) => String(n).padStart(2, '0');
      const filename = `qca-project-${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}.qca`;
      setProjectMessage(t('projectSave.saveProjectSuccess', filename));
      setProjectMessageType('success');
    } catch (err: any) {
      setProjectMessage(`${t('projectSave.loadProjectError')}${err.message}`);
      setProjectMessageType('error');
    }
  }, [state, t]);

  // ─── Project Load ──────────────────────────────────────────────────────────

  const handleLoadProjectClick = useCallback(() => {
    fileLoadRef.current?.click();
  }, []);

  const handleFileSelected = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      try {
        const project = await readProjectFile(file);

        // Restore settings, params, BERT model
        if (project.settings) {
          try { localStorage.setItem('qca-settings', JSON.stringify(project.settings)); } catch {}
        }
        if (project.params) {
          try { localStorage.setItem('qca-params', JSON.stringify(project.params)); } catch {}
        }
        if (project.bertModel) {
          try { localStorage.setItem('qca-bert-model', JSON.stringify(project.bertModel)); } catch {}
        }

        // Sanitize stage
        const safeStage = sanitizeStageForRestore(project.pipeline.stage);

        // Restore recent runs
        if (project.recentRuns && project.recentRuns.length > 0) {
          try { localStorage.setItem(RECENT_RUNS_KEY, JSON.stringify(project.recentRuns)); } catch {}
          window.dispatchEvent(new Event(RECENT_RUNS_EVENT));
        }

        // Hydrate pipeline state
        hydrateFromProject(
          {
            stage: safeStage,
            conditionSet: project.pipeline.conditionSet,
            fuzzyData: project.pipeline.fuzzyData,
            prototypeFuzzyData: project.pipeline.prototypeFuzzyData,
            analysisResult: project.pipeline.analysisResult,
            prototypeAnalysisResult: project.pipeline.prototypeAnalysisResult,
            analysisResultB: project.pipeline.analysisResultB ?? null,
            robustnessReport: project.pipeline.robustnessReport,
            counterfactualReport: project.pipeline.counterfactualReport,
            multiOutcomeReport: project.pipeline.multiOutcomeReport ?? null,
          },
          project.settings,
          project.params,
          project.bertModel,
          project.recentRuns,
          {
            texts: project.textCorpus.texts,
            textCases: project.textCorpus.textCases,
            yamlContent: project.textCorpus.yamlContent,
            protoConditions: project.textCorpus.protoConditions,
          }
        );

        setProjectMessage(t('projectSave.loadProjectSuccess'));
        setProjectMessageType('success');
        setAutoSaveBanner(null);

        // Navigate to appropriate page based on restored stage
        if (safeStage !== 'idle') {
          setTimeout(() => navigate('/results'), 500);
        }
      } catch (err: any) {
        setProjectMessage(`${t('projectSave.loadProjectInvalid')}${err.message}`);
        setProjectMessageType('error');
      }

      // Reset file input
      if (fileLoadRef.current) fileLoadRef.current.value = '';
    },
    [hydrateFromProject, navigate, t]
  );

  // ─── Auto-restore ──────────────────────────────────────────────────────────

  const handleAutoRestore = useCallback(() => {
    if (!autoSaveBanner?.project) return;
    const project = autoSaveBanner.project;

    // Same logic as handleFileSelected but from auto-save data
    if (project.settings) {
      try { localStorage.setItem('qca-settings', JSON.stringify(project.settings)); } catch {}
    }
    if (project.params) {
      try { localStorage.setItem('qca-params', JSON.stringify(project.params)); } catch {}
    }
    if (project.bertModel) {
      try { localStorage.setItem('qca-bert-model', JSON.stringify(project.bertModel)); } catch {}
    }

    const safeStage = sanitizeStageForRestore(project.pipeline.stage);

    if (project.recentRuns && project.recentRuns.length > 0) {
      try { localStorage.setItem(RECENT_RUNS_KEY, JSON.stringify(project.recentRuns)); } catch {}
      window.dispatchEvent(new Event(RECENT_RUNS_EVENT));
    }

    hydrateFromProject(
      {
        stage: safeStage,
        conditionSet: project.pipeline.conditionSet,
        fuzzyData: project.pipeline.fuzzyData,
        prototypeFuzzyData: project.pipeline.prototypeFuzzyData,
        analysisResult: project.pipeline.analysisResult,
        prototypeAnalysisResult: project.pipeline.prototypeAnalysisResult,
        analysisResultB: project.pipeline.analysisResultB ?? null,
        robustnessReport: project.pipeline.robustnessReport,
        counterfactualReport: project.pipeline.counterfactualReport,
        multiOutcomeReport: project.pipeline.multiOutcomeReport ?? null,
      },
      project.settings,
      project.params,
      project.bertModel,
      project.recentRuns,
      {
        texts: project.textCorpus.texts,
        textCases: project.textCorpus.textCases,
        yamlContent: project.textCorpus.yamlContent,
        protoConditions: project.textCorpus.protoConditions,
      }
    );

    setAutoSaveBanner(null);
    setProjectMessage(t('projectSave.loadProjectSuccess'));
    setProjectMessageType('success');

    if (safeStage !== 'idle') {
      setTimeout(() => navigate('/results'), 500);
    }
  }, [autoSaveBanner, hydrateFromProject, navigate, t]);

  const handleDismissRestore = useCallback(() => {
    setAutoSaveBanner(null);
    clearAutoSave();
  }, []);

  return (
    <div className="dashboard">
      <div className="page-header">
        <h2 className="page-title">{t('dashboard.title')}</h2>
        <p className="page-subtitle">{t('dashboard.subtitle')}</p>
        <p className="page-desc">{t('dashboard.description')}</p>
      </div>

      {/* Auto-Restore Banner */}
      {autoSaveBanner && (
        <div
          className="card"
          style={{
            padding: '12px 16px',
            marginBottom: '16px',
            borderLeft: '4px solid var(--color-accent)',
            background: 'var(--color-accent-bg, #eff6ff)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
          }}
        >
          <span style={{ fontSize: '0.8125rem', flex: 1 }}>
            {t('projectSave.autoRestoreBanner', autoSaveBanner.timestamp)}
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn btn-primary"
              onClick={handleAutoRestore}
              style={{ fontSize: '0.8125rem', padding: '4px 12px' }}
            >
              {t('projectSave.autoRestoreBtn')}
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleDismissRestore}
              style={{ fontSize: '0.8125rem', padding: '4px 12px' }}
            >
              {t('projectSave.autoRestoreDismiss')}
            </button>
          </div>
        </div>
      )}

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

      {/* BERT Performance */}
      <PerformancePanel />

      {/* Share Import Modal (P1-13) */}
      <ShareImportModal />

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
                onClick={handleLoadEngine}
                disabled={initState.status === 'ready' || initState.status === 'loading'}
                className={`btn ${initState.status === 'error' ? 'btn-danger' : 'btn-primary'}`}
              >
                {initState.status === 'ready' ? t('dashboard.step1BtnReady') : initState.status === 'loading' ? t('dashboard.step1BtnLoading') : initState.status === 'error' ? t('dashboard.step1BtnError') : t('dashboard.step1BtnLoad')}
              </button>
              {initState.status === 'error' && (
                <div style={{ marginTop: '8px', padding: '8px', background: 'var(--color-error-bg, #fef2f2)', border: '1px solid var(--color-error, #ef4444)', borderRadius: '4px', fontSize: '0.75rem', color: 'var(--color-error, #ef4444)' }}>
                  {(initState as any).error || 'Unknown error'}
                </div>
              )}
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

      {/* Project Save/Load Section */}
      <div className="dashboard-section">
        <h3 className="section-title">{t('projectSave.sectionTitle')}</h3>
        <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
          {t('projectSave.sectionDesc')}
        </p>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              className="btn btn-primary"
              onClick={handleSaveProject}
              disabled={!state.conditionSet}
              title={state.conditionSet ? t('projectSave.saveProjectTooltip') : t('projectSave.saveProjectNoData')}
              style={{ fontSize: '0.8125rem' }}
            >
              {t('projectSave.saveProjectBtn')}
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleLoadProjectClick}
              title={t('projectSave.loadProjectTooltip')}
              style={{ fontSize: '0.8125rem' }}
            >
              {t('projectSave.loadProjectBtn')}
            </button>
            <input
              ref={fileLoadRef}
              type="file"
              accept=".qca"
              onChange={handleFileSelected}
              style={{ display: 'none' }}
            />
            {projectMessage && (
              <span
                style={{
                  fontSize: '0.8125rem',
                  color: projectMessageType === 'error' ? 'var(--color-error)' : 'var(--color-success)',
                  fontWeight: 600,
                }}
              >
                {projectMessage}
              </span>
            )}
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
      {recentRuns.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--color-text-secondary)' }}>
          <p style={{ fontSize: '0.875rem' }}>{t('dashboard.emptyTitle')}</p>
          <p style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
            {t('dashboard.emptyAction')}
          </p>
        </div>
      )}

      {/* Template Library (P1-13) */}
      <TemplateLibrary />

      {/* Privacy Section */}
      <section className="privacy-section">
        <h3 className="privacy-section-title">{t('dashboard.privacyTitle')}</h3>
        <p className="privacy-section-desc">{t('dashboard.privacyDesc')}</p>
        <button className="btn btn-outline" onClick={handleClearData}>
          {t('dashboard.clearAllData')}
        </button>
      </section>
    </div>
  );
}
