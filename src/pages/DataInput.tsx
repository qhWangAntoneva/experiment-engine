/**
 * Data Input — text corpus upload + condition set YAML editor.
 *
 * Supports:
 *   - File upload (CSV/JSON/TXT/XLSX) with drag-and-drop
 *   - Text paste with field auto-detection
 *   - Condition set YAML editor with validation
 *   - Domain preset picker
 *   - Run calibration button
 *   - Prototype calibration mode: structured text input + prototype editor table
 */

import React, { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { useQCAWorkflow } from '../hooks/useQCAWorkflow';
import { usePyodide } from '../hooks/usePyodide';
import { useT } from '../i18n/I18nContext';
import PipelineStatus from '../components/PipelineStatus';
import DistributionPlot from '../components/DistributionPlot';
import type {
  TextCorpusEntry,
  TextCase,
  ConditionSet,
  ConditionDefinition,
  ConceptPrototype,
  ScoringSource,
  TextDomain,
} from '../types/qca';
import { CalibrationMethod, QCAVariant } from '../types/qca';
import './DataInput.css';

// ─── Default condition set YAML template ────────────────────────────────────

// FIXME-BERT: YAML template still uses 'keywords' fields — replace with prototype-based template after Phase 2

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

/** @deprecated Use t('dataInput.domainLabels.xxx') from I18nContext instead. */
const _DOMAIN_LABELS_LEGACY: Record<TextDomain, string> = {
  dissatisfaction: 'Dissatisfaction',
  policy_demand: 'Policy Demand',
  co_production: 'Co-Production',
  trust: 'Trust',
  gov_responsiveness: 'Gov Responsiveness',
};

// ─── Frontend-only helpers: file detection (lightweight pre-checks) ────────
// All actual text parsing is delegated to Python's TextCorpusReader
// via the Pyodide worker to avoid duplicating CSV/JSON/TXT/XLSX logic.

/** Detect corpus format from file extension (frontend pre-check only). */
function detectCorpusFormat(fileName: string): 'csv' | 'json' | 'txt' | 'xlsx' {
  const lower = fileName.toLowerCase();
  if (lower.endsWith('.csv')) return 'csv';
  if (lower.endsWith('.json')) return 'json';
  if (lower.endsWith('.xlsx') || lower.endsWith('.xls')) return 'xlsx';
  return 'txt';
}

/** Convert an ArrayBuffer to a base64 string for transfer to the worker. */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/** Maximum upload file size: 10 MB. */
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

/**
 * Read the configured QCA variant from localStorage settings.
 * Returns QCAVariant.CSQCA if 'csqca' is set, otherwise QCAVariant.FSQCA.
 */
function getQCAVariantFromSettings(): QCAVariant {
  try {
    const raw = localStorage.getItem('qca-settings');
    if (raw) {
      const settings = JSON.parse(raw);
      if (settings.qca_variant === 'csqca') return QCAVariant.CSQCA;
    }
  } catch {}
  return QCAVariant.FSQCA;
}

/**
 * Check that a File object is within the acceptable size limit.
 * Returns an error message string on failure, or null if OK.
 */
function checkFileSize(file: File): string | null {
  if (file.size > MAX_FILE_SIZE_BYTES) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
    return `File too large: ${sizeMB} MB (max 10 MB)`;
  }
  return null;
}

// ─── Prototype mode helpers ────────────────────────────────────────────────

interface PrototypeConditionRow {
  id: string;
  name: string;
  displayName: string;
  prototypesText: string;
}

let _protoRowIdCounter = 0;
function newProtoRow(name: string = '', displayName: string = '', prototypesText: string = ''): PrototypeConditionRow {
  _protoRowIdCounter += 1;
  return { id: `pcr_${_protoRowIdCounter}`, name, displayName, prototypesText };
}

/** Parse prototype textarea lines into ConceptPrototype[] */
function parsePrototypeTexts(text: string): ConceptPrototype[] {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const match = line.match(/^\[([01])\]\s*(.+)/);
      if (match) {
        return {
          prototype_text: match[2].trim(),
          is_member: parseInt(match[1]) as 0 | 1,
          weight: 1.0,
        };
      }
      // Default: no prefix means membership = 1
      return {
        prototype_text: line,
        is_member: 1 as const,
        weight: 1.0,
      };
    });
}

/** Parse prototype CSV input (3 columns: 编号, 文本内容, 结果) into TextCase[] */
function parsePrototypeCSV(content: string): TextCase[] {
  const lines = content.split('\n').filter((l) => l.trim());
  if (lines.length === 0) return [];

  const firstLine = lines[0].toLowerCase();
  const hasHeader =
    firstLine.includes('编号') ||
    firstLine.includes('文本') ||
    firstLine.includes('结果') ||
    firstLine.includes('text') ||
    firstLine.includes('outcome');
  const start = hasHeader ? 1 : 0;

  return lines.slice(start).map((line, i) => {
    const sep = line.includes('\t') ? '\t' : ',';
    const parts = line.split(sep).map((p) => p.trim().replace(/^"|"$/g, ''));
    return {
      text_id: parts[0] || `case_${i + 1}`,
      text: parts[1] || parts[0],
      outcome: (parseInt(parts[2]) || 0) as 0 | 1,
    };
  });
}

/** Generate a ConditionSet from prototype editor rows */
function generatePrototypeConditionSet(
  rows: PrototypeConditionRow[],
  domain: TextDomain,
  qcaVariant: QCAVariant = QCAVariant.FSQCA,
): ConditionSet {
  const calType = qcaVariant === QCAVariant.CSQCA
    ? CalibrationMethod.CRISP_SET
    : CalibrationMethod.DIRECT;

  const conditions: ConditionDefinition[] = rows
    .filter((row) => row.name.trim() !== '')
    .map((row) => ({
      name: row.name.trim(),
      display_name: row.displayName.trim() || row.name.trim(),
      domain,
      calibration_type: calType,
      calibration_params: qcaVariant === QCAVariant.CSQCA
        ? null
        : {
            threshold_full_in: 0.80,
            threshold_full_out: 0.20,
            crossover_point: 0.50,
            direction: 'ascending' as const,
          },
      description: '',
      scoring_source: 'prototype' as ScoringSource,
      prototypes: parsePrototypeTexts(row.prototypesText),
      prototype_embeddings: null,
      embedding_model: null,
    }));

  return {
    name: 'prototype-qca',
    description: `QCA model with prototype-based calibration (${qcaVariant})`,
    conditions,
    outcome: {
      name: 'outcome',
      display_name: 'Outcome',
      domain,
      calibration_type: qcaVariant === QCAVariant.CSQCA
        ? CalibrationMethod.CRISP_SET
        : CalibrationMethod.PASSTHROUGH,
      calibration_params: null,
      description: 'Binary outcome from text input',
      scoring_source: 'prototype' as ScoringSource,
      prototypes: [],
      prototype_embeddings: null,
      embedding_model: null,
    },
    domain,
    scoring_source: 'prototype',
    qca_variant: qcaVariant,
  };
}

// ─── Component ─────────────────────────────────────────────────────────────

export default function DataInput() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const t = useT();

  const { state } = useQCAPipeline();
  const { initState } = usePyodide();
  const {
    runFullPipeline,
    runCalibrateOnly,
    loadCorpus,
  } = useQCAWorkflow();
  // Phase 5 stubs: keyword functionality removed
  const importKeywords = async (..._args: any[]): Promise<any> => ({ conditions: [], outcome: null } as any);
  const exportKeywords = async (..._args: any[]): Promise<any> => new Blob();

  // ─── Form state ────────────────────────────────────────────────────

  // Keyword mode form state
  const [texts, setTexts] = useState<TextCorpusEntry[]>([]);
  const [yamlContent, setYamlContent] = useState(DEFAULT_CONDITION_SET_YAML);
  const [textInputMode, setTextInputMode] = useState<'upload' | 'paste'>('paste');
  const [pasteContent, setPasteContent] = useState('');
  const [pasteFormat, setPasteFormat] = useState<'csv' | 'json' | 'txt'>('csv');
  const [selectedDomain, setSelectedDomain] = useState<TextDomain>('dissatisfaction');

  // Prototype mode form state
  const [textCases, setTextCases] = useState<TextCase[]>([]);
  const [protoPasteContent, setProtoPasteContent] = useState('');
  const [protoConditions, setProtoConditions] = useState<PrototypeConditionRow[]>([
    newProtoRow('', ''),
    newProtoRow('', ''),
  ]);

  const [importedConditionSet, setImportedConditionSet] = useState<ConditionSet | null>(null);
  const dictFileInputRef = useRef<HTMLInputElement>(null);

  // ─── Export state ─────────────────────────────────────────────────────
  const [isExporting, setIsExporting] = useState(false);

  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // ─── Keyword mode handlers ───────────────────────────────────────────────

  const handleFileUpload = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      const sizeError = checkFileSize(file);
      if (sizeError) {
        setValidationMessage(t('dataInput.fileTooLarge', (file.size / (1024 * 1024)).toFixed(1)));
        return;
      }

      const format = detectCorpusFormat(file.name);

      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          let content: string;
          if (format === 'xlsx') {
            // Binary file — read as ArrayBuffer and base64-encode
            content = arrayBufferToBase64(e.target?.result as ArrayBuffer);
          } else {
            content = e.target?.result as string;
          }
          const entries = await loadCorpus(file.name, content, format);
          setTexts(entries);
          setValidationMessage(t('dataInput.loadedCases', entries.length, file.name));
        } catch (err: any) {
          setValidationMessage(`${t('common.error')}: ${err.message}`);
        }
      };
      reader.onerror = () => {
        setValidationMessage(t('dataInput.errorReadingFile'));
      };
      if (format === 'xlsx') {
        reader.readAsArrayBuffer(file);
      } else {
        reader.readAsText(file, 'UTF-8');
      }
    },
    [loadCorpus]
  );

  const handleParsePaste = useCallback(async () => {
    try {
      // Generate a synthetic file name so Python TextCorpusReader
      // can detect the format from the extension.
      const fileName =
        pasteFormat === 'csv' ? 'pasted.csv'
        : pasteFormat === 'json' ? 'pasted.json'
        : 'pasted.txt';
      const entries = await loadCorpus(fileName, pasteContent, pasteFormat);
      setTexts(entries);
      setValidationMessage(t('dataInput.parsedCases', entries.length));
    } catch (err: any) {
      setValidationMessage(`${t('dataInput.parseError')}${err.message}`);
    }
  }, [pasteContent, pasteFormat, loadCorpus, t]);

  const handleYamlChange = useCallback((value: string) => {
    setYamlContent(value);
  }, []);

  // ─── Dictionary Import handler ─────────────────────────────────────────

  const detectDictFormat = useCallback((fileName: string): 'csv' | 'json' => {
    const lower = fileName.toLowerCase();
    if (lower.endsWith('.json')) return 'json';
    return 'csv'; // default to CSV for .csv, .txt, etc.
  }, []);

  const handleDictFileUpload = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      const format = detectDictFormat(file.name);
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const content = e.target?.result as string;
          const cs = await importKeywords(file.name, content, format, selectedDomain);
          setImportedConditionSet(cs);
          // FIXME-BERT: c.keywords removed from ConditionDefinition — keyword count unavailable after Phase 2
          const kwCount = cs.conditions.reduce(
            (sum: number, c: any) => sum + ((c as any).keywords?.length ?? 0), 0
          );
          if (cs.outcome) {
            const outcomeKws = (cs.outcome as any).keywords?.length ?? 0;
            setValidationMessage(
              t('dataInput.importedDict', cs.conditions.length, true, kwCount + outcomeKws, file.name)
            );
          } else {
            setValidationMessage(
              t('dataInput.importedDictNoOutcome', cs.conditions.length, kwCount, file.name)
            );
          }
        } catch (err: any) {
          setValidationMessage(`${t('dataInput.dictImportError')}${err.message}`);
        }
      };
      reader.onerror = () => {
        setValidationMessage(t('dataInput.errorReadingFile'));
      };
      reader.readAsText(file, 'UTF-8');
    },
    [importKeywords, selectedDomain, detectDictFormat]
  );

  const handleExportKeywords = useCallback(async () => {
    if (!importedConditionSet) {
      setValidationMessage(t('dataInput.noDictLoaded'));
      return;
    }
    setIsExporting(true);
    setValidationMessage(null);
    try {
      const blob = await exportKeywords(importedConditionSet, 'csv');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'keywords-dictionary.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      // FIXME-BERT: c.keywords removed from ConditionDefinition — keyword count unavailable after Phase 2
      const kwCount = importedConditionSet.conditions.reduce(
        (sum, c) => sum + ((c as any).keywords?.length ?? 0), 0
      );
      setValidationMessage(
        t('dataInput.exportedDict', importedConditionSet.conditions.length, kwCount)
      );
    } catch (err: any) {
      setValidationMessage(`${t('dataInput.exportDictError')}${err.message}`);
    } finally {
      setIsExporting(false);
    }
  }, [importedConditionSet, exportKeywords, t]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    const sizeError = checkFileSize(file);
    if (sizeError) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      setValidationMessage(t('dataInput.fileTooLarge', sizeMB));
      return;
    }

    const format = detectCorpusFormat(file.name);

    const reader = new FileReader();
    reader.onload = async (ev) => {
      try {
        let content: string;
        if (format === 'xlsx') {
          content = arrayBufferToBase64(ev.target?.result as ArrayBuffer);
        } else {
          content = ev.target?.result as string;
        }
        const entries = await loadCorpus(file.name, content, format);
        setTexts(entries);
        setValidationMessage(t('dataInput.loadedCases', entries.length, file.name));
      } catch (err: any) {
        setValidationMessage(`${t('common.error')}: ${err.message}`);
      }
    };
    if (format === 'xlsx') {
      reader.readAsArrayBuffer(file);
    } else {
      reader.readAsText(file, 'UTF-8');
    }
  }, [loadCorpus, t]);

  // ─── Prototype mode handlers ─────────────────────────────────────────────

  const handleParseProtoCSV = useCallback(() => {
    try {
      const cases = parsePrototypeCSV(protoPasteContent);
      setTextCases(cases);
      const outcome0 = cases.filter((c) => c.outcome === 0).length;
      const outcome1 = cases.filter((c) => c.outcome === 1).length;
      setValidationMessage(
        t('dataInput.parsedProtoCases', cases.length, outcome0, outcome1)
      );
    } catch (err: any) {
      setValidationMessage(`${t('dataInput.protoCsvParseError')}${err.message}`);
    }
  }, [protoPasteContent, t]);

  const handleProtoFileUpload = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          const cases = parsePrototypeCSV(content);
          setTextCases(cases);
          const outcome0 = cases.filter((c) => c.outcome === 0).length;
          const outcome1 = cases.filter((c) => c.outcome === 1).length;
          setValidationMessage(
            t('dataInput.loadedProtoCases', cases.length, outcome0, outcome1, file.name)
          );
        } catch (err: any) {
          setValidationMessage(`${t('common.error')}: ${err.message}`);
        }
      };
      reader.onerror = () => {
        setValidationMessage(t('dataInput.errorReadingFile'));
      };
      reader.readAsText(file, 'UTF-8');
    },
    [t]
  );

  const handleProtoDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const content = ev.target?.result as string;
        const cases = parsePrototypeCSV(content);
        setTextCases(cases);
        const outcome0 = cases.filter((c) => c.outcome === 0).length;
        const outcome1 = cases.filter((c) => c.outcome === 1).length;
        setValidationMessage(
          t('dataInput.loadedProtoCases', cases.length, outcome0, outcome1, file.name)
        );
      } catch (err: any) {
        setValidationMessage(`${t('common.error')}: ${err.message}`);
      }
    };
    reader.readAsText(file, 'UTF-8');
  }, [t]);

  const updateProtoCondition = useCallback(
    (index: number, field: keyof PrototypeConditionRow, value: string) => {
      setProtoConditions((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], [field]: value };
        return next;
      });
    },
    []
  );

  const addProtoCondition = useCallback(() => {
    setProtoConditions((prev) => [...prev, newProtoRow('', '')]);
  }, []);

  const removeProtoCondition = useCallback((index: number) => {
    setProtoConditions((prev) => {
      if (prev.length <= 1) return prev;
      return prev.filter((_, i) => i !== index);
    });
  }, []);

  const handleReset = useCallback(() => {
    handleParsePaste();
  }, [handleParsePaste]);



  // ─── Calibration / Pipeline triggers ─────────────────────────────────────

  const handleCalibrate = useCallback(async () => {
    if (texts.length === 0) {
      setValidationMessage(t('dataInput.noTextData'));
      return;
    }

    setIsRunning(true);
    setValidationMessage(null);

    try {
      await runCalibrateOnly({
        texts,
        conditionSet: importedConditionSet
          ? { ...importedConditionSet, qca_variant: importedConditionSet.qca_variant ?? getQCAVariantFromSettings() }
          : (yamlContent as any), // YAML string parsed on Python side
        prototypeTexts: textCases.length > 0 ? textCases : undefined,
      });
      if (textCases.length > 0) {
        setValidationMessage(t('dataInput.calibrationCompleteProto', textCases.length));
      } else {
        setValidationMessage(t('dataInput.calibrationComplete'));
      }
    } catch (err: any) {
      setValidationMessage(`${t('dataInput.calibrationFailed')}${err.message}`);
    } finally {
      setIsRunning(false);
    }
  }, [
    textCases, texts, yamlContent,
    runCalibrateOnly, t,
  ]);

  const handleRunPipeline = useCallback(async () => {
    if (texts.length === 0) {
      setValidationMessage(t('dataInput.noTextData'));
      return;
    }

    setIsRunning(true);
    setValidationMessage(null);

    try {
      await runFullPipeline({
        texts,
        conditionSet: importedConditionSet
          ? { ...importedConditionSet, qca_variant: importedConditionSet.qca_variant ?? getQCAVariantFromSettings() }
          : (yamlContent as any), // YAML string parsed on Python side
        runRobustness: true,
        runCounterfactuals: false,
        prototypeTexts: textCases.length > 0 ? textCases : undefined,
      });
      setValidationMessage(t('dataInput.analysisComplete'));
      setTimeout(() => navigate('/results'), 500);
    } catch (err: any) {
      setValidationMessage(`${t('dataInput.pipelineFailed')}${err.message}`);
    } finally {
      setIsRunning(false);
    }
  }, [
    textCases, texts, yamlContent,
    runFullPipeline,
    navigate, t,
  ]);

  return (
    <div className="data-input">
      <div className="page-header">
        <h2 className="page-title">{t('dataInput.title')}</h2>
        <p className="page-subtitle">{t('dataInput.subtitle')}</p>
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
          {t('dataInput.engineNotReady')}
        </div>
      )}

      {/* FIXME-BERT: Section 0 — Import/Export Keyword Dictionary (keyword-specific, remove after Phase 3) */}
      <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h3 className="section-title" style={{ marginBottom: 0, borderBottom: 'none', paddingBottom: 0 }}>
            {t('dataInput.importExportTitle')}
          </h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn btn-secondary"
              onClick={() => dictFileInputRef.current?.click()}
              style={{ fontSize: '0.8125rem' }}
            >
              {t('dataInput.importCsvJson')}
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleExportKeywords}
              disabled={isExporting || !importedConditionSet}
              style={{ fontSize: '0.8125rem' }}
            >
              {isExporting ? t('dataInput.exporting') : t('dataInput.exportCsv')}
            </button>
          </div>
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>
          {t('dataInput.importHelp')}
        </p>
        <input
          ref={dictFileInputRef}
          type="file"
          accept=".csv,.json"
          onChange={handleDictFileUpload}
          style={{ display: 'none' }}
        />
        {importedConditionSet && (
          <div style={{ marginTop: '12px', padding: '8px 12px', background: 'var(--color-success-bg)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem' }}>
            <strong>{t('dataInput.imported')}</strong>{' '}
            {importedConditionSet.conditions.map((c) => (
              <span key={c.name} style={{ marginRight: '12px' }}>
                <span style={{ fontWeight: 600 }}>{c.name}</span>
                {/* FIXME-BERT: c.keywords removed — kw count display broken until Phase 3 */}
                <span style={{ color: 'var(--color-text-secondary)' }}> ({(c as any).keywords?.length ?? 0} {t('dataInput.kw')})</span>
              </span>
            ))}
            {importedConditionSet.outcome && (
              <span>
                | {t('dataInput.outcomeLabel')}: <span style={{ fontWeight: 600 }}>{importedConditionSet.outcome.name}</span>
                {/* FIXME-BERT: outcome.keywords removed — kw count display broken until Phase 3 */}
                <span style={{ color: 'var(--color-text-secondary)' }}> ({(importedConditionSet.outcome as any).keywords?.length ?? 0} {t('dataInput.kw')})</span>
              </span>
            )}
          </div>
        )}
      </div>

      {/* === Section 0: Calibration Mode Selector === */}
      <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
        <h3 className="section-title">{t('dataInput.calibrationMode')}</h3>
      </div>

      {/* ── Text Corpus Input ── */}
        <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
          <h3 className="section-title">{t('dataInput.textCorpus')}</h3>

          {/* Mode toggle */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <button
              className={`btn ${textInputMode === 'paste' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTextInputMode('paste')}
              style={{ fontSize: '0.8125rem' }}
            >
              {t('dataInput.pasteText')}
            </button>
            <button
              className={`btn ${textInputMode === 'upload' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTextInputMode('upload')}
              style={{ fontSize: '0.8125rem' }}
            >
              {t('dataInput.uploadFile')}
            </button>
          </div>

          {textInputMode === 'paste' ? (
            <div>
              <div style={{ display: 'flex', gap: '12px', marginBottom: '8px', alignItems: 'center' }}>
                <label className="label" style={{ marginBottom: 0 }}>{t('dataInput.format')}</label>
                <select
                  className="input"
                  value={pasteFormat}
                  onChange={(e) => setPasteFormat(e.target.value as any)}
                  style={{ width: 120 }}
                >
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                  <option value="txt">{t('dataInput.formatPlainText')}</option>
                </select>
                <button className="btn btn-secondary" onClick={handleParsePaste} style={{ fontSize: '0.8125rem', marginLeft: 'auto' }}>
                  {t('dataInput.parseText')}
                </button>
              </div>
              <textarea
                className="input input-mono"
                rows={8}
                value={pasteContent}
                onChange={(e) => setPasteContent(e.target.value)}
                placeholder={
                  pasteFormat === 'csv'
                    ? t('dataInput.pastePlaceholderCsv')
                    : pasteFormat === 'json'
                      ? t('dataInput.pastePlaceholderJson')
                      : t('dataInput.pastePlaceholderTxt')
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
                accept=".csv,.json,.txt,.xlsx,.xls"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                {t('dataInput.dropHere')}
              </p>
              <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                {t('dataInput.orClickBrowse')}
              </p>
            </div>
          )}

          {/* Text preview */}
          {texts.length > 0 && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                  {texts.length} {t('dataInput.casesLoaded')}
                </span>
              </div>
              <div className="table-container" style={{ maxHeight: 200, overflowY: 'auto' }}>
                <table style={{ fontSize: '0.75rem' }}>
                  <thead>
                    <tr>
                      <th>{t('dataInput.id')}</th>
                      <th>{t('dataInput.textTruncated')}</th>
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
                          {t('dataInput.andMoreCases', texts.length - 20)}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

      {/* ── Prototype Text Input (Optional) ── */}
        <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
          <h3 className="section-title">{t('dataInput.prototypeTitle')}</h3>

          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>
            {t('dataInput.prototypeFormatHelp')}
          </p>

          <div style={{ display: 'flex', gap: '12px', marginBottom: '8px', alignItems: 'center' }}>
            <button
              className={`btn ${textInputMode === 'paste' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTextInputMode('paste')}
              style={{ fontSize: '0.8125rem' }}
            >
              {t('dataInput.parseCsv')}
            </button>
            <button
              className={`btn ${textInputMode === 'upload' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTextInputMode('upload')}
              style={{ fontSize: '0.8125rem' }}
            >
              {t('dataInput.uploadFile')}
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleParseProtoCSV}
              style={{ fontSize: '0.8125rem', marginLeft: 'auto' }}
            >
              {t('dataInput.parseProtoCsv')}
            </button>
          </div>

          {textInputMode === 'paste' ? (
            <textarea
              className="input input-mono"
              rows={8}
              value={protoPasteContent}
              onChange={(e) => setProtoPasteContent(e.target.value)}
              placeholder={t('dataInput.prototypePlaceholder')}
              style={{ resize: 'vertical', fontSize: '0.8125rem' }}
            />
          ) : (
            <div
              onDrop={handleProtoDrop}
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
                accept=".csv"
                onChange={handleProtoFileUpload}
                style={{ display: 'none' }}
              />
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                {t('dataInput.dropProtoFile')}
              </p>
              <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                {t('dataInput.orClickBrowse')}
              </p>
            </div>
          )}

          {/* Prototype text case preview */}
          {textCases.length > 0 && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                  {textCases.length} {t('dataInput.casesLoaded')}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                  {t('dataInput.outcome0')}: {textCases.filter((c) => c.outcome === 0).length} | {t('dataInput.outcome1')}: {textCases.filter((c) => c.outcome === 1).length}
                </span>
              </div>
              <div className="table-container" style={{ maxHeight: 200, overflowY: 'auto' }}>
                <table style={{ fontSize: '0.75rem' }}>
                  <thead>
                    <tr>
                      <th>{t('dataInput.id')}</th>
                      <th>{t('dataInput.textTruncated')}</th>
                      <th>{t('dataInput.outcomeLabel')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {textCases.slice(0, 20).map((t, i) => (
                      <tr key={i}>
                        <td className="mono">{t.text_id}</td>
                        <td style={{ maxWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {t.text.substring(0, 80)}{t.text.length > 80 ? '...' : ''}
                        </td>
                        <td style={{ textAlign: 'center', fontWeight: 600, color: t.outcome === 1 ? 'var(--color-success)' : 'var(--color-error)' }}>
                          {t.outcome}
                        </td>
                      </tr>
                    ))}
                    {textCases.length > 20 && (
                      <tr>
                        <td colSpan={3} style={{ textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                          {t('dataInput.andMoreCases', textCases.length - 20)}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

      {/* Distribution plot (appears after calibration, shared across modes) */}
      {state.fuzzyData && (
        <div style={{ marginBottom: '16px' }}>
          <DistributionPlot fuzzyData={state.fuzzyData} height={300} />
        </div>
      )}

      {/* ── Keyword mode: Condition Set YAML Editor ── */}
      {true && (
        <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
          <h3 className="section-title">{t('dataInput.conditionSetYaml')}</h3>

          {/* Domain picker */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <label className="label" style={{ marginBottom: 0 }}>{t('dataInput.domainPreset')}</label>
            <select
              className="input"
              style={{ width: 180 }}
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value as TextDomain)}
            >
              {DOMAIN_PRESETS.map((d) => (
                <option key={d} value={d}>{t('dataInput.domainLabels.' + d)}</option>
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
      )}

      {/* ── Prototype mode: Prototype Editor ── */}
      {true && (
        <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="section-title" style={{ marginBottom: 0, borderBottom: 'none', paddingBottom: 0 }}>
              {t('dataInput.prototypeEditor')}
            </h3>
            <button className="btn btn-secondary" onClick={addProtoCondition} style={{ fontSize: '0.8125rem' }}>
              {t('dataInput.addCondition')}
            </button>
          </div>

          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
            {t('dataInput.prototypeHelp')}
          </p>

          {/* Domain picker (shared for all prototype conditions) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <label className="label" style={{ marginBottom: 0 }}>{t('dataInput.domainPreset')}</label>
            <select
              className="input"
              style={{ width: 180 }}
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value as TextDomain)}
            >
              {DOMAIN_PRESETS.map((d) => (
                <option key={d} value={d}>{t('dataInput.domainLabels.' + d)}</option>
              ))}
            </select>
          </div>

          {/* Condition rows */}
          {protoConditions.map((row, index) => (
            <div
              key={row.id}
              style={{
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: '12px',
                marginBottom: '12px',
                background: 'var(--color-bg-input)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                  {t('dataInput.conditionN', index + 1)}
                </span>
                <button
                  className="btn btn-secondary"
                  onClick={() => removeProtoCondition(index)}
                  style={{ fontSize: '0.75rem', padding: '2px 8px' }}
                  disabled={protoConditions.length <= 1}
                  title={t('dataInput.removeCondition')}
                >
                  x
                </button>
              </div>

              <div style={{ display: 'flex', gap: '12px', marginBottom: '8px' }}>
                <div style={{ flex: 1 }}>
                  <label className="label" style={{ fontSize: '0.75rem' }}>{t('dataInput.name')}</label>
                  <input
                    className="input input-mono"
                    style={{ width: '100%' }}
                    value={row.name}
                    onChange={(e) => updateProtoCondition(index, 'name', e.target.value)}
                    placeholder={t('dataInput.namePlaceholder')}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="label" style={{ fontSize: '0.75rem' }}>{t('dataInput.displayName')}</label>
                  <input
                    className="input"
                    style={{ width: '100%' }}
                    value={row.displayName}
                    onChange={(e) => updateProtoCondition(index, 'displayName', e.target.value)}
                    placeholder={t('dataInput.displayNamePlaceholder')}
                  />
                </div>
              </div>

              <div>
                <label className="label" style={{ fontSize: '0.75rem' }}>
                  {t('dataInput.prototypeTextsLabel')}
                </label>
                <textarea
                  className="input input-mono"
                  rows={4}
                  value={row.prototypesText}
                  onChange={(e) => updateProtoCondition(index, 'prototypesText', e.target.value)}
                  placeholder={t('dataInput.prototypeTextsPlaceholder')}
                  style={{ resize: 'vertical', fontSize: '0.75rem', lineHeight: 1.5 }}
                  spellCheck={false}
                />
              </div>
            </div>
          ))}

          {/* Generated condition set preview */}
          {protoConditions.some((r) => r.name.trim() !== '') && (
            <div style={{ marginTop: '12px', padding: '8px 12px', background: 'var(--color-bg-input)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
              <strong>{t('dataInput.generatedConditionSet')}</strong>{' '}
              {t('dataInput.conditionCount', protoConditions.filter((r) => r.name.trim() !== '').length)}{' '}
              {t('dataInput.totalText')}{' '}
              {t('dataInput.prototypeCount', protoConditions
                .filter((r) => r.name.trim() !== '')
                .reduce((sum, r) => sum + parsePrototypeTexts(r.prototypesText).length, 0))}{' '}
              {t('dataInput.outcomePassthrough')}
            </div>
          )}
        </div>
      )}

      {/* === Validation / Status Message === */}
      {validationMessage && (
        <div
          className="card"
          style={{
            padding: '12px 16px',
            marginBottom: '16px',
            fontSize: '0.8125rem',
            borderColor:
              validationMessage.includes('Error') || validationMessage.includes('fail') ||
              validationMessage.includes('错误') || validationMessage.includes('失败')
                ? 'var(--color-error)'
                : 'var(--color-success)',
            background:
              validationMessage.includes('Error') || validationMessage.includes('fail') ||
              validationMessage.includes('错误') || validationMessage.includes('失败')
                ? 'var(--color-error-bg)'
                : 'var(--color-success-bg)',
            color:
              validationMessage.includes('Error') || validationMessage.includes('fail') ||
              validationMessage.includes('错误') || validationMessage.includes('失败')
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
          disabled={isRunning || texts.length === 0}
        >
          {isRunning ? t('dataInput.calibrating') : t('dataInput.calibrateBtn')}
        </button>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleRunPipeline}
          disabled={isRunning || texts.length === 0}
        >
          {isRunning ? t('dataInput.running') : t('dataInput.runPipelineBtn')}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleReset}
        >
          {t('dataInput.resetBtn')}
        </button>
      </div>
    </div>
  );
}
