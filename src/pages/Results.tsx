/**
 * Results — displays all QCA analysis output in organized sections:
 *   1. Truth Table (sortable table + heatmap)
 *   2. Solutions (complex/parsimonious/intermediate)
 *   3. Necessity / Sufficiency
 *   4. Robustness (if run)
 *   5. Export buttons
 *
 * When prototype analysis results are available, a view-mode toggle
 * lets users switch between raw-text results, prototype results, and
 * a side-by-side comparison with difference highlighting.
 */

import React, { useState, useCallback, useMemo } from 'react';
import PipelineStatus from '../components/PipelineStatus';
import TruthTableViewer from '../components/TruthTableViewer';
import SolutionViewer from '../components/SolutionViewer';
import FuzzySetHeatmap from '../components/FuzzySetHeatmap';
import NecessityXYPlot from '../components/NecessityXYPlot';
import CaseMembershipTable from '../components/CaseMembershipTable';
import {
  CompareView,
  NecessityTable,
  ComparisonMetricChip,
  ComparisonSummary,
} from '../components/CompareView';
import { loadSnapshot, saveSnapshot } from '../utils/snapshotStorage';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { useQCAWorkflow } from '../hooks/useQCAWorkflow';
import { useT } from '../i18n/I18nContext';
import HelpTooltip from '../components/HelpTooltip';
import type {
  QCAAnalysisResultJSON,
  ConditionSet,
  ConditionDefinition,
  SolutionTerm,
  QCASolution,
  NecessityResults,
  ParameterSnapshot,
} from '../types/qca';
import { DEFAULT_QCA_PARAMS } from '../types/qca';
import './Results.css';

type ViewMode = 'raw' | 'prototype' | 'compare';

export default function Results() {
  const t = useT();
  const { state } = useQCAPipeline();
  const { runExport } = useQCAWorkflow();
  const [activeTab, setActiveTab] = useState<'truth-table' | 'solutions' | 'necessity' | 'robustness' | 'cases'>(() => {
    const hasFuzzy = !!(state.fuzzyData || state.prototypeFuzzyData);
    const hasAnalysis = !!(state.analysisResult || state.prototypeAnalysisResult);
    return hasFuzzy && !hasAnalysis ? 'cases' : 'solutions';
  });
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('raw');
  const [latexPreviewContent, setLatexPreviewContent] = useState<string | null>(null);

  // Toast notification state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Snapshot state (P1-7)
  const [snapshotMsg, setSnapshotMsg] = useState<string | null>(null);

  const hasResults = !!state.analysisResult || !!(state.fuzzyData || state.prototypeFuzzyData);

  const hasPrototypeResults = !!state.prototypeAnalysisResult;
  const hasRobustness = !!state.robustnessReport;

  // Derive active data based on view mode
  const activeResult: QCAAnalysisResultJSON | null = useMemo(() => {
    if (viewMode === 'prototype') return state.prototypeAnalysisResult;
    return state.analysisResult;
  }, [viewMode, state.analysisResult, state.prototypeAnalysisResult]);

  const handleSaveSnapshot = useCallback(
    (label: 'a' | 'b') => {
      const result = activeResult || state.analysisResult;
      if (!result?.condition_set) {
        setSnapshotMsg(t('results.noResults'));
        return;
      }
      let params = { ...DEFAULT_QCA_PARAMS };
      try {
        const raw = localStorage.getItem('qca-params');
        if (raw) params = JSON.parse(raw);
      } catch { /* use defaults */ }
      const snapshot: ParameterSnapshot = {
        id: `snap-${Date.now()}`,
        name: result.metadata?.run_name as string || `Snapshot ${label.toUpperCase()}`,
        timestamp: new Date().toISOString(),
        conditionSet: result.condition_set,
        analysisParams: params,
        result,
      };
      saveSnapshot(label, snapshot);
      setSnapshotMsg(`Saved as Snapshot ${label.toUpperCase()}`);
      setTimeout(() => setSnapshotMsg(null), 2000);
    },
    [activeResult, state.analysisResult, t],
  );

  // Derive fuzzy data for Cases tab based on view mode
  const casesFuzzyData = viewMode === 'prototype' ? state.prototypeFuzzyData : state.fuzzyData;

  const tabs = [
    { key: 'solutions' as const, label: t('results.tabSolutions'), available: !!activeResult?.solutions },
    { key: 'cases' as const, label: t('results.tabCases'), available: !!(state.fuzzyData || state.prototypeFuzzyData) },
    { key: 'truth-table' as const, label: t('results.tabTruthTable'), available: !!activeResult?.truth_table },
    { key: 'necessity' as const, label: t('results.tabNecessity'), available: !!activeResult?.necessity },
    { key: 'robustness' as const, label: t('results.tabRobustness'), available: hasRobustness && viewMode !== 'prototype' },
  ];

  const handleExport = useCallback(
    async (format: 'csv' | 'json' | 'latex' | 'docx') => {
      setExporting(true);
      setExportError(null);
      setExportSuccess(null);
      try {
        const blob = await runExport(format);

        // For LaTeX: show preview modal before download
        if (format === 'latex') {
          const content = await blob.text();
          setLatexPreviewContent(content);
          return;
        }

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const extMap: Record<string, string> = {
          csv: 'csv',
          json: 'json',
          latex: 'tex',
          docx: 'docx',
        };
        a.download = `qca-analysis.${extMap[format]}`;
        a.click();
        URL.revokeObjectURL(url);
        setExportSuccess(t('results.exportedAs', format.toUpperCase()));
        setToast({ message: t('results.exportedAs', format.toUpperCase()), type: 'success' });
        setTimeout(() => setToast(null), 3000);
      } catch (err: any) {
        setExportError(t('results.exportFailed') + err.message);
        setToast({ message: t('results.exportFailed') + err.message, type: 'error' });
        setTimeout(() => setToast(null), 3000);
      } finally {
        setExporting(false);
      }
    },
    [runExport, t]
  );

  const handleLatexDownload = useCallback(async () => {
    if (!latexPreviewContent) return;
    setExporting(true);
    try {
      const blob = await runExport('latex');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'qca-analysis.tex';
      a.click();
      URL.revokeObjectURL(url);
      setLatexPreviewContent(null);
      setExportSuccess(t('results.exportedAs', 'LATEX'));
      setToast({ message: t('results.exportedAs', 'LATEX'), type: 'success' });
      setTimeout(() => setToast(null), 3000);
    } catch (err: any) {
      setExportError(t('results.exportFailed') + err.message);
      setToast({ message: t('results.exportFailed') + err.message, type: 'error' });
      setTimeout(() => setToast(null), 3000);
    } finally {
      setExporting(false);
    }
  }, [latexPreviewContent, runExport, t]);

  // ── Empty state ──────────────────────────────────────────────────────────
  if (!hasResults) {
    return (
      <div className="results">
        <div className="page-header">
          <h2 className="page-title">{t('results.title')}</h2>
          <p className="page-subtitle">{t('results.subtitle')}</p>
        </div>
        <PipelineStatus />
        <div className="results-empty">
          <p style={{ fontSize: '0.875rem', marginBottom: '8px' }}>{t('results.noResults')}</p>
          <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
            {t('results.noResultsHint')}
          </p>
        </div>
      </div>
    );
  }

  const { analysisResult, prototypeAnalysisResult, fuzzyData, robustnessReport } = state;
  const showViewToggle = hasPrototypeResults;

  // Derive data source for summary stats
  const summaryFuzzyData = viewMode === 'prototype' ? state.prototypeFuzzyData : fuzzyData;

  return (
    <div className="results">
      <div className="page-header">
        <h2 className="page-title">{t('results.title')}</h2>
        <p className="page-subtitle">{t('results.subtitle')}</p>
      </div>

      <PipelineStatus />

      {/* ── View Mode Toggle (only when prototype results exist) ── */}
      {showViewToggle && (
        <div className="view-mode-toggle">
          <button
            className={`view-mode-btn ${viewMode === 'raw' ? 'active' : ''}`}
            onClick={() => setViewMode('raw')}
          >
            {t('results.rawText')}
          </button>
          <button
            className={`view-mode-btn ${viewMode === 'prototype' ? 'active' : ''}`}
            onClick={() => setViewMode('prototype')}
          >
            {t('results.prototype')}
          </button>
          <button
            className={`view-mode-btn ${viewMode === 'compare' ? 'active' : ''}`}
            onClick={() => setViewMode('compare')}
          >
            {t('results.compare')}
          </button>
        </div>
      )}

      {/* ── Comparison Summary (compare mode only) ── */}
      {viewMode === 'compare' && analysisResult && prototypeAnalysisResult && (
        <ComparisonSummary raw={analysisResult} prototype={prototypeAnalysisResult} t={t} />
      )}

      {/* Toolbar */}
      <div className="results-toolbar">
        <div className="toolbar-left" style={{ display: 'flex', gap: '8px' }}>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8125rem' }}
            onClick={() => handleExport('csv')}
            disabled={exporting}
          >
            {t('results.exportCsv')}
          </button>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8125rem' }}
            onClick={() => handleExport('json')}
            disabled={exporting}
          >
            {t('results.exportJson')}
          </button>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8125rem' }}
            onClick={() => handleExport('latex')}
            disabled={exporting}
          >
            {t('results.exportLatex')}
          </button>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8125rem' }}
            onClick={() => handleExport('docx')}
            disabled={exporting}
          >
            {t('results.exportDocx')}
          </button>
          <span style={{ width: '1px', height: '20px', background: 'var(--color-border)', alignSelf: 'center', margin: '0 4px' }} />
          <button
            className="btn btn-primary"
            style={{ fontSize: '0.8125rem' }}
            onClick={() => handleSaveSnapshot('a')}
            disabled={!activeResult}
            title={t('results.saveSnapshotA')}
          >
            Snapshot A
          </button>
          <button
            className="btn btn-primary"
            style={{ fontSize: '0.8125rem' }}
            onClick={() => handleSaveSnapshot('b')}
            disabled={!activeResult}
            title={t('results.saveSnapshotB')}
          >
            Snapshot B
          </button>
          {snapshotMsg && (
            <span
              style={{
                fontSize: '0.75rem',
                color: 'var(--color-success)',
                alignSelf: 'center',
              }}
            >
              {snapshotMsg}
            </span>
          )}
          {exportSuccess && (
            <span
              style={{
                fontSize: '0.75rem',
                color: 'var(--color-success)',
                alignSelf: 'center',
              }}
            >
              {exportSuccess}
            </span>
          )}
          {exportError && (
            <span
              style={{
                fontSize: '0.75rem',
                color: 'var(--color-error)',
                alignSelf: 'center',
              }}
            >
              {exportError}
            </span>
          )}
        </div>
      </div>

      {/* ── Compare Mode: Side-by-side ── */}
      {viewMode === 'compare' && analysisResult && prototypeAnalysisResult ? (
        <CompareView
          raw={analysisResult}
          prototype={prototypeAnalysisResult}
          t={t}
        />
      ) : (
        <>
          {/* Summary Stats */}
          {activeResult && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '20px' }}>
              <MetricChip label={t('results.cases')} value={summaryFuzzyData?.membership?.length ?? 0} />
              <MetricChip label={t('results.conditions')} value={summaryFuzzyData?.condition_names?.length ?? 0} />
              <MetricChip
                label={t('results.consistency')}
                value={activeResult.solutions?.complex?.solution_consistency?.toFixed(3) ?? '-'}
                helpText={t('help.consistency')}
              />
              <MetricChip
                label={t('results.coverage')}
                value={activeResult.solutions?.complex?.solution_coverage?.toFixed(3) ?? '-'}
                helpText={t('help.coverage')}
              />
              <MetricChip
                label={t('results.robustness')}
                value={robustnessReport ? robustnessReport.overall_robustness.toFixed(2) : t('results.nA')}
                helpText={t('help.robustness')}
              />
            </div>
          )}

          {/* Tabs */}
          <div style={{ display: 'flex', gap: '2px', marginBottom: '16px', borderBottom: '1px solid var(--color-border)' }}>
            {tabs
              .filter((t) => t.available)
              .map((tab) => (
                <button
                  key={tab.key}
                  className={activeTab === tab.key ? 'btn btn-primary' : 'btn btn-secondary'}
                  onClick={() => setActiveTab(tab.key)}
                  style={{
                    borderBottomLeftRadius: 0,
                    borderBottomRightRadius: 0,
                    borderBottom: activeTab === tab.key ? '2px solid var(--color-accent)' : 'none',
                    fontSize: '0.8125rem',
                  }}
                >
                  {tab.label}
                </button>
              ))}
          </div>

          {/* Tab Content */}
          <div>
            {activeTab === 'truth-table' && activeResult?.truth_table && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
                <div className="card" style={{ padding: '16px' }}>
                  <TruthTableViewer truthTable={activeResult.truth_table} />
                </div>
                <div className="card" style={{ padding: '16px' }}>
                  <FuzzySetHeatmap truthTable={activeResult.truth_table} height={350} />
                </div>
              </div>
            )}

            {activeTab === 'solutions' && activeResult?.solutions && (
              <>
                <div className="card" style={{ padding: '16px' }}>
                  <SolutionViewer solutions={activeResult.solutions} showAll={true} />
                </div>
                <AutoInterpretation result={activeResult} />
              </>
            )}

            {activeTab === 'cases' && casesFuzzyData && (
              <div className="card" style={{ padding: '16px' }}>
                <CaseMembershipTable data={casesFuzzyData} />
              </div>
            )}

            {activeTab === 'necessity' && activeResult?.necessity && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="card" style={{ padding: '16px' }}>
                  <NecessityXYPlot necessity={activeResult.necessity} height={400} />
                </div>
                <div className="card" style={{ padding: '16px' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '12px' }}>
                    {t('results.necessityTitle', activeResult.necessity.threshold)}
                  </h4>
                  <div className="table-container">
                    <table style={{ fontSize: '0.8125rem' }}>
                      <thead>
                        <tr>
                          <th>{t('results.colCondition')}</th>
                          <th>{t('results.colConsistency')}</th>
                          <th>{t('results.colCoverage')}</th>
                          <th>{t('results.colNecessary')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activeResult.necessity.conditions.map((c, idx) => (
                          <tr
                            key={idx}
                            style={{
                              background: c.is_necessary ? 'rgba(5, 150, 105, 0.05)' : undefined,
                            }}
                          >
                            <td style={{ fontWeight: 600 }}>{c.condition_name}</td>
                            <td className="mono">{c.consistency.toFixed(3)}</td>
                            <td className="mono">{c.coverage.toFixed(3)}</td>
                            <td>
                              {c.is_necessary ? (
                                <span className="badge badge-success">{t('common.yes')}</span>
                              ) : (
                                <span className="badge badge-error">{t('common.no')}</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'robustness' && robustnessReport && (
              <div className="card" style={{ padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                    {t('results.robustnessReport')}
                  </h4>
                  <span className={`badge ${robustnessReport.overall_robustness >= 0.8 ? 'badge-success' : 'badge-warning'}`}>
                    {t('results.overall')}{robustnessReport.overall_robustness.toFixed(2)}
                  </span>
                </div>

                {robustnessReport.summary && (
                  <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
                    {robustnessReport.summary}
                  </p>
                )}

                {robustnessReport.tests.map((test, idx) => (
                  <div
                    key={idx}
                    className="card"
                    style={{
                      padding: '12px 16px',
                      marginBottom: '8px',
                      borderColor: test.passed ? 'var(--color-success)' : 'var(--color-warning)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <strong style={{ fontSize: '0.8125rem' }}>{test.test_name}</strong>
                        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                          {t('results.varying')}{test.parameter_varied}
                        </p>
                      </div>
                      <span className={`badge ${test.passed ? 'badge-success' : 'badge-warning'}`}>
                        {test.passed ? t('common.passed') : t('common.unstable')}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '0.75rem' }}>
                      <span className="mono" style={{ color: 'var(--color-text-secondary)' }}>
                        {t('results.stability')}{test.solution_stability.map((s) => s.toFixed(2)).join(', ')}
                      </span>
                      <span className="mono" style={{ color: 'var(--color-text-secondary)' }}>
                        {t('results.params')}{test.parameter_values.map((v) => v.toFixed(2)).join(', ')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* ── LaTeX Preview Modal ── */}
      {latexPreviewContent && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2000,
            padding: '20px',
          }}
          onClick={() => setLatexPreviewContent(null)}
        >
          <div
            style={{
              background: 'var(--color-bg-primary)',
              borderRadius: 'var(--radius-lg)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.25)',
              width: '100%',
              maxWidth: '720px',
              maxHeight: '80vh',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid var(--color-border)' }}>
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: 0 }}>LaTeX Preview</h3>
              <button className="btn btn-secondary" onClick={() => setLatexPreviewContent(null)} style={{ fontSize: '0.75rem', padding: '4px 10px' }}>x</button>
            </div>
            <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
              <textarea
                readOnly
                value={latexPreviewContent}
                style={{
                  width: '100%',
                  minHeight: '300px',
                  fontFamily: 'var(--font-mono, monospace)',
                  fontSize: '0.75rem',
                  lineHeight: 1.6,
                  padding: '12px',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--color-bg-input)',
                  color: 'var(--color-text-primary)',
                  resize: 'vertical',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
                spellCheck={false}
                onClick={(e) => (e.target as HTMLTextAreaElement).select()}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', padding: '12px 20px', borderTop: '1px solid var(--color-border)' }}>
              <button className="btn btn-secondary" onClick={() => setLatexPreviewContent(null)} style={{ fontSize: '0.8125rem' }} disabled={exporting}>Cancel</button>
              <button className="btn btn-primary" onClick={handleLatexDownload} style={{ fontSize: '0.8125rem' }} disabled={exporting}>
                {exporting ? 'Downloading...' : 'Download .tex'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Toast Notification ── */}
      {toast && (
        <div
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            padding: '12px 20px',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.8125rem',
            fontWeight: 500,
            color: '#fff',
            background: toast.type === 'error' ? 'var(--color-error, #e74c3c)' : 'var(--color-success, #27ae60)',
            boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
            zIndex: 3000,
            animation: 'fadeIn 0.2s ease',
            maxWidth: '400px',
          }}
        >
          {toast.message}
        </div>
      )}
    </div>
  );
}


// ─── Mini Metric Chip ──────────────────────────────────────────────────────

function MetricChip({ label, value, helpText }: { label: string; value: string | number; helpText?: string }) {
  return (
    <div
      className="card"
      style={{
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '4px',
      }}
    >
      <span style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'inline-flex', alignItems: 'center' }}>
        {label}
        {helpText && <HelpTooltip text={helpText} />}
      </span>
      <span className="mono" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
        {value}
      </span>
    </div>
  );
}

// ─── Auto-Interpretation (Chinese NL) ─────────────────────────────────────

/** Domain-name to default Chinese display label. */
const DOMAIN_LABELS: Record<string, string> = {
  dissatisfaction: '不满程度',
  policy_demand: '政策需求',
  co_production: '合产参与',
  trust: '信任程度',
  gov_responsiveness: '政府响应',
};

/** Chinese numerals 0-10. */
const CN_NUMERALS = ['零', '一', '两', '三', '四', '五', '六', '七', '八', '九', '十'];

const SOLUTION_TYPE_CN: Record<string, string> = {
  complex: '复杂解',
  parsimonious: '精简解',
  intermediate: '中间解',
};

const SOLUTION_TYPE_DESC: Record<string, string> = {
  complex: '仅基于实际观察到的配置推导',
  parsimonious: '包含全部逻辑余项作为“不确定”行',
  intermediate: '仅包含理论上可能的反事实',
};

function guessLabel(cond: ConditionDefinition): string {
  return DOMAIN_LABELS[cond.domain] ?? cond.name.replace(/_/g, ' ');
}

function resolveDisplay(name: string, conditionSet: ConditionSet | null): string {
  if (conditionSet) {
    for (const c of conditionSet.conditions) {
      if (c.name === name) return c.display_name || guessLabel(c);
    }
    if (conditionSet.outcome?.name === name)
      return conditionSet.outcome.display_name || guessLabel(conditionSet.outcome);
  }
  return name.replace(/_/g, ' ');
}

function numToCN(n: number): string {
  if (n >= 0 && n < CN_NUMERALS.length) return CN_NUMERALS[n];
  return String(n);
}

function interpretCondition(cn: string, cs: ConditionSet | null): string {
  const negated = cn.startsWith('~');
  const clean = negated ? cn.slice(1) : cn;
  const display = resolveDisplay(clean, cs);
  return negated ? `低${display}` : `高${display}`;
}

function interpretTerm(term: SolutionTerm, cs: ConditionSet | null): string {
  if (term.term && term.term.length > 0) {
    return term.term.map((c) => interpretCondition(c, cs)).join(' 且 ');
  }
  if (term.label) {
    return term.label
      .split('*')
      .map((c) => interpretCondition(c.trim(), cs))
      .join(' 且 ');
  }
  return '未知条件组合';
}

function interpretConsistency(solution: QCASolution): string {
  const c = solution.solution_consistency;
  let quality: string;
  if (c >= 0.95) quality = '非常高';
  else if (c >= 0.9) quality = '很高';
  else if (c >= 0.8) quality = '较高';
  else if (c >= 0.75) quality = '可接受';
  else quality = '偏低';
  return (
    `解的一致性为${c.toFixed(3)}（${quality}），` +
    `表明这些条件组合是结果的充分条件——` +
    `即当这些条件组合出现时，结果几乎总是出现。`
  );
}

function interpretCoverage(solution: QCASolution): string {
  const c = solution.solution_coverage;
  const pct = c * 100;
  let quality: string;
  let detail: string;
  if (c >= 0.8) {
    quality = '很高';
    detail = `绝大部分（约${pct.toFixed(0)}%）`;
  } else if (c >= 0.6) {
    quality = '较高';
    detail = `超过一半（约${pct.toFixed(0)}%）`;
  } else if (c >= 0.4) {
    quality = '中等';
    detail = `约${pct.toFixed(0)}%`;
  } else {
    quality = '较低';
    detail = `仅约${pct.toFixed(0)}%`;
  }
  return (
    `解的覆盖度为${c.toFixed(3)}（${quality}），` +
    `表明这些路径解释了${detail}的结果案例。`
  );
}

function generateInterpretation(result: QCAAnalysisResultJSON): string {
  const cs = result.condition_set;
  const solutions = result.solutions;
  const primary = solutions.intermediate || solutions.complex || solutions.parsimonious;
  if (!primary || !primary.terms || primary.terms.length === 0) {
    return '未找到有效的解。';
  }

  const outcome =
    cs?.outcome?.display_name ||
    cs?.outcome?.name ||
    '结果';

  const lines: string[] = [];
  const nTerms = primary.terms.length;

  if (nTerms === 1) {
    lines.push(`导致“${outcome}”有一条主要路径：`);
  } else {
    lines.push(`导致“${outcome}”有${numToCN(nTerms)}条路径：`);
  }

  const pathLabels = ['一', '二', '三', '四', '五', '六'];
  for (let i = 0; i < primary.terms.length; i++) {
    const term = primary.terms[i];
    const idx = i < pathLabels.length ? pathLabels[i] : String(i + 1);
    const cnLabel = interpretTerm(term, cs);
    lines.push(`路径${idx}：${cnLabel}`);
  }

  const solTypeCN = SOLUTION_TYPE_CN[primary.solution_type] ?? primary.solution_type;
  lines.push('');
  lines.push(`（以上为${solTypeCN}）`);
  lines.push('');
  lines.push(interpretConsistency(primary));
  lines.push(interpretCoverage(primary));

  // Alternative solution types
  lines.push('');
  for (const st of ['complex', 'parsimonious', 'intermediate'] as const) {
    const sol = solutions[st] as QCASolution | null;
    const cnName = SOLUTION_TYPE_CN[st];
    const desc = SOLUTION_TYPE_DESC[st] ?? '';
    if (sol && sol.terms && sol.terms.length > 0) {
      if (st === primary.solution_type) {
        lines.push(`• ${cnName}（已展示于上方）：${desc}`);
      } else {
        lines.push(`• ${cnName}：${numToCN(sol.terms.length)}条路径，${desc}`);
        lines.push(`  公式：${sol.formula}`);
      }
    } else {
      lines.push(`• ${cnName}：未生成（不足够的一致配置）`);
      lines.push(`  ${desc}`);
    }
  }

  return lines.join('\n');
}

function generateNecessityInterpretation(
  necessity: NecessityResults,
  conditionSet: ConditionSet | null
): string {
  const outcome = necessity.outcome_name || '结果';
  if (!necessity.conditions || necessity.conditions.length === 0) {
    return `对于“${outcome}”，未找到必要条件分析结果。`;
  }

  const threshold = necessity.threshold;
  const necessary = necessity.conditions.filter((c) => c.is_necessary);
  const notNecessary = necessity.conditions.filter((c) => !c.is_necessary);

  const lines: string[] = [];
  lines.push(`必要条件分析（阈值 = ${threshold}）：`);

  if (necessary.length > 0) {
    lines.push(`其有${numToCN(necessary.length)}个条件是“${outcome}”的必要条件：`);
    for (const c of necessary) {
      const disp = resolveDisplay(c.condition_name, conditionSet);
      lines.push(`  • ${disp}：一致性${c.consistency.toFixed(3)}，覆盖度${c.coverage.toFixed(3)}`);
    }
    lines.push(
      `这意味着当“${outcome}”出现时，这些条件几乎总是存在（一致性≥${threshold}）。`
    );
  } else {
    lines.push(`没有条件达到必要性阈值（一致性 ≥ ${threshold}）。`);
    lines.push(`这表明没有单一条件是“${outcome}”的必要前提。`);
  }

  if (notNecessary.length > 0) {
    lines.push('');
    lines.push(`其他${numToCN(notNecessary.length)}个条件未达到必要性阈值：`);
    for (const c of notNecessary) {
      const disp = resolveDisplay(c.condition_name, conditionSet);
      lines.push(`  • ${disp}：一致性${c.consistency.toFixed(3)}`);
    }
  }

  return lines.join('\n');
}

function AutoInterpretation({ result }: { result: QCAAnalysisResultJSON }) {
  const [expanded, setExpanded] = useState(false);
  const t = useT();

  const interpretationText = useMemo(() => {
    if (!result) return '';
    return generateInterpretation(result);
  }, [result]);

  const necessityText = useMemo(() => {
    if (!result?.necessity) return '';
    return generateNecessityInterpretation(result.necessity, result.condition_set);
  }, [result]);

  if (!interpretationText && !necessityText) return null;

  return (
    <div className="card" style={{ padding: '16px', marginTop: '12px', borderColor: 'var(--color-accent)' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-accent)' }}>
          {t('results.autoInterpretation')}
        </h4>
        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
          {expanded ? t('results.collapse') : t('results.expand')}
        </span>
      </div>

      {expanded && (
        <div
          style={{
            marginTop: '12px',
            padding: '16px',
            background: 'var(--color-bg-primary)',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.875rem',
            lineHeight: '1.8',
            color: 'var(--color-text-primary)',
            whiteSpace: 'pre-wrap',
          }}
        >
          {interpretationText}

          {necessityText && (
            <>
              <div style={{ margin: '16px 0', borderTop: '1px solid var(--color-border)' }} />
              {necessityText}
            </>
          )}
        </div>
      )}
    </div>
  );
}
