/**
 * Plotly-based heatmap for truth table visualization.
 *
 * Architecture: receives data as JSON (serialized from Python/Pyodide),
 * renders with Plotly.js directly in TypeScript — no matplotlib needed.
 *
 * Data contract: { z: number[][]; x: string[]; y: string[]; title: string }
 *
 * Dependencies: react-plotly.js, plotly.js-dist-min
 */

import React, { useMemo } from 'react';
import type { TruthTableJSON } from '../types/qca';

// Conditional import — Plotly is lazy-loaded to avoid bloating the initial bundle.
// In production, this is wrapped in a React.lazy() boundary.

interface Props {
  truthTable: TruthTableJSON;
  height?: number;
  colorScale?: string[][];
}

export default function FuzzySetHeatmap({ truthTable, height = 400, colorScale }: Props) {
  const includedRows = useMemo(
    () => truthTable.rows.filter((r) => r.included),
    [truthTable.rows]
  );

  const plotData = useMemo(() => {
    if (includedRows.length === 0) return null;

    const z: number[][] = [];
    const x = ['Frequency', 'Consistency'];
    const y = includedRows.map((r) => r.config_label);

    // Build frequency + consistency columns
    for (let i = 0; i < includedRows.length; i++) {
      z.push([includedRows[i].frequency, includedRows[i].raw_consistency]);
    }

    return {
      data: [
        {
          z: z,
          x: x,
          y: y,
          type: 'heatmap' as const,
          colorscale: colorScale || [
            ['0.0', '#f7fbff'],
            ['0.25', '#deebf7'],
            ['0.5', '#9ecae1'],
            ['0.75', '#4292c6'],
            ['1.0', '#08519c'],
          ],
          showscale: true,
          hovertemplate:
            'Config: %{y}<br>%{x}: %{z}<extra></extra>',
          colorbar: {
            title: 'Value',
            titleside: 'right' as const,
          },
        },
      ],
      layout: {
        title: `Truth Table Heatmap (${truthTable.outcome_name})`,
        height,
        margin: { l: 120, r: 40, t: 40, b: 40 },
        xaxis: { side: 'top' as const },
        yaxis: { automargin: true },
        font: {
          family: 'var(--font-mono), monospace',
          size: 11,
        },
      },
      config: {
        responsive: true,
        displayModeBar: 'hover',
        toImageButtonOptions: {
          format: 'png',
          filename: 'qca-fuzzy-heatmap',
          height: 600,
          width: 900,
        },
      },
    };
  }, [includedRows, truthTable.outcome_name, height, colorScale]);

  if (!plotData) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        No included rows to display in heatmap.
      </div>
    );
  }

  return (
    <div style={{ width: '100%', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
      <PlotlyChart data={plotData.data} layout={plotData.layout} config={plotData.config} />
    </div>
  );
}

// ─── Lazy Plotly loader ────────────────────────────────────────────────────
// This avoids bundling Plotly (~3MB) in the main chunk.
// Plotly is loaded on first render of any chart component.

let PlotlyModule: any = null;
let plotlyLoadPromise: Promise<any> | null = null;

function loadPlotly(): Promise<any> {
  if (PlotlyModule) return Promise.resolve(PlotlyModule);
  if (plotlyLoadPromise) return plotlyLoadPromise;

  plotlyLoadPromise = import('plotly.js-dist-min').then((mod) => {
    PlotlyModule = mod.default || mod;
    return PlotlyModule;
  }).catch((err) => {
    plotlyLoadPromise = null;
    throw err;
  });

  return plotlyLoadPromise;
}

function PlotlyChart({ data, layout, config }: { data: any[]; layout: any; config?: any }) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    const container = containerRef.current;
    if (!container) return;

    loadPlotly()
      .then((Plotly) => {
        if (cancelled || !container) return;
        Plotly.newPlot(container, data, layout, config);
      })
      .catch((err: any) => {
        if (!cancelled) setError(err.message || 'Failed to load Plotly');
      });

    return () => {
      cancelled = true;
      if (container && PlotlyModule) {
        PlotlyModule.purge(container);
      }
    };
  }, [data, layout, config]);

  if (error) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-error)' }}>
        Chart error: {error}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: layout?.height || 400 }}
    />
  );
}

export { loadPlotly, PlotlyChart };
