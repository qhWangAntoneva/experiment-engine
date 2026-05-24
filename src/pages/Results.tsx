/**
 * Results — displays all QCA analysis output in organized sections:
 *   1. Truth Table (sortable table + heatmap)
 *   2. Solutions (complex/parsimonious/intermediate)
 *   3. Necessity / Sufficiency
 *   4. Robustness (if run)
 *   5. Export buttons
 */

import React, { useState, useCallback } from 'react';
import PipelineStatus from '../components/PipelineStatus';
import TruthTableViewer from '../components/TruthTableViewer';
import SolutionViewer from '../components/SolutionViewer';
import FuzzySetHeatmap from '../components/FuzzySetHeatmap';
import NecessityXYPlot from '../components/NecessityXYPlot';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { useQCAWorkflow } from '../hooks/useQCAWorkflow';
import './Results.css';

export default function Results() {
  const { state } = useQCAPipeline();
  const { runExport } = useQCAWorkflow();
  const [activeTab, setActiveTab] = useState<'truth-table' | 'solutions' | 'necessity' | 'robustness'>('solutions');
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);

  const hasResults = !!state.analysisResult;
  const hasRobustness = !!state.robustnessReport;

  const tabs = [
    { key: 'solutions' as const, label: 'Solutions', available: !!state.analysisResult?.solutions },
    { key: 'truth-table' as const, label: 'Truth Table', available: !!state.analysisResult?.truth_table },
    { key: 'necessity' as const, label: 'Necessity', available: !!state.analysisResult?.necessity },
    { key: 'robustness' as const, label: 'Robustness', available: hasRobustness },
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

  // Empty state
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

  const { analysisResult, fuzzyData, robustnessReport } = state;

  return (
    <div className="results">
      <div className="page-header">
        <h2 className="page-title">Results</h2>
        <p className="page-subtitle">QCA analysis output and visualizations</p>
      </div>

      <PipelineStatus />

      {/* Toolbar */}
      <div className="results-toolbar">
        <div className="toolbar-left" style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary" style={{ fontSize: '0.8125rem' }}>
            Refresh
          </button>
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

      {/* Summary Stats */}
      {analysisResult && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '20px' }}>
          <MetricChip label="Cases" value={fuzzyData?.membership?.length ?? 0} />
          <MetricChip label="Conditions" value={fuzzyData?.condition_names?.length ?? 0} />
          <MetricChip
            label="Consistency"
            value={analysisResult.solutions?.complex?.solution_consistency?.toFixed(3) ?? '-'}
          />
          <MetricChip
            label="Coverage"
            value={analysisResult.solutions?.complex?.solution_coverage?.toFixed(3) ?? '-'}
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
        {activeTab === 'truth-table' && analysisResult?.truth_table && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
            <div className="card" style={{ padding: '16px' }}>
              <TruthTableViewer truthTable={analysisResult.truth_table} />
            </div>
            <div className="card" style={{ padding: '16px' }}>
              <FuzzySetHeatmap truthTable={analysisResult.truth_table} height={350} />
            </div>
          </div>
        )}

        {activeTab === 'solutions' && analysisResult?.solutions && (
          <div className="card" style={{ padding: '16px' }}>
            <SolutionViewer solutions={analysisResult.solutions} showAll={true} />
          </div>
        )}

        {activeTab === 'necessity' && analysisResult?.necessity && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="card" style={{ padding: '16px' }}>
              <NecessityXYPlot necessity={analysisResult.necessity} height={400} />
            </div>
            <div className="card" style={{ padding: '16px' }}>
              <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '12px' }}>
                Necessity Analysis (threshold = {analysisResult.necessity.threshold})
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
                    {analysisResult.necessity.conditions.map((c, idx) => (
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
