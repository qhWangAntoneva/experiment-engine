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
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { useQCAWorkflow } from '../hooks/useQCAWorkflow';
import { useT } from '../i18n/I18nContext';
import type {
  QCAAnalysisResultJSON,
  ConditionSet,
  ConditionDefinition,
  SolutionTerm,
  QCASolution,
  NecessityResults,
} from '../types/qca';
import './Results.css';

type ViewMode = 'raw' | 'prototype' | 'compare';

export default function Results() {
  const t = useT();
  const { state } = useQCAPipeline();
  const { runExport } = useQCAWorkflow();
  const [activeTab, setActiveTab] = useState<'truth-table' | 'solutions' | 'necessity' | 'robustness'>('solutions');
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('raw');

  const hasResults = !!state.analysisResult;
  const hasPrototypeResults = !!state.prototypeAnalysisResult;
  const hasRobustness = !!state.robustnessReport;

  // Derive active data based on view mode
  const activeResult: QCAAnalysisResultJSON | null = useMemo(() => {
    if (viewMode === 'prototype') return state.prototypeAnalysisResult;
    return state.analysisResult;
  }, [viewMode, state.analysisResult, state.prototypeAnalysisResult]);

  const tabs = [
    { key: 'solutions' as const, label: t('results.tabSolutions'), available: !!activeResult?.solutions },
    { key: 'truth-table' as const, label: t('results.tabTruthTable'), available: !!activeResult?.truth_table },
    { key: 'necessity' as const, label: t('results.tabNecessity'), available: !!activeResult?.necessity },
    { key: 'robustness' as const, label: t('results.tabRobustness'), available: hasRobustness && viewMode !== 'prototype' },
  ];

  const handleExport = useCallback(
    async (format: 'csv' | 'json' | 'latex') => {
      setExporting(true);
      setExportError(null);
      setExportSuccess(null);
      try {
        const blob = await runExport(format);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `qca-analysis.${format === 'latex' ? 'tex' : format}`;
        a.click();
        URL.revokeObjectURL(url);
        setExportSuccess(t('results.exportedAs', format.toUpperCase()));
      } catch (err: any) {
        setExportError(t('results.exportFailed') + err.message);
      } finally {
        setExporting(false);
      }
    },
    [runExport, t]
  );

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
              />
              <MetricChip
                label={t('results.coverage')}
                value={activeResult.solutions?.complex?.solution_coverage?.toFixed(3) ?? '-'}
              />
              <MetricChip
                label={t('results.robustness')}
                value={robustnessReport ? robustnessReport.overall_robustness.toFixed(2) : t('results.nA')}
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
    </div>
  );
}

// ─── Comparison Summary ─────────────────────────────────────────────────────

function ComparisonSummary({
  raw,
  prototype,
  t,
}: {
  raw: QCAAnalysisResultJSON;
  prototype: QCAAnalysisResultJSON;
  t: (path: string) => string;
}) {
  const rawConsistency = raw.solutions?.complex?.solution_consistency ?? 0;
  const protoConsistency = prototype.solutions?.complex?.solution_consistency ?? 0;
  const rawCoverage = raw.solutions?.complex?.solution_coverage ?? 0;
  const protoCoverage = prototype.solutions?.complex?.solution_coverage ?? 0;

  const rawFormula = raw.solutions?.complex?.formula ?? '';
  const protoFormula = prototype.solutions?.complex?.formula ?? '';
  const formulasDiffer = rawFormula !== protoFormula;

  const consistencyDelta = protoConsistency - rawConsistency;
  const coverageDelta = protoCoverage - rawCoverage;

  // Count necessity differences
  const rawNecessary = raw.necessity?.conditions.filter((c) => c.is_necessary).length ?? 0;
  const protoNecessary = prototype.necessity?.conditions.filter((c) => c.is_necessary).length ?? 0;

  // Count truth table row differences
  const rawRows = raw.truth_table?.rows.length ?? 0;
  const protoRows = prototype.truth_table?.rows.length ?? 0;

  return (
    <div className="comparison-summary">
      <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '12px' }}>
        {t('results.comparisonTitle')}
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px' }}>
        <ComparisonMetricChip
          label={t('results.consistencyCmp')}
          rawValue={rawConsistency.toFixed(3)}
          protoValue={protoConsistency.toFixed(3)}
          delta={consistencyDelta}
          t={t}
        />
        <ComparisonMetricChip
          label={t('results.coverageCmp')}
          rawValue={rawCoverage.toFixed(3)}
          protoValue={protoCoverage.toFixed(3)}
          delta={coverageDelta}
          t={t}
        />
        <ComparisonMetricChip
          label={t('results.formulaMatchCmp')}
          rawValue={formulasDiffer ? t('common.different') : t('common.same')}
          protoValue=""
          delta={0}
          highlight={formulasDiffer}
          t={t}
        />
        <ComparisonMetricChip
          label={t('results.necessaryCondCmp')}
          rawValue={String(rawNecessary)}
          protoValue={String(protoNecessary)}
          delta={protoNecessary - rawNecessary}
          t={t}
        />
        <ComparisonMetricChip
          label={t('results.truthTableRowsCmp')}
          rawValue={String(rawRows)}
          protoValue={String(protoRows)}
          delta={protoRows - rawRows}
          t={t}
        />
      </div>
      {formulasDiffer && (
        <div style={{ marginTop: '12px', padding: '12px', background: 'var(--color-bg-primary)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, marginBottom: '6px', color: 'var(--color-text-secondary)' }}>
            {t('results.solutionFormulaComparison')}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.8125rem' }}>
            <div>
              <span style={{ color: 'var(--color-text-secondary)' }}>{t('results.raw')}: </span>
              <span className="mono" style={{ fontWeight: 600 }}>{rawFormula || `(${t('common.none')})`}</span>
            </div>
            <div>
              <span style={{ color: 'var(--color-text-secondary)' }}>{t('results.prototype')}: </span>
              <span className="mono" style={{ fontWeight: 600 }}>{protoFormula || `(${t('common.none')})`}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Side-by-side Compare View ──────────────────────────────────────────────

function CompareView({
  raw,
  prototype,
  t,
}: {
  raw: QCAAnalysisResultJSON;
  prototype: QCAAnalysisResultJSON;
  t: (path: string) => string;
}) {
  const [compareTab, setCompareTab] = useState<'solutions' | 'truth-table' | 'necessity'>('solutions');

  const hasSolutions = !!(raw.solutions && prototype.solutions);
  const hasTruthTable = !!(raw.truth_table && prototype.truth_table);
  const hasNecessity = !!(raw.necessity && prototype.necessity);

  const compareTabs = [
    { key: 'solutions' as const, label: t('results.tabSolutions'), available: hasSolutions },
    { key: 'truth-table' as const, label: t('results.tabTruthTable'), available: hasTruthTable },
    { key: 'necessity' as const, label: t('results.tabNecessity'), available: hasNecessity },
  ];

  const headingStyle: React.CSSProperties = {
    fontSize: '0.8125rem',
    fontWeight: 600,
    marginBottom: '8px',
    color: 'var(--color-text-secondary)',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  };

  return (
    <>
      {/* Compare Tabs */}
      <div style={{ display: 'flex', gap: '2px', marginBottom: '16px', borderBottom: '1px solid var(--color-border)' }}>
        {compareTabs
          .filter((t) => t.available)
          .map((tab) => (
            <button
              key={tab.key}
              className={compareTab === tab.key ? 'btn btn-primary' : 'btn btn-secondary'}
              onClick={() => setCompareTab(tab.key)}
              style={{
                borderBottomLeftRadius: 0,
                borderBottomRightRadius: 0,
                borderBottom: compareTab === tab.key ? '2px solid var(--color-accent)' : 'none',
                fontSize: '0.8125rem',
              }}
            >
              {tab.label}
            </button>
          ))}
      </div>

      {/* Solutions comparison */}
      {compareTab === 'solutions' && raw.solutions && prototype.solutions && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <h4 style={headingStyle}>
              {t('results.rawTextSolutions')}
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <SolutionViewer solutions={raw.solutions} showAll={true} />
            </div>
          </div>
          <div>
            <h4 style={headingStyle}>
              {t('results.protoSolutions')}
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <SolutionViewer solutions={prototype.solutions} showAll={true} />
            </div>
          </div>
        </div>
      )}

      {/* Truth Table comparison */}
      {compareTab === 'truth-table' && raw.truth_table && prototype.truth_table && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <h4 style={headingStyle}>
              {t('results.rawTruthTable')}
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <TruthTableViewer truthTable={raw.truth_table} />
            </div>
            <div className="card" style={{ padding: '16px', marginTop: '16px' }}>
              <FuzzySetHeatmap truthTable={raw.truth_table} height={300} />
            </div>
          </div>
          <div>
            <h4 style={headingStyle}>
              {t('results.protoTruthTable')}
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <TruthTableViewer truthTable={prototype.truth_table} />
            </div>
            <div className="card" style={{ padding: '16px', marginTop: '16px' }}>
              <FuzzySetHeatmap truthTable={prototype.truth_table} height={300} />
            </div>
          </div>
        </div>
      )}

      {/* Necessity comparison */}
      {compareTab === 'necessity' && raw.necessity && prototype.necessity && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <h4 style={headingStyle}>
              {t('results.rawNecessity')}
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <NecessityXYPlot necessity={raw.necessity} height={350} />
            </div>
            <div className="card" style={{ padding: '16px', marginTop: '16px' }}>
              <NecessityTable necessity={raw.necessity} highlight={prototype.necessity} t={t} />
            </div>
          </div>
          <div>
            <h4 style={headingStyle}>
              {t('results.protoNecessity')}
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <NecessityXYPlot necessity={prototype.necessity} height={350} />
            </div>
            <div className="card" style={{ padding: '16px', marginTop: '16px' }}>
              <NecessityTable necessity={prototype.necessity} highlight={raw.necessity} t={t} />
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ─── Necessity Table (reusable for individual + compare views) ─────────────

function NecessityTable({ necessity, highlight, t }: { necessity: any; highlight?: any; t: (path: string) => string }) {
  // Build a map of condition -> is_necessary from highlight source
  const highlightMap: Record<string, boolean> = {};
  if (highlight) {
    for (const c of highlight.conditions) {
      highlightMap[c.condition_name] = c.is_necessary;
    }
  }

  return (
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
          {necessity.conditions.map((c: any, idx: number) => {
            const otherNecessary = highlightMap[c.condition_name];
            const differs = otherNecessary !== undefined && otherNecessary !== c.is_necessary;
            return (
              <tr
                key={idx}
                style={{
                  background: c.is_necessary ? 'rgba(5, 150, 105, 0.05)' : undefined,
                  outline: differs ? '1px solid var(--color-warning)' : undefined,
                }}
              >
                <td style={{ fontWeight: 600 }}>
                  {c.condition_name}
                  {differs && (
                    <span style={{ fontSize: '0.65rem', color: 'var(--color-warning)', marginLeft: '4px' }}>
                      {t('common.differs')}
                    </span>
                  )}
                </td>
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
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── Comparison Metric Chip ─────────────────────────────────────────────────

function ComparisonMetricChip({
  label,
  rawValue,
  protoValue,
  delta,
  highlight = false,
  t,
}: {
  label: string;
  rawValue: string;
  protoValue: string;
  delta: number;
  highlight?: boolean;
  t: (path: string) => string;
}) {
  const deltaStr = delta > 0 ? `+${delta.toFixed(3)}` : delta.toFixed(3);
  const deltaColor = delta === 0
    ? 'var(--color-text-secondary)'
    : delta > 0
      ? 'var(--color-success)'
      : 'var(--color-error)';

  return (
    <div
      className="card"
      style={{
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '4px',
        borderColor: highlight ? 'var(--color-warning)' : undefined,
      }}
    >
      <span style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </span>
      <div style={{ display: 'flex', gap: '6px', alignItems: 'baseline', fontSize: '0.75rem' }}>
        <span className="mono" style={{ fontWeight: 600, color: 'var(--color-accent)' }}>
          {rawValue}
        </span>
        <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.65rem' }}>{t('common.vs')}</span>
        <span className="mono" style={{ fontWeight: 600, color: 'var(--color-accent-secondary, var(--color-accent))' }}>
          {protoValue || '-'}
        </span>
      </div>
      {delta !== 0 && (
        <span className="mono" style={{ fontSize: '0.7rem', color: deltaColor }}>
          {deltaStr}
        </span>
      )}
    </div>
  );
}

// ─── Mini Metric Chip ──────────────────────────────────────────────────────

function MetricChip({ label, value }: { label: string; value: string | number }) {
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
      <span style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
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
    return term.term.map((c) => interpretCondition(c, cs)).join(' AND ');
  }
  if (term.label) {
    return term.label
      .split('*')
      .map((c) => interpretCondition(c.trim(), cs))
      .join(' AND ');
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
