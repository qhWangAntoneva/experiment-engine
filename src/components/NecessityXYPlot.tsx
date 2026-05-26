/**
 * Necessity/Consistency XY scatter plot.
 *
 * X-axis: Necessity Consistency (condition >= outcome)
 * Y-axis: Necessity Coverage
 * Each point = one condition. Reference lines for threshold (default 0.9).
 *
 * Data contract: { conditions: { name, consistency, coverage, is_necessary }[] }
 */

import React, { useMemo } from 'react';
import { PlotlyChart } from './FuzzySetHeatmap';
import type { NecessityResults } from '../types/qca';

interface Props {
  necessity: NecessityResults;
  height?: number;
}

export default function NecessityXYPlot({ necessity, height = 400 }: Props) {
  const plotData = useMemo(() => {
    const conditions = necessity.conditions;

    const necessary = conditions.filter((c) => c.is_necessary);
    const notNecessary = conditions.filter((c) => !c.is_necessary);

    const traces: any[] = [];

    // Necessary conditions (green)
    if (necessary.length > 0) {
      traces.push({
        x: necessary.map((c) => c.consistency),
        y: necessary.map((c) => c.coverage),
        text: necessary.map((c) => c.condition_name),
        type: 'scatter' as const,
        mode: 'markers+text' as const,
        name: 'Necessary',
        textposition: 'top center' as const,
        marker: {
          size: 12,
          color: 'var(--color-success, #059669)',
          symbol: 'circle',
          line: { width: 1, color: '#fff' },
        },
        hovertemplate: '%{text}<br>Consistency: %{x:.3f}<br>Coverage: %{y:.3f}<extra></extra>',
      });
    }

    // Not necessary (gray)
    if (notNecessary.length > 0) {
      traces.push({
        x: notNecessary.map((c) => c.consistency),
        y: notNecessary.map((c) => c.coverage),
        text: notNecessary.map((c) => c.condition_name),
        type: 'scatter' as const,
        mode: 'markers+text' as const,
        name: 'Not Necessary',
        textposition: 'top center' as const,
        marker: {
          size: 10,
          color: 'var(--color-text-secondary, #94a3b8)',
          symbol: 'circle-open',
          line: { width: 1 },
        },
        hovertemplate: '%{text}<br>Consistency: %{x:.3f}<br>Coverage: %{y:.3f}<extra></extra>',
      });
    }

    // Reference line for necessity threshold
    traces.push({
      x: [necessity.threshold, necessity.threshold],
      y: [0, 1],
      type: 'scatter' as const,
      mode: 'lines' as const,
      name: `Threshold = ${necessity.threshold}`,
      line: {
        dash: 'dash',
        color: 'var(--color-warning, #d97706)',
        width: 1,
      },
      showlegend: true,
    });

    return {
      data: traces,
      layout: {
        title: `Necessity Analysis (${necessity.outcome_name})`,
        height,
        xaxis: {
          title: 'Necessity Consistency',
          range: [0, 1.05],
          zeroline: false,
        },
        yaxis: {
          title: 'Necessity Coverage',
          range: [0, 1.05],
          zeroline: false,
        },
        font: {
          family: 'var(--font-mono), monospace',
          size: 11,
        },
        legend: {
          x: 0.01,
          y: 0.99,
          bgcolor: 'rgba(255,255,255,0.8)',
        },
        margin: { l: 60, r: 20, t: 40, b: 60 },
      },
      config: {
        responsive: true,
        displayModeBar: 'hover',
        toImageButtonOptions: {
          format: 'png',
          filename: 'qca-necessity-xy-plot',
          height: 600,
          width: 900,
        },
      },
    };
  }, [necessity]);

  if (necessity.conditions.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        No necessity analysis data available.
      </div>
    );
  }

  return <PlotlyChart data={plotData.data} layout={plotData.layout} config={plotData.config} />;
}
