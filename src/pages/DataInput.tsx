/**
 * Data Input — text corpus upload + condition set YAML editor.
 *
 * Supports:
 *   - File upload (CSV/JSON/TXT) with drag-and-drop
 *   - Text paste with field auto-detection
 *   - Condition set YAML editor with validation
 *   - Domain preset picker
 *   - Run calibration button
 */

import React, { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { useQCAWorkflow } from '../hooks/useQCAWorkflow';
import { usePyodide } from '../hooks/usePyodide';
import PipelineStatus from '../components/PipelineStatus';
import DistributionPlot from '../components/DistributionPlot';
import type { TextCorpusEntry, ConditionSet, TextDomain } from '../types/qca';
import './DataInput.css';

// ─── Default condition set YAML template ────────────────────────────────────

const DEFAULT_CONDITION_SET_YAML = `# QCA Condition Set Definition
# Define causal conditions and the outcome for fuzzy-set analysis.
name: "citizen-feedback-qca"
description: "QCA model of citizen feedback text"
domain: dissatisfaction

# Outcome condition
outcome:
  name: gov_response_effective
  display_name: "政府回应有效"
  domain: dissatisfaction
  calibration_type: direct
  calibration_params:
    threshold_full_in: 0.85
    threshold_full_out: 0.25
    crossover_point: 0.50
    direction: ascending
  keywords:
    - pattern: "已解决"
      weight: 1.0
      scope: bigram
    - pattern: "满意"
      weight: 0.8
      scope: bigram
    - pattern: "效率高"
      weight: 0.7
      scope: bigram

# Causal conditions
conditions:
  - name: strong_negative_affect
    display_name: "强烈负面情感"
    domain: dissatisfaction
    calibration_type: direct
    calibration_params:
      threshold_full_in: 0.80
      threshold_full_out: 0.20
      crossover_point: 0.50
      direction: ascending
    keywords:
      - pattern: "严重"
        weight: 1.0
        scope: unigram
      - pattern: "非常差"
        weight: 0.9
        scope: trigram
      - pattern: "难以忍受"
        weight: 0.8
        scope: exact

  - name: policy_clarity
    display_name: "政策诉求明确性"
    domain: policy_demand
    calibration_type: direct
    calibration_params:
      threshold_full_in: 0.80
      threshold_full_out: 0.20
      crossover_point: 0.50
      direction: ascending
    keywords:
      - pattern: "建议"
        weight: 0.9
        scope: unigram
      - pattern: "要求"
        weight: 0.7
        scope: unigram
`;

const DOMAIN_PRESETS: TextDomain[] = [
  'dissatisfaction',
  'policy_demand',
  'co_production',
  'trust',
  'gov_responsiveness',
];

const DOMAIN_LABELS: Record<TextDomain, string> = {
  dissatisfaction: 'Dissatisfaction',
  policy_demand: 'Policy Demand',
  co_production: 'Co-Production',
  trust: 'Trust',
  gov_responsiveness: 'Gov Responsiveness',
};

// ─── Helper: parse uploaded text into TextCorpusEntry[] ────────────────────

function parseTextContent(content: string, format: 'csv' | 'json' | 'txt'): TextCorpusEntry[] {
  switch (format) {
    case 'csv': {
      const lines = content.split('\n').filter((l) => l.trim());
      if (lines.length === 0) return [];
      // Auto-detect header
      const firstLine = lines[0].toLowerCase();
      const hasHeader = firstLine.includes('text') || firstLine.includes('id') || firstLine.includes('content');
      const start = hasHeader ? 1 : 0;

      return lines.slice(start).map((line, i) => {
        // Support both comma and tab separators
        const sep = line.includes('\t') ? '\t' : ',';
        const parts = line.split(sep).map((p) => p.trim().replace(/^"|"$/g, ''));
        return {
          text_id: parts[0] || `case_${i + 1}`,
          text: parts[1] || parts[0],
          metadata: parts.length > 2 ? { source: parts[2] } : {},
        };
      });
    }
    case 'json': {
      try {
        const parsed = JSON.parse(content);
        const arr = Array.isArray(parsed) ? parsed : parsed.data || parsed.cases || [];
        return arr.map((item: any, i: number) => ({
          text_id: item.id || item.text_id || `case_${i + 1}`,
          text: item.text || item.content || String(item),
          metadata: item.metadata || {},
        }));
      } catch {
        throw new Error('Invalid JSON format. Expected array of objects with "text" field.');
      }
    }
    case 'txt':
    default: {
      // Split by double newline for paragraph-level cases
      const paragraphs = content
        .split(/\n\s*\n/)
        .map((p) => p.trim())
        .filter(Boolean);
      return paragraphs.map((p, i) => ({
        text_id: `txt_${i + 1}`,
        text: p,
        metadata: {},
      }));
    }
  }
}

// ─── Component ─────────────────────────────────────────────────────────────

export default function DataInput() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { state } = useQCAPipeline();
  const { initState } = usePyodide();
  const { runFullPipeline, runCalibrateOnly } = useQCAWorkflow();

  // Form state
  const [texts, setTexts] = useState<TextCorpusEntry[]>([]);
  const [yamlContent, setYamlContent] = useState(DEFAULT_CONDITION_SET_YAML);
  const [parsedConditionSet, setParsedConditionSet] = useState<ConditionSet | null>(null);
  const [textInputMode, setTextInputMode] = useState<'upload' | 'paste'>('paste');
  const [pasteContent, setPasteContent] = useState('');
  const [pasteFormat, setPasteFormat] = useState<'csv' | 'json' | 'txt'>('csv');
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // Handle file upload
  const handleFileUpload = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      const format = file.name.endsWith('.json')
        ? 'json'
        : file.name.endsWith('.csv')
          ? 'csv'
          : 'txt';

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          const entries = parseTextContent(content, format);
          setTexts(entries);
          setValidationMessage(`Loaded ${entries.length} cases from ${file.name}`);
        } catch (err: any) {
          setValidationMessage(`Error: ${err.message}`);
        }
      };
      reader.onerror = () => {
        setValidationMessage('Error reading file');
      };
      reader.readAsText(file, 'UTF-8');
    },
    []
  );

  // Handle paste
  const handleParsePaste = useCallback(() => {
    try {
      const entries = parseTextContent(pasteContent, pasteFormat);
      setTexts(entries);
      setValidationMessage(`Parsed ${entries.length} cases from pasted text`);
    } catch (err: any) {
      setValidationMessage(`Parse error: ${err.message}`);
    }
  }, [pasteContent, pasteFormat]);

  // Handle YAML changes
  const handleYamlChange = useCallback((value: string) => {
    setYamlContent(value);
  }, []);

  // Handle drag-and-drop
  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    const format = file.name.endsWith('.json')
      ? 'json'
      : file.name.endsWith('.csv')
        ? 'csv'
        : 'txt';

    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const content = ev.target?.result as string;
        const entries = parseTextContent(content, format);
        setTexts(entries);
        setValidationMessage(`Loaded ${entries.length} cases from ${file.name}`);
      } catch (err: any) {
        setValidationMessage(`Error: ${err.message}`);
      }
    };
    reader.readAsText(file, 'UTF-8');
  }, []);

  // Run calibration only (texts → fuzzy membership)
  const handleCalibrate = useCallback(async () => {
    if (texts.length === 0) {
      setValidationMessage('No text data loaded. Upload or paste text first.');
      return;
    }

    setIsRunning(true);
    setValidationMessage(null);

    try {
      // Parse YAML to ConditionSet via Pyodide
      // The condition set is sent as a YAML string to the worker for parsing
      // For now, we construct it from the YAML editor content
      // In production, this would use js-yaml for client-side preview + Pyodide for validation

      // Send YAML string as raw input; the worker will parse it
      await runCalibrateOnly({
        texts,
        conditionSet: yamlContent as any, // Worker will parse YAML
      });

      setValidationMessage('Calibration complete. Navigate to Results to analyze.');
    } catch (err: any) {
      setValidationMessage(`Calibration failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  }, [texts, yamlContent, runCalibrateOnly]);

  // Run full pipeline
  const handleRunPipeline = useCallback(async () => {
    if (texts.length === 0) {
      setValidationMessage('No text data loaded.');
      return;
    }

    setIsRunning(true);
    setValidationMessage(null);

    try {
      await runFullPipeline({
        texts,
        conditionSet: yamlContent as any,
        runRobustness: true,
        runCounterfactuals: false,
      });
      setValidationMessage('Analysis complete!');
      setTimeout(() => navigate('/results'), 500);
    } catch (err: any) {
      setValidationMessage(`Pipeline failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  }, [texts, yamlContent, runFullPipeline, navigate]);

  return (
    <div className="data-input">
      <div className="page-header">
        <h2 className="page-title">Data Input</h2>
        <p className="page-subtitle">Upload text corpus and define QCA conditions</p>
      </div>

      <PipelineStatus />

      {/* Engine status warning */}
      {initState.status !== 'ready' && (
        <div
          className="card"
          style={{
            padding: '12px 16px',
            marginBottom: '16px',
            borderColor: 'var(--color-warning)',
            background: 'var(--color-warning-bg)',
            color: 'var(--color-warning)',
            fontSize: '0.8125rem',
          }}
        >
          Pyodide engine is not ready. Go to Dashboard and click "Load Engine" first.
        </div>
      )}

      {/* === Section 1: Text Corpus Input === */}
      <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
        <h3 className="section-title">Text Corpus Input</h3>

        {/* Mode toggle */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <button
            className={`btn ${textInputMode === 'paste' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setTextInputMode('paste')}
            style={{ fontSize: '0.8125rem' }}
          >
            Paste Text
          </button>
          <button
            className={`btn ${textInputMode === 'upload' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setTextInputMode('upload')}
            style={{ fontSize: '0.8125rem' }}
          >
            Upload File
          </button>
        </div>

        {textInputMode === 'paste' ? (
          <div>
            <div style={{ display: 'flex', gap: '12px', marginBottom: '8px', alignItems: 'center' }}>
              <label className="label" style={{ marginBottom: 0 }}>Format:</label>
              <select
                className="input"
                value={pasteFormat}
                onChange={(e) => setPasteFormat(e.target.value as any)}
                style={{ width: 120 }}
              >
                <option value="csv">CSV</option>
                <option value="json">JSON</option>
                <option value="txt">Plain Text</option>
              </select>
              <button className="btn btn-secondary" onClick={handleParsePaste} style={{ fontSize: '0.8125rem', marginLeft: 'auto' }}>
                Parse Text
              </button>
            </div>
            <textarea
              className="input input-mono"
              rows={8}
              value={pasteContent}
              onChange={(e) => setPasteContent(e.target.value)}
              placeholder={
                pasteFormat === 'csv'
                  ? 'id,text\ncase_1,投诉内容...\ncase_2,建议内容...'
                  : pasteFormat === 'json'
                    ? '[{"text_id": "1", "text": "投诉内容..."}]'
                    : '每条文本用空行分隔...'
              }
              style={{ resize: 'vertical', fontSize: '0.8125rem' }}
            />
          </div>
        ) : (
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            style={{
              border: '2px dashed var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: '32px',
              textAlign: 'center',
              cursor: 'pointer',
              background: 'var(--color-bg-input)',
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.json,.txt"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
              Drop a CSV, JSON, or TXT file here
            </p>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
              or click to browse
            </p>
          </div>
        )}

        {/* Text preview */}
        {texts.length > 0 && (
          <div style={{ marginTop: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                {texts.length} cases loaded
              </span>
            </div>
            <div className="table-container" style={{ maxHeight: 200, overflowY: 'auto' }}>
              <table style={{ fontSize: '0.75rem' }}>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Text (truncated)</th>
                  </tr>
                </thead>
                <tbody>
                  {texts.slice(0, 20).map((t, i) => (
                    <tr key={i}>
                      <td className="mono">{t.text_id}</td>
                      <td style={{ maxWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {t.text.substring(0, 80)}{t.text.length > 80 ? '...' : ''}
                      </td>
                    </tr>
                  ))}
                  {texts.length > 20 && (
                    <tr>
                      <td colSpan={2} style={{ textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                        ... and {texts.length - 20} more cases
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Distribution plot (appears after calibration) */}
        {state.fuzzyData && (
          <div style={{ marginTop: '16px' }}>
            <DistributionPlot fuzzyData={state.fuzzyData} height={300} />
          </div>
        )}
      </div>

      {/* === Section 2: Condition Set YAML Editor === */}
      <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
        <h3 className="section-title">Condition Set (YAML)</h3>

        {/* Domain picker */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
          <label className="label" style={{ marginBottom: 0 }}>Domain Preset:</label>
          <select className="input" style={{ width: 180 }}>
            {DOMAIN_PRESETS.map((d) => (
              <option key={d} value={d}>{DOMAIN_LABELS[d]}</option>
            ))}
          </select>
        </div>

        <textarea
          className="input input-mono"
          rows={22}
          value={yamlContent}
          onChange={(e) => handleYamlChange(e.target.value)}
          style={{ resize: 'vertical', fontSize: '0.75rem', lineHeight: 1.5 }}
          spellCheck={false}
        />
      </div>

      {/* === Validation / Status Message === */}
      {validationMessage && (
        <div
          className="card"
          style={{
            padding: '12px 16px',
            marginBottom: '16px',
            fontSize: '0.8125rem',
            borderColor:
              validationMessage.includes('Error') || validationMessage.includes('fail')
                ? 'var(--color-error)'
                : 'var(--color-success)',
            background:
              validationMessage.includes('Error') || validationMessage.includes('fail')
                ? 'var(--color-error-bg)'
                : 'var(--color-success-bg)',
            color:
              validationMessage.includes('Error') || validationMessage.includes('fail')
                ? 'var(--color-error)'
                : 'var(--color-success)',
          }}
        >
          {validationMessage}
        </div>
      )}

      {/* === Actions === */}
      <div className="form-actions" style={{ display: 'flex', gap: '12px' }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleCalibrate}
          disabled={texts.length === 0 || isRunning}
        >
          {isRunning ? 'Calibrating...' : 'Calibrate (Text to Fuzzy-Set)'}
        </button>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleRunPipeline}
          disabled={texts.length === 0 || isRunning}
        >
          {isRunning ? 'Running...' : 'Run Full Pipeline'}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleParsePaste}
        >
          Reset
        </button>
      </div>
    </div>
  );
}
