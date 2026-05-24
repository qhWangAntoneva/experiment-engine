/**
 * Distribution histogram for fuzzy-set membership scores.
 *
 * Shows the distribution of membership values (0-1) across conditions,
 * helping users verify calibration quality.
 *
 * Data contract: { membership: number[][]; condition_names: string[] }
 */

import React, { useMemo, useState } from 'react';
import { PlotlyChart } from './FuzzySetHeatmap';
import type { MembershipDataJSON } from '../types/qca';

interface Props {
  fuzzyData: MembershipDataJSON;
  height?: number;
}

export default function DistributionPlot({ fuzzyData, height = 400 }: Props) {
  const [selectedCondition, setSelectedCondition] = useState<string>(
    fuzzyData.condition_names[0] || fuzzyData.outcome_name
  );

  const allNames = [...fuzzyData.condition_names, fuzzyData.outcome_name].filter(Boolean);

  const plotData = useMemo(() => {
    const colIdx = allNames.indexOf(selectedCondition);
    if (colIdx < 0 || colIdx >= fuzzyData.membership[0]?.length) return null;

    const values = fuzzyData.membership.map((row) => row[colIdx]);
    const nCases = values.length;
    const nBins = Math.max(8, Math.min(30, Math.floor(Math.sqrt(nCases))));

    return {
      data: [
        {
          x: values,
          type: 'histogram' as const,
          nbinsx: nBins,
          marker: {
            color: 'var(--color-accent, #2563eb)',
            line: { color: '#fff', width: 1 },
          },
          hovertemplate: 'Range: %{x}<br>Count: %{y}<extra></extra>',
        },
      ],
      layout: {
        title: `Membership Distribution: ${selectedCondition}`,
        height,
        xaxis: {
          title: 'Membership Score',
          range: [0, 1],
          dtick: 0.1,
        },
        yaxis: {
          title: 'Frequency',
        },
        font: {
          family: 'var(--font-mono), monospace',
          size: 11,
        },
        margin: { l: 60, r: 20, t: 40, b: 60 },
      },
      config: { responsive: true, displayModeBar: false },
    };
  }, [fuzzyData, selectedCondition, allNames, height]);

  return (
    <div>
      {/* Condition selector */}
      <div style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <label className="label" style={{ marginBottom: 0 }}>
          Condition:
        </label>
        <select
          className="input"
          value={selectedCondition}
          onChange={(e) => setSelectedCondition(e.target.value)}
          style={{ width: 220 }}
        >
          {allNames.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>

        {/* Summary stats */}
        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginLeft: 'auto' }}>
          {fuzzyData.membership.length} cases
        </span>
      </div>

      {plotData ? (
        <PlotlyChart data={plotData.data} layout={plotData.layout} config={plotData.config} />
      ) : (
        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
          No membership data to display.
        </div>
      )}
    </div>
  );
}
