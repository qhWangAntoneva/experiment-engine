/**
 * CalibrationPreview — live histogram showing how calibration parameters
 * transform raw scores into fuzzy membership values.
 *
 * JS-side calibration formulas mirror the Python strategies.py implementations.
 * Uses synthetic data (normal/uniform/bimodal) so no uploaded data is required.
 */

import React, { useMemo, useState, useEffect, useRef } from 'react';
import { PlotlyChart } from './FuzzySetHeatmap';
import { useT } from '../i18n/I18nContext';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Props {
  thresholdFullIn: number;
  thresholdFullOut: number;
  crossoverPoint: number;
  direction: 'ascending' | 'descending';
  calibrationType: string;
  qcaVariant: string;
  steepness?: number;
}

type Distribution = 'normal' | 'uniform' | 'bimodal';

// ─── Synthetic data generation ────────────────────────────────────────────────

function normalRandom(mean: number, std: number): number {
  // Box-Muller transform
  const u1 = Math.random() || 1e-10;
  const u2 = Math.random();
  return mean + std * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function generateScores(dist: Distribution, n: number = 1000): number[] {
  const scores: number[] = [];
  switch (dist) {
    case 'normal':
      for (let i = 0; i < n; i++) {
        scores.push(Math.max(0, Math.min(1, normalRandom(0.5, 0.15))));
      }
      break;
    case 'uniform':
      for (let i = 0; i < n; i++) {
        scores.push(Math.random());
      }
      break;
    case 'bimodal':
      for (let i = 0; i < n; i++) {
        const v = i < n / 2
          ? normalRandom(0.25, 0.08)
          : normalRandom(0.75, 0.08);
        scores.push(Math.max(0, Math.min(1, v)));
      }
      break;
  }
  return scores;
}

// ─── Min-max normalization ────────────────────────────────────────────────────

function normalizeMinMax(scores: number[]): number[] {
  let min = Infinity, max = -Infinity;
  for (const s of scores) {
    if (s < min) min = s;
    if (s > max) max = s;
  }
  const range = max - min;
  if (range > 0) {
    return scores.map((s) => (s - min) / range);
  }
  return scores.map(() => 0.5);
}

// ─── Calibration strategies ───────────────────────────────────────────────────

function calibrateDirect(
  raw: number[], fullOut: number, fullIn: number, cross: number
): number[] {
  const normalized = normalizeMinMax(raw);
  const denomLow = cross - fullOut;
  const denomHi = fullIn - cross;

  return normalized.map((s) => {
    if (s <= fullOut) return 0.0;
    if (s >= fullIn) return 1.0;
    if (s <= cross) {
      return denomLow > 0 ? 0.5 * (s - fullOut) / denomLow : 0.0;
    }
    return denomHi > 0 ? 0.5 + 0.5 * (s - cross) / denomHi : 0.5;
  });
}

function calibrateIndirect(
  raw: number[], cross: number, k: number
): number[] {
  const normalized = normalizeMinMax(raw);
  const crossLogOdds = (cross > 0 && cross < 1) ? Math.log(cross / (1 - cross)) : 0;

  return normalized.map((s) => {
    if (s <= 0.0) return 0.0;
    if (s >= 1.0) return 1.0;
    const logOdds = Math.log(s / (1 - s));
    return 1.0 / (1.0 + Math.exp(-k * (logOdds - crossLogOdds)));
  });
}

function calibrateRagin(
  raw: number[], fullOut: number, fullIn: number, cross: number
): number[] {
  const logOdds95 = Math.log(0.95 / 0.05);
  const scaleUp = fullIn > cross ? logOdds95 / (fullIn - cross) : 0;
  const scaleDown = cross > fullOut ? logOdds95 / (cross - fullOut) : 0;

  return raw.map((s) => {
    const dev = s >= cross
      ? (s - cross) * scaleUp
      : (s - cross) * scaleDown;
    const clamped = Math.max(-700, Math.min(700, dev));
    const membership = Math.exp(clamped) / (1.0 + Math.exp(clamped));
    return Math.max(0.05, Math.min(0.95, membership));
  });
}

function calibrateCrisp(raw: number[], cross: number): number[] {
  return raw.map((s) => (s >= cross ? 1.0 : 0.0));
}

function calibrate(
  rawScores: number[],
  params: {
    thresholdFullIn: number;
    thresholdFullOut: number;
    crossoverPoint: number;
    direction: 'ascending' | 'descending';
    calibrationType: string;
    steepness: number;
  }
): number[] {
  const { thresholdFullIn, thresholdFullOut, crossoverPoint, calibrationType, steepness } = params;

  let result: number[];
  switch (calibrationType) {
    case 'direct':
      result = calibrateDirect(rawScores, thresholdFullOut, thresholdFullIn, crossoverPoint);
      break;
    case 'indirect':
      result = calibrateIndirect(rawScores, crossoverPoint, steepness);
      break;
    case 'fuzzy_direct':
      result = calibrateRagin(rawScores, thresholdFullOut, thresholdFullIn, crossoverPoint);
      break;
    case 'crisp_set':
      result = calibrateCrisp(rawScores, crossoverPoint);
      break;
    default:
      result = calibrateDirect(rawScores, thresholdFullOut, thresholdFullIn, crossoverPoint);
  }

  if (params.direction === 'descending') {
    result = result.map((v) => 1.0 - v);
  }

  return result;
}

// ─── Debounce hook ────────────────────────────────────────────────────────────

function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    timeoutRef.current = setTimeout(() => setDebounced(value), delayMs);
    return () => {
      if (timeoutRef.current !== null) clearTimeout(timeoutRef.current);
    };
  }, [value, delayMs]);

  return debounced;
}

// ─── Component ────────────────────────────────────────────────────────────────

const N_SAMPLES = 1000;
const N_BINS = 20;

export default function CalibrationPreview(props: Props) {
  const t = useT();

  const effectiveType = props.qcaVariant === 'csqca' ? 'crisp_set' : props.calibrationType;

  const [distribution, setDistribution] = useState<Distribution>('normal');

  const rawScores = useMemo(
    () => generateScores(distribution, N_SAMPLES),
    [distribution]
  );

  const calibratedScores = useMemo(
    () => calibrate(rawScores, {
      thresholdFullIn: props.thresholdFullIn,
      thresholdFullOut: props.thresholdFullOut,
      crossoverPoint: props.crossoverPoint,
      direction: props.direction,
      calibrationType: effectiveType,
      steepness: props.steepness ?? 10,
    }),
    [rawScores, props.thresholdFullIn, props.thresholdFullOut,
     props.crossoverPoint, props.direction, effectiveType, props.steepness]
  );

  // Summary stats (instant, no debounce)
  const stats = useMemo(() => {
    let mean = 0, fullyOut = 0, fullyIn = 0, atCrossover = 0;
    const n = calibratedScores.length;
    for (const v of calibratedScores) {
      mean += v / n;
      if (v <= 0.001) fullyOut++;
      if (v >= 0.999) fullyIn++;
      if (v > 0.49 && v < 0.51) atCrossover++;
    }
    return {
      mean: (mean * 100).toFixed(1),
      fullyOut: ((fullyOut / n) * 100).toFixed(1),
      fullyIn: ((fullyIn / n) * 100).toFixed(1),
      atCrossover: ((atCrossover / n) * 100).toFixed(1),
    };
  }, [calibratedScores]);

  // Debounced Plotly data — prevents purge+newPlot on every slider tick
  const debouncedCalibrated = useDebouncedValue(calibratedScores, 80);

  const plotData = useMemo(() => {
    const methodNames: Record<string, string> = {
      direct: 'Direct',
      indirect: 'Indirect',
      fuzzy_direct: 'Ragin',
      crisp_set: 'Crisp',
    };
    const methodName = methodNames[effectiveType] || effectiveType;
    const dirLabel = props.direction === 'descending' ? ' (↓)' : ' (↑)';

    return {
      data: [
        {
          x: rawScores,
          type: 'histogram' as const,
          name: 'Raw Scores',
          nbinsx: N_BINS,
          opacity: 0.5,
          marker: { color: '#94a3b8' },
          hovertemplate: 'Range: %{x}<br>Count: %{y}<extra></extra>',
        },
        {
          x: debouncedCalibrated,
          type: 'histogram' as const,
          name: 'Membership',
          nbinsx: N_BINS,
          opacity: 0.7,
          marker: {
            color: '#2563eb',
            line: { color: '#fff', width: 1 },
          },
          hovertemplate: 'Range: %{x}<br>Count: %{y}<extra></extra>',
        },
      ],
      layout: {
        title: `${methodName}${dirLabel}  |  ${N_SAMPLES} samples`,
        height: 350,
        barmode: 'overlay' as const,
        xaxis: { title: 'Score', range: [0, 1], dtick: 0.1 },
        yaxis: { title: 'Frequency' },
        margin: { l: 50, r: 20, t: 40, b: 50 },
        font: { family: 'var(--font-mono), monospace', size: 11 },
        legend: { orientation: 'h' as const, y: 1.12 },
      },
      config: {
        responsive: true,
        displayModeBar: 'hover',
        toImageButtonOptions: {
          format: 'png',
          filename: 'qca-calibration-preview',
          height: 600,
          width: 900,
        },
      },
    };
  }, [rawScores, debouncedCalibrated, effectiveType, props.direction]);

  return (
    <div className="calibration-preview">
      <div className="preview-header">
        <h3 className="section-title">{t('settings.calibrationPreview')}</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label className="label" style={{ marginBottom: 0, fontSize: '0.8125rem' }}>
            {t('settings.previewDistribution')}
          </label>
          <select
            className="input"
            value={distribution}
            onChange={(e) => setDistribution(e.target.value as Distribution)}
            style={{ width: 140 }}
          >
            <option value="normal">{t('settings.distributionNormal')}</option>
            <option value="uniform">{t('settings.distributionUniform')}</option>
            <option value="bimodal">{t('settings.distributionBimodal')}</option>
          </select>
        </div>
      </div>
      <p className="setting-desc" style={{ marginBottom: 12 }}>
        {t('settings.previewHelp')}
      </p>
      <div className="preview-chart">
        <PlotlyChart data={plotData.data} layout={plotData.layout} config={plotData.config} />
      </div>
      <div className="preview-stats">
        <div className="stat-item">
          <span>{t('settings.previewMeanMembership')}</span>
          <span className="stat-value">{stats.mean}%</span>
        </div>
        <div className="stat-item">
          <span>{t('settings.previewFullyOut')}</span>
          <span className="stat-value">{stats.fullyOut}%</span>
        </div>
        <div className="stat-item">
          <span>{t('settings.previewFullyIn')}</span>
          <span className="stat-value">{stats.fullyIn}%</span>
        </div>
        <div className="stat-item">
          <span>{t('settings.previewAtCrossover')}</span>
          <span className="stat-value">{stats.atCrossover}%</span>
        </div>
      </div>
    </div>
  );
}
