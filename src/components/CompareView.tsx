/**
 * CompareView — shared comparison components for side-by-side QCA result comparison.
 *
 * Used by both Results.tsx (raw-vs-prototype compare mode) and Compare.tsx (P1-7 A/B analysis).
 *
 * Exports:
 *   CompareView     — side-by-side solutions / truth table / necessity comparison
 *   NecessityTable   — necessity analysis table with optional highlighting
 *   ComparisonMetricChip — metric chip with raw/proto values and delta
 *   ComparisonSummary — 5-column summary grid for two QCAAnalysisResultJSON objects
 */

import React, { useState } from 'react';
import TruthTableViewer from './TruthTableViewer';
import SolutionViewer from './SolutionViewer';
import FuzzySetHeatmap from './FuzzySetHeatmap';
import NecessityXYPlot from './NecessityXYPlot';
import type {
  QCAAnalysisResultJSON,
} from '../types/qca';

/** Heading style shared across compare views. */
export const COMPARE_HEADING_STYLE: React.CSSProperties = {
  fontSize: '0.8125rem',
  fontWeight: 600,
  marginBottom: '8px',
  color: 'var(--color-text-secondary)',
  textTransform: 'uppercase' as const,
  letterSpacing: '0.04em',
};

// ─── CompareView ──────────────────────────────────────────────────────────────

export function CompareView({
  raw,
  prototype,
  t,
}: {
  raw: QCAAnalysisResultJSON;
  prototype: QCAAnalysisResultJSON;
  t: (path: string, ...args: any[]) => string;
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
            <h4 style={COMPARE_HEADING_STYLE}>
              {t('results.rawTextSolutions')}
            </h4>
            <div className="card" style={{ padding: '16px' }}>
              <SolutionViewer solutions={raw.solutions} showAll={true} />
            </div>
          </div>
          <div>
            <h4 style={COMPARE_HEADING_STYLE}>
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
            <h4 style={COMPARE_HEADING_STYLE}>
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
            <h4 style={COMPARE_HEADING_STYLE}>
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
            <h4 style={COMPARE_HEADING_STYLE}>
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
            <h4 style={COMPARE_HEADING_STYLE}>
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

// ─── NecessityTable ───────────────────────────────────────────────────────────

export function NecessityTable({
  necessity,
  highlight,
  t,
}: {
  necessity: any;
  highlight?: any;
  t: (path: string, ...args: any[]) => string;
}) {
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

// ─── ComparisonMetricChip ─────────────────────────────────────────────────────

export function ComparisonMetricChip({
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
  t: (path: string, ...args: any[]) => string;
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

// ─── ComparisonSummary ────────────────────────────────────────────────────────

export function ComparisonSummary({
  raw,
  prototype,
  t,
}: {
  raw: QCAAnalysisResultJSON;
  prototype: QCAAnalysisResultJSON;
  t: (path: string, ...args: any[]) => string;
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
