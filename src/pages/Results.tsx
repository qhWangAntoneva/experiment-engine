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
import type { QCAAnalysisResultJSON } from '../types/qca';
import './Results.css';

type ViewMode = 'raw' | 'prototype' | 'compare';

export default function Results() {
  const { state } = useQCAPipeline();
  const { runExport } = useQCAWorkflow();
  const [activeTab, setActiveTab] = useState<'truth-table' | 'solutions' | 'necessity' | 'robustness'>('solutions');
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);
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
    { key: 'solutions' as const, label: 'Solutions', available: !!activeResult?.solutions },
    { key: 'truth-table' as const, label: 'Truth Table', available: !!activeResult?.truth_table },
    { key: 'necessity' as const, label: 'Necessity', available: !!activeResult?.necessity },
    { key: 'robustness' as const, label: 'Robustness', available: hasRobustness && viewMode !== 'prototype' },
  ];

  const handleExport = useCallback(
    async (format: 'csv' | 'json' | 'latex') => {
      setExporting(true);
      setExportMsg(null);
      try {
        const blob = await runExport(format);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `qca-analysis.${format === 'latex' ? 'tex' : format}`;
        a.click();
        URL.revokeObjectURL(url);
        setExportMsg(`Exported as ${format.toUpperCase()}`);
      } catch (err: any) {
        setExportMsg(`Export failed: ${err.message}`);
      } finally {
        setExporting(false);
      }
    },
    [runExport]
  );

  // ── Empty state ──────────────────────────────────────────────────────────
  if (!hasResults) {
    return (
      <div className="results">
        <div className="page-header">
          <h2 className="page-title">Results</h2>
          <p className="page-subtitle">QCA analysis output and visualizations</p>
        </div>
        <PipelineStatus />
        <div className="results-empty">
          <p style={{ fontSize: '0.875rem', marginBottom: '8px' }}>No analysis results yet.</p>
          <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
            Go to Data Input to upload texts and run the QCA pipeline.
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
        <h2 className="page-title">Results</h2>
        <p className="page-subtitle">QCA analysis output and visualizations</p>
      </div>

      <PipelineStatus />

      {/* ── View Mode Toggle (only when prototype results exist) ── */}
      {showViewToggle && (
        <div className="view-mode-toggle">
          <button
            className={`view-mode-btn ${viewMode === 'raw' ? 'active' : ''}`}
            onClick={() => setViewMode('raw')}
          >
            Raw Text
          </button>
          <button
            className={`view-mode-btn ${viewMode === 'prototype' ? 'active' : ''}`}
            onClick={() => setViewMode('prototype')}
          >
            Prototype
          </button>
          <button
            className={`view-mode-btn ${viewMode === 'compare' ? 'active' : ''}`}
            onClick={() => setViewMode('compare')}
          >
            Compare
          </button>
        </div>
      )}

      {/* ── Comparison Summary (compare mode only) ── */}
      {viewMode === 'compare' && analysisResult && prototypeAnalysisResult && (
        <ComparisonSummary raw={analysisResult} prototype={prototypeAnalysisResult} />
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
            Export CSV
          </button>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8125rem' }}
            onClick={() => handleExport('json')}
            disabled={exporting}
          >
            Export JSON
          </button>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8125rem' }}
            onClick={() => handleExport('latex')}
            disabled={exporting}
          >
            Export LaTeX
          </button>
          {exportMsg && (
            <span
              style={{
                fontSize: '0.75rem',
                color: exportMsg.includes('fail') ? 'var(--color-error)' : 'var(--color-success)',
                alignSelf: 'center',
              }}
            >
              {exportMsg}
            </span>
          )}
        </div>
      </div>

      {/* ── Compare Mode: Side-by-side ── */}
      {viewMode === 'compare' && analysisResult && prototypeAnalysisResult ? (
        <CompareView
          raw={analysisResult}
          prototype={prototypeAnalysisResult}
        />
      ) : (
        <>
          {/* Summary Stats */}
          {activeResult && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '20px' }}>
              <MetricChip label="Cases" value={summaryFuzzyData?.membership?.length ?? 0} />
              <MetricChip label="Conditions" value={summaryFuzzyData?.condition_names?.length ?? 0} />
              <MetricChip
                label="Consistency"
                value={activeResult.solutions?.complex?.solution_consistency?.toFixed(3) ?? '-'}
              />
              <MetricChip
                label="Coverage"
                value={activeResult.solutions?.complex?.solution_coverage?.toFixed(3) ?? '-'}
              />
              <MetricChip
                label="Robustness"
                value={robustnessReport ? robustnessReport.overall_robustness.toFixed(2) : 'N/A'}
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
              <div className="card" style={{ padding: '16px' }}>
                <SolutionViewer solutions={activeResult.solutions} showAll={true} />
              </div>
            )}

            {activeTab === 'necessity' && activeResult?.necessity && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="card" style={{ padding: '16px' }}>
                  <NecessityXYPlot necessity={activeResult.necessity} height={400} />
                </div>
                <div className="card" style={{ padding: '16px' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '12px' }}>
                    Necessity Analysis (threshold = {activeResult.necessity.threshold})
                  </h4>
                  <div className="table-container">
                    <table style={{ fontSize: '0.8125rem' }}>
                      <thead>
                        <tr>
                          <th>Condition</th>
                          <th>Consistency</th>
                          <th>Coverage</th>
                          <th>Necessary?</th>
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
                                <span className="badge badge-success">Yes</span>
                              ) : (
                                <span className="badge badge-error">No</span>
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
                    Robustness Report
                  </h4>
                  <span className={`badge ${robustnessReport.overall_robustness >= 0.8 ? 'badge-success' : 'badge-warning'}`}>
                    Overall: {robustnessReport.overall_robustness.toFixed(2)}
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
                          Varying: {test.parameter_varied}
                        </p>
                      </div>
                      <span className={`badge ${test.passed ? 'badge-success' : 'badge-warning'}`}>
                        {test.passed ? 'PASSED' : 'UNSTABLE'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '0.75rem' }}>
                      <span className="mono" style={{ color: 'var(--color-text-secondary)' }}>
                        Stability: {test.solution_stability.map((s) => s.toFixed(2)).join(', ')}
                      </span>
                      <span className="mono" style={{ color: 'var(--color-text-secondary)' }}>
                        Params: {test.parameter_values.map((v) => v.toFixed(2)).join(', ')}
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
}: {
  raw: QCAAnalysisResultJSON;
  prototype: QCAAnalysisResultJSON;
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
        Raw Text vs Prototype Comparison
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px' }}>
        <ComparisonMetricChip
          label="Consistency"
          rawValue={rawConsistency.toFixed(3)}
          protoValue={protoConsistency.toFixed(3)}
          delta={consistencyDelta}
        />
        <ComparisonMetricChip
          label="Coverage"
          rawValue={rawCoverage.toFixed(3)}
          protoValue={protoCoverage.toFixed(3)}
          delta={coverageDelta}
        />
        <ComparisonMetricChip
          label="Formula Match"
          rawValue={formulasDiffer ? 'Different' : 'Same'}
          protoValue=""
          delta={0}
          highlight={formulasDiffer}
        />
        <ComparisonMetricChip
          label="Necessary Cond."
          rawValue={String(rawNecessary)}
          protoValue={String(protoNecessary)}
          delta={protoNecessary - rawNecessary}
        />
        <ComparisonMetricChip
          label="Truth Table Rows"
          rawValue={String(rawRows)}
          protoValue={String(protoRows)}
          delta={protoRows - rawRows}
        />
      </div>
      {formulasDiffer && (
        <div style={{ marginTop: '12px', padding: '12px', background: 'var(--color-bg-primary)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, marginBottom: '6px', color: 'var(--color-text-secondary)' }}>
            Solution Formula Comparison
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.8125rem' }}>
            <div>
              <span style={{ color: 'var(--color-text-secondary)' }}>Raw: </span>
              <span className="mono" style={{ fontWeight: 600 }}>{rawFormula || '(none)'}</span>
            </div>
            <div>
              <span style={{ color: 'var(--color-text-secondary)' }}>Prototype: </span>
              <span className="mono" style={{ fontWeight: 600 }}>{protoFormula || '(none)'}</span>
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
}: {
  raw: QCAAnalysisResultJSON;
  prototype: QCAAnalysisResultJSON;
}) {
  const [compareTab, setCompareTab] = useState<'solutions' | 'truth-table' | 'necessity'>('solutions');

  const hasSolutions = !!(raw.solutions && prototype.solutions);
  const hasTruthTable = !!(raw.truth_table && prototype.truth_table);
  const hasNecessity = !!(raw.necessity && prototype.necessity);

  const compareTabs = [
    { key: 'solutions' as const, label: 'Solutions', available: hasSolutions },
    { key: 'truth-table' as const, label: 'Truth Table', available: hasTruthTable },
    { key: 'necessity' as const, label: 'Necessity', available: hasNecessity },
  ];

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
            <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '8px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Raw Text Solutions
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <SolutionViewer solutions={raw.solutions} showAll={true} />
            </div>
          </div>
          <div>
            <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '8px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Prototype Solutions
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
            <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '8px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Raw Truth Table
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <TruthTableViewer truthTable={raw.truth_table} />
            </div>
            <div className="card" style={{ padding: '16px', marginTop: '16px' }}>
              <FuzzySetHeatmap truthTable={raw.truth_table} height={300} />
            </div>
          </div>
          <div>
            <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '8px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Prototype Truth Table
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
            <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '8px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Raw Necessity
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <NecessityXYPlot necessity={raw.necessity} height={350} />
            </div>
            <div className="card" style={{ padding: '16px', marginTop: '16px' }}>
              <NecessityTable necessity={raw.necessity} highlight={prototype.necessity} />
            </div>
          </div>
          <div>
            <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '8px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Prototype Necessity
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <NecessityXYPlot necessity={prototype.necessity} height={350} />
            </div>
            <div className="card" style={{ padding: '16px', marginTop: '16px' }}>
              <NecessityTable necessity={prototype.necessity} highlight={raw.necessity} />
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ─── Necessity Table (reusable for individual + compare views) ─────────────

function NecessityTable({ necessity, highlight }: { necessity: any; highlight?: any }) {
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
            <th>Condition</th>
            <th>Consistency</th>
            <th>Coverage</th>
            <th>Necessary?</th>
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
                      differs
                    </span>
                  )}
                </td>
                <td className="mono">{c.consistency.toFixed(3)}</td>
                <td className="mono">{c.coverage.toFixed(3)}</td>
                <td>
                  {c.is_necessary ? (
                    <span className="badge badge-success">Yes</span>
                  ) : (
                    <span className="badge badge-error">No</span>
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
}: {
  label: string;
  rawValue: string;
  protoValue: string;
  delta: number;
  highlight?: boolean;
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
        <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.65rem' }}>vs</span>
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
