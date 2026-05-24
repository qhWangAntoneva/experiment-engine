/**
 * Settings — QCA analysis parameters, calibration defaults, and engine config.
 *
 * Groups:
 *   1. Calibration Defaults (threshold_full_in/out, crossover, direction)
 *   2. Analysis Thresholds (consistency, frequency, necessity N-cut)
 *   3. Export Preferences (format, include raw data)
 *   4. About / Version Info
 */

import React, { useState, useCallback } from 'react';
import { DEFAULT_QCA_PARAMS, type QCAAnalysisParams, type ConditionSet } from '../types/qca';
import { usePyodide } from '../hooks/usePyodide';
import { useQCAWorkflow } from '../hooks/useQCAWorkflow';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import './Settings.css';

interface SettingField {
  key: string;
  label: string;
  type: 'number' | 'select' | 'boolean' | 'range';
  default: string | number | boolean;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  description: string;
  group: 'calibration' | 'analysis' | 'export';
}

const settings: SettingField[] = [
  // ── Calibration Defaults ──
  {
    key: 'threshold_full_in',
    label: 'Threshold Full-In',
    type: 'number',
    default: 0.85,
    min: 0.5,
    max: 1.0,
    step: 0.01,
    description: 'Membership score above which a case is fully in the set (0.5-1.0)',
    group: 'calibration',
  },
  {
    key: 'threshold_full_out',
    label: 'Threshold Full-Out',
    type: 'number',
    default: 0.20,
    min: 0.0,
    max: 0.5,
    step: 0.01,
    description: 'Membership score below which a case is fully out of the set (0.0-0.5)',
    group: 'calibration',
  },
  {
    key: 'crossover_point',
    label: 'Crossover Point',
    type: 'number',
    default: 0.50,
    min: 0.0,
    max: 1.0,
    step: 0.01,
    description: 'Score at which membership = 0.5 (maximum ambiguity)',
    group: 'calibration',
  },
  {
    key: 'calibration_direction',
    label: 'Default Direction',
    type: 'select',
    default: 'ascending',
    options: ['ascending', 'descending'],
    description: 'Whether higher keyword scores mean higher membership (ascending) or lower (descending)',
    group: 'calibration',
  },
  {
    key: 'calibration_type',
    label: 'Calibration Method',
    type: 'select',
    default: 'direct',
    options: ['direct', 'indirect', 'fuzzy_direct', 'crisp_set'],
    description: 'Direct = piecewise linear, Indirect = log-odds, Fuzzy Direct = Ragins method',
    group: 'calibration',
  },

  // ── Analysis Thresholds ──
  {
    key: 'consistency_threshold',
    label: 'Consistency Threshold',
    type: 'number',
    default: DEFAULT_QCA_PARAMS.consistency_threshold,
    min: 0.5,
    max: 1.0,
    step: 0.01,
    description: 'Minimum subset consistency for a truth table row to be assigned outcome=1',
    group: 'analysis',
  },
  {
    key: 'frequency_threshold',
    label: 'Frequency Threshold',
    type: 'number',
    default: DEFAULT_QCA_PARAMS.frequency_threshold,
    min: 1,
    max: 100,
    step: 1,
    description: 'Minimum number of cases for a truth table configuration to be included',
    group: 'analysis',
  },
  {
    key: 'necessity_threshold',
    label: 'Necessity Threshold',
    type: 'number',
    default: DEFAULT_QCA_PARAMS.necessity_threshold,
    min: 0.7,
    max: 1.0,
    step: 0.01,
    description: 'Minimum consistency for a condition to be considered necessary (typically 0.9)',
    group: 'analysis',
  },
  {
    key: 'n_cut',
    label: 'N-Cut (Truth Table)',
    type: 'range',
    default: DEFAULT_QCA_PARAMS.n_cut,
    min: 1,
    max: 20,
    step: 1,
    description: 'Frequency cutoff for truth table rows. Higher values reduce noise but require more cases.',
    group: 'analysis',
  },

  // ── Export Preferences ──
  {
    key: 'export_default_format',
    label: 'Default Export Format',
    type: 'select',
    default: 'json',
    options: ['csv', 'json', 'latex'],
    description: 'Default format when exporting analysis results',
    group: 'export',
  },
  {
    key: 'include_raw_data',
    label: 'Include Raw Data in Export',
    type: 'boolean',
    default: false,
    description: 'Whether to include the original membership matrix in exported files',
    group: 'export',
  },
  {
    key: 'pretty_print_json',
    label: 'Pretty-Print JSON',
    type: 'boolean',
    default: true,
    description: 'Use indented formatting when exporting JSON',
    group: 'export',
  },
];

export default function Settings() {
  const { initState } = usePyodide();
  const { exportKeywords } = useQCAWorkflow();
  const { state: pipelineState } = useQCAPipeline();

  const [values, setValues] = useState<Record<string, string | number | boolean>>(() => {
    const initial: Record<string, string | number | boolean> = {};
    for (const s of settings) {
      initial[s.key] = s.default;
    }
    return initial;
  });

  const [saved, setSaved] = useState(false);

  // ─── Export Dictionary state ──────────────────────────────────────────────
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('csv');
  const [exportStatus, setExportStatus] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const handleExportDictionary = useCallback(async () => {
    const cs: ConditionSet | null = pipelineState.conditionSet;
    if (!cs) {
      setExportStatus('No condition set loaded. Import or define a dictionary first.');
      return;
    }
    setIsExporting(true);
    setExportStatus(null);
    try {
      const blob = await exportKeywords(cs, exportFormat);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `keywords-dictionary.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setExportStatus(`Exported ${cs.conditions.length} condition(s) as ${exportFormat.toUpperCase()}.`);
    } catch (err: any) {
      setExportStatus(`Export failed: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  }, [pipelineState.conditionSet, exportFormat, exportKeywords]);

  const updateValue = useCallback((key: string, value: string | number | boolean) => {
    setValues((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  }, []);

  const handleSave = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      // Build analysis params for downstream use
      const params: QCAAnalysisParams = {
        consistency_threshold: Number(values.consistency_threshold),
        frequency_threshold: Number(values.frequency_threshold),
        necessity_threshold: Number(values.necessity_threshold),
        n_cut: Number(values.n_cut),
      };

      // Save to localStorage
      try {
        localStorage.setItem('qca-settings', JSON.stringify(values));
        localStorage.setItem('qca-params', JSON.stringify(params));
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      } catch {
        // localStorage unavailable (private browsing)
      }
    },
    [values]
  );

  const calibrationFields = settings.filter((s) => s.group === 'calibration');
  const analysisFields = settings.filter((s) => s.group === 'analysis');
  const exportFields = settings.filter((s) => s.group === 'export');

  return (
    <div className="settings">
      <div className="page-header">
        <h2 className="page-title">Settings</h2>
        <p className="page-subtitle">QCA pipeline configuration and preferences</p>
      </div>

      <form onSubmit={handleSave}>
        {/* Calibration Section */}
        <div className="settings-section card">
          <h3 className="section-title">Calibration Defaults</h3>
          {calibrationFields.map((s) => (
            <SettingRow key={s.key} field={s} value={values[s.key]} onChange={updateValue} />
          ))}
        </div>

        {/* Analysis Section */}
        <div className="settings-section card">
          <h3 className="section-title">Analysis Thresholds</h3>
          {analysisFields.map((s) => (
            <SettingRow key={s.key} field={s} value={values[s.key]} onChange={updateValue} />
          ))}
        </div>

        {/* Export Section */}
        <div className="settings-section card">
          <h3 className="section-title">Export Preferences</h3>
          {exportFields.map((s) => (
            <SettingRow key={s.key} field={s} value={values[s.key]} onChange={updateValue} />
          ))}
        </div>

        {/* Engine Status */}
        <div className="settings-section card">
          <h3 className="section-title">Engine Status</h3>
          <div className="about-grid">
            <div className="about-item">
              <span className="about-label">Pyodide</span>
              <span className={`badge ${initState.status === 'ready' ? 'badge-success' : 'badge-warning'}`}>
                {initState.status}
              </span>
            </div>
            <div className="about-item">
              <span className="about-label">Python Version</span>
              <span className="about-value mono">3.12 (via Pyodide v0.26)</span>
            </div>
            <div className="about-item">
              <span className="about-label">Packages</span>
              <span className="about-value mono">
                {initState.status === 'ready'
                  ? (initState as any).loadedPackages?.join(', ') || 'numpy, pyyaml'
                  : 'Not loaded'}
              </span>
            </div>
            <div className="about-item">
              <span className="about-label">Worker Thread</span>
              <span className="about-value">{initState.status === 'ready' ? 'Active' : 'Idle'}</span>
            </div>
          </div>
        </div>

        {/* Export Keyword Dictionary */}
        <div className="settings-section card">
          <h3 className="section-title">Export Keyword Dictionary</h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
            Export the current condition set's keyword dictionary to CSV or JSON for reuse in other projects.
            {!pipelineState.conditionSet && (
              <span style={{ color: 'var(--color-warning)' }}>
                {' '}No condition set is currently loaded. Import or define a dictionary first on the Data Input page.
              </span>
            )}
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <select
              className="input"
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as 'csv' | 'json')}
              style={{ width: 120 }}
            >
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
            <button
              className="btn btn-primary"
              onClick={handleExportDictionary}
              disabled={isExporting || !pipelineState.conditionSet}
              style={{ fontSize: '0.8125rem' }}
            >
              {isExporting ? 'Exporting...' : 'Export Dictionary'}
            </button>
          </div>
          {exportStatus && (
            <p style={{
              marginTop: '12px',
              fontSize: '0.8125rem',
              color: exportStatus.includes('fail') ? 'var(--color-error)' : 'var(--color-success)',
            }}>
              {exportStatus}
            </p>
          )}
        </div>

        {/* About */}
        <div className="settings-section card">
          <h3 className="section-title">About</h3>
          <div className="about-grid">
            <div className="about-item">
              <span className="about-label">Application</span>
              <span className="about-value">QCA Text Analysis Tool</span>
            </div>
            <div className="about-item">
              <span className="about-label">Version</span>
              <span className="about-value mono">0.2.0</span>
            </div>
            <div className="about-item">
              <span className="about-label">Frontend</span>
              <span className="about-value">React 18 + TypeScript + Vite 5</span>
            </div>
            <div className="about-item">
              <span className="about-label">Python Engine</span>
              <span className="about-value">Pyodide 0.26 (in-browser)</span>
            </div>
            <div className="about-item">
              <span className="about-label">Analysis Engine</span>
              <span className="about-value">experiment-engine v0.2.0</span>
            </div>
            <div className="about-item">
              <span className="about-label">Visualization</span>
              <span className="about-value">Plotly.js (client-side)</span>
            </div>
          </div>
        </div>

        {/* Save */}
        <div className="form-actions">
          <button type="submit" className="btn btn-primary">
            Save Settings
          </button>
          {saved && (
            <span style={{ color: 'var(--color-success)', fontSize: '0.8125rem' }}>
              Settings saved.
            </span>
          )}
        </div>
      </form>
    </div>
  );
}

// ─── Setting Row Component ─────────────────────────────────────────────────

function SettingRow({
  field,
  value,
  onChange,
}: {
  field: SettingField;
  value: string | number | boolean;
  onChange: (key: string, value: string | number | boolean) => void;
}) {
  return (
    <div className="setting-row">
      <div className="setting-info">
        <label className="setting-label" htmlFor={field.key}>
          {field.label}
        </label>
        <p className="setting-desc">{field.description}</p>
      </div>
      <div className="setting-control">
        {field.type === 'number' && (
          <input
            id={field.key}
            className="input input-mono"
            type="number"
            min={field.min}
            max={field.max}
            step={field.step}
            value={value as number}
            onChange={(e) => onChange(field.key, e.target.valueAsNumber || 0)}
            style={{ width: 120 }}
          />
        )}
        {field.type === 'range' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: 160 }}>
            <input
              id={field.key}
              type="range"
              min={field.min}
              max={field.max}
              step={field.step}
              value={value as number}
              onChange={(e) => onChange(field.key, Number(e.target.value))}
              style={{ flex: 1 }}
            />
            <span className="mono" style={{ fontSize: '0.8125rem', fontWeight: 600, minWidth: 28 }}>
              {value}
            </span>
          </div>
        )}
        {field.type === 'select' && (
          <select
            id={field.key}
            className="input"
            value={value as string}
            onChange={(e) => onChange(field.key, e.target.value)}
            style={{ width: 160 }}
          >
            {field.options?.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        )}
        {field.type === 'boolean' && (
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={value as boolean}
              onChange={(e) => onChange(field.key, e.target.checked)}
            />
            <span className="toggle-text">{value ? 'Enabled' : 'Disabled'}</span>
          </label>
        )}
      </div>
    </div>
  );
}
