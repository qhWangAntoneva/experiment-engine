/**
 * ParamDiffTable (P1-7)
 *
 * Displays parameter differences between two ParameterSnapshots in a table.
 * Groups: calibration, analysis, variant
 * Rows that differ are highlighted with yellow background and left border accent.
 */

import React from 'react';
import type { ParamDiffEntry, ParameterSnapshot } from '../types/qca';

interface ParamDiffTableProps {
  snapshotA: ParameterSnapshot;
  snapshotB: ParameterSnapshot;
}

/** Compute parameter difference entries between two snapshots. */
export function computeParamDiffs(a: ParameterSnapshot, b: ParameterSnapshot): ParamDiffEntry[] {
  const diffs: ParamDiffEntry[] = [];

  // ── Calibration group ──
  const csA = a.conditionSet;
  const csB = b.conditionSet;
  const condNamesA = csA.conditions.map((c) => c.name);
  const condNamesB = csB.conditions.map((c) => c.name);

  // Condition count
  diffs.push({
    paramName: 'Number of conditions',
    group: 'calibration' as const,
    valueA: condNamesA.length,
    valueB: condNamesB.length,
    differs: condNamesA.length !== condNamesB.length,
  });

  // Condition names
  diffs.push({
    paramName: 'Condition names',
    group: 'calibration' as const,
    valueA: condNamesA.join(', ') || '(none)',
    valueB: condNamesB.join(', ') || '(none)',
    differs: condNamesA.join(',') !== condNamesB.join(','),
  });

  // Outcome name
  const outcomeA = csA.outcome?.display_name || csA.outcome?.name || '(none)';
  const outcomeB = csB.outcome?.display_name || csB.outcome?.name || '(none)';
  diffs.push({
    paramName: 'Outcome',
    group: 'calibration' as const,
    valueA: outcomeA,
    valueB: outcomeB,
    differs: outcomeA !== outcomeB,
  });

  // Per-condition calibration params
  for (const condA of csA.conditions) {
    const condB = csB.conditions.find((c) => c.name === condA.name);
    const calMethodA = condA.calibration_type;
    const calMethodB = condB?.calibration_type ?? '(missing)';
    diffs.push({
      paramName: `${condA.display_name || condA.name}: Calibration method`,
      group: 'calibration' as const,
      valueA: calMethodA,
      valueB: calMethodB,
      differs: calMethodA !== calMethodB,
    });
  }

  // ── Analysis group ──
  const paramsA = a.analysisParams;
  const paramsB = b.analysisParams;

  diffs.push({
    paramName: 'Consistency threshold',
    group: 'analysis' as const,
    valueA: paramsA.consistency_threshold,
    valueB: paramsB.consistency_threshold,
    differs: paramsA.consistency_threshold !== paramsB.consistency_threshold,
  });

  diffs.push({
    paramName: 'Frequency threshold',
    group: 'analysis' as const,
    valueA: paramsA.frequency_threshold,
    valueB: paramsB.frequency_threshold,
    differs: paramsA.frequency_threshold !== paramsB.frequency_threshold,
  });

  diffs.push({
    paramName: 'Necessity threshold',
    group: 'analysis' as const,
    valueA: paramsA.necessity_threshold,
    valueB: paramsB.necessity_threshold,
    differs: paramsA.necessity_threshold !== paramsB.necessity_threshold,
  });

  diffs.push({
    paramName: 'N-Cut',
    group: 'analysis' as const,
    valueA: paramsA.n_cut,
    valueB: paramsB.n_cut,
    differs: paramsA.n_cut !== paramsB.n_cut,
  });

  // Case count
  const casesA = a.result.fuzzy_data?.membership?.length ?? 0;
  const casesB = b.result.fuzzy_data?.membership?.length ?? 0;
  diffs.push({
    paramName: 'Case count',
    group: 'analysis' as const,
    valueA: casesA,
    valueB: casesB,
    differs: casesA !== casesB,
  });

  // ── Variant group ──
  const qcaVarA = csA.qca_variant ?? 'fsqca';
  const qcaVarB = csB.qca_variant ?? 'fsqca';
  diffs.push({
    paramName: 'QCA Variant',
    group: 'variant' as const,
    valueA: qcaVarA,
    valueB: qcaVarB,
    differs: qcaVarA !== qcaVarB,
  });

  const scoringA = csA.scoring_source ?? 'prototype';
  const scoringB = csB.scoring_source ?? 'prototype';
  diffs.push({
    paramName: 'Scoring source',
    group: 'variant' as const,
    valueA: scoringA,
    valueB: scoringB,
    differs: scoringA !== scoringB,
  });

  return diffs;
}

const GROUP_LABELS: Record<ParamDiffEntry['group'], string> = {
  calibration: 'Calibration',
  analysis: 'Analysis',
  variant: 'Variant',
};

export default function ParamDiffTable({ snapshotA, snapshotB }: ParamDiffTableProps) {
  const diffs = React.useMemo(
    () => computeParamDiffs(snapshotA, snapshotB),
    [snapshotA, snapshotB]
  );

  if (diffs.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        No parameters to compare.
      </div>
    );
  }

  // Group diffs
  const groups: Record<string, ParamDiffEntry[]> = {};
  for (const d of diffs) {
    if (!groups[d.group]) groups[d.group] = [];
    groups[d.group].push(d);
  }

  return (
    <div>
      {(['calibration', 'analysis', 'variant'] as const).map((groupKey) => {
        const entries = groups[groupKey];
        if (!entries || entries.length === 0) return null;
        return (
          <div key={groupKey} style={{ marginBottom: '20px' }}>
            <h4
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--color-text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                marginBottom: '8px',
              }}
            >
              {GROUP_LABELS[groupKey]}
            </h4>
            <div className="table-container">
              <table style={{ fontSize: '0.8125rem', width: '100%' }}>
                <thead>
                  <tr>
                    <th style={{ width: '35%' }}>Parameter</th>
                    <th style={{ width: '25%' }}>Value A</th>
                    <th style={{ width: '25%' }}>Value B</th>
                    <th style={{ width: '15%', textAlign: 'center' }}>Match</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry, idx) => (
                    <tr
                      key={`${groupKey}-${idx}`}
                      style={{
                        background: entry.differs
                          ? 'rgba(251, 191, 36, 0.08)'
                          : undefined,
                        borderLeft: entry.differs
                          ? '3px solid var(--color-warning)'
                          : '3px solid transparent',
                      }}
                    >
                      <td style={{ fontWeight: 500 }}>{entry.paramName}</td>
                      <td className="mono">{String(entry.valueA)}</td>
                      <td className="mono">{String(entry.valueB)}</td>
                      <td style={{ textAlign: 'center' }}>
                        {entry.differs ? (
                          <span
                            style={{
                              display: 'inline-block',
                              padding: '2px 8px',
                              borderRadius: 'var(--radius-sm, 4px)',
                              fontSize: '0.7rem',
                              fontWeight: 600,
                              background: 'var(--color-warning)',
                              color: '#000',
                            }}
                          >
                            !
                          </span>
                        ) : (
                          <span
                            style={{
                              display: 'inline-block',
                              padding: '2px 8px',
                              borderRadius: 'var(--radius-sm, 4px)',
                              fontSize: '0.7rem',
                              fontWeight: 600,
                              background: 'var(--color-success)',
                              color: '#fff',
                            }}
                          >
                            v
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}
