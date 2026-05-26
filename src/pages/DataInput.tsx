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
import ShareLinkButton from '../components/ShareLinkButton';
import HelpTooltip from '../components/HelpTooltip';
import { getBuiltinTemplates } from '../services/templateService';
import { conditionSetToYaml } from '../utils/conditionSetToYaml';
import type {
  TextCorpusEntry,
  TextCase,
  ConditionSet,
  ConditionDefinition,
  ConceptPrototype,
  ScoringSource,
  TextDomain,
  QCAProjectProtoConditionRow,
} from '../types/qca';
import { CalibrationMethod, QCAVariant, DEFAULT_CONDITION_SET_YAML } from '../types/qca';
import './DataInput.css';


// ─── Sample cases CSV (30 cases, 5 domains, 6 per domain) ──────────────────

const SAMPLE_CSV_CONTENT = `text_id,domain,text,expected_outcome
1,dissatisfaction,"你们这服务太差了，去办证跑了五趟都没办成，窗口人员推诿踢皮球，我要打市长热线投诉你们",1
2,dissatisfaction,"工作人员态度极其恶劣，效率极低，一个简单的证明拖了一个月，我已经去纪委反映了",1
3,dissatisfaction,"为什么隔壁区能办我们这就不行？区别对待太不公平了，再不解决我就找媒体曝光",1
4,dissatisfaction,"今天去办了业务，工作人员态度还可以，虽然等了一会儿但总算办完了",0
5,dissatisfaction,"请问一下这个证明材料在哪里可以下载，大概需要多久办好",0
6,dissatisfaction,"整体感觉比以前好一些了，虽然还有提升空间，但已经进步不少",0
7,policy_demand,"建议政府尽快出台针对老旧小区加装电梯的补贴政策，我们全体居民强烈要求",1
8,policy_demand,"据统计数据显示其他城市已经实施了共享单车管理办法，我们这应该尽快参照",1
9,policy_demand,"我们社区老年人多，希望政府增加社区卫生服务站的人员经费投入",1
10,policy_demand,"我想咨询一下现在执行的购房补贴政策具体是什么条件",0
11,policy_demand,"随便了解一下，这个新政策什么时候开始实施",0
12,policy_demand,"目前政策挺好的，希望保持稳定不要频繁变动就行了",0
13,co_production,"我们社区居民愿意出钱出力，一起把垃圾分类这个事情做好，希望政府能组织协调",1
14,co_production,"我在环保领域工作多年，可以从专业角度提几点建议，配合你们一起完善方案",1
15,co_production,"大家齐心协力联合行动，我们楼栋全体住户都愿意参与社区绿化共建",1
16,co_production,"这是政府的事，我们老百姓管不了那么多，你们自己想办法处理",0
17,co_production,"我不太懂这些技术问题，你们专业人士看着办就行了",0
18,co_production,"我一个人来反映一下意见就可以了，不需要组织其他人一起",0
19,trust,"我对政府很放心，相信他们能公正处理好这件事，现在办事确实越来越透明了",1
20,trust,"工作人员非常专业，态度好有耐心，整个流程非常规范，我要给他们点赞",1
21,trust,"政府真心为老百姓着想，政策越来越人性化，办事比以前方便多了",1
22,trust,"政府没什么公信力，说要解决问题说了半年了也没见动静，完全不靠谱",0
23,trust,"办事人员连基本政策都解释不清楚，一问三不知，能力太差了",0
24,trust,"这里面肯定有猫腻，不按规矩办事，有关系的人就优先处理",0
25,gov_responsiveness,"反映问题后当天就有人联系我，三天内就办好了，效率非常高，处理很到位",1
26,gov_responsiveness,"整个处理过程都有短信通知，每一步都告知进展，办完还有回访电话",1
27,gov_responsiveness,"工作人员态度非常好，耐心解答，认真细致，办完后还主动跟进后续情况",1
28,gov_responsiveness,"反映了好几次问题，等了两个星期也没人回复，石沉大海一样",0
29,gov_responsiveness,"虽然有回应但都是敷衍，说什么正在处理中，实际上根本没有任何进展",0
30,gov_responsiveness,"办理后就没人管了，出了问题不知道找谁，没有任何后续跟进机制",0
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

let _protoRowIdCounter = 0;
function newProtoRow(name: string = '', displayName: string = '', prototypesText: string = ''): QCAProjectProtoConditionRow {
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
  rows: QCAProjectProtoConditionRow[],
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

  const {
    state,
    setTextCorpus,
    setTextCases: setTextCasesContext,
    setYamlContent: setYamlContentContext,
    setProtoConditions: setProtoConditionsContext,
  } = useQCAPipeline();
  const { initState } = usePyodide();
  const {
    runFullPipeline,
    runCalibrateOnly,
    loadCorpus,
    initBert,
    runEmbedCalibrate,
  } = useQCAWorkflow();
  // Phase 5 stubs: keyword import removed
  const importKeywords = async (..._args: any[]): Promise<any> => ({ conditions: [], outcome: null } as any);
  // Keyword dictionary export
  const exportKeywords = useCallback(
    async (conditionSet: ConditionSet, format: 'csv' | 'json'): Promise<Blob> => {
      if (format === 'json') {
        const json = JSON.stringify(conditionSet, null, 2);
        return new Blob([json], { type: 'application/json' });
      }
      const rows: string[] = ['condition,display_name,prototype_text,is_member,weight'];
      for (const cond of conditionSet.conditions) {
        if (cond.prototypes && cond.prototypes.length > 0) {
          for (const proto of cond.prototypes) {
            const escaped = proto.prototype_text.replace(/"/g, '""');
            rows.push(
              `${cond.name},${cond.display_name},"${escaped}",${proto.is_member},${proto.weight}`
            );
          }
        } else {
          rows.push(`${cond.name},${cond.display_name},,,`);
        }
      }
      return new Blob(['﻿' + rows.join('\n')], { type: 'text/csv;charset=utf-8' });
    },
    []
  );

  // ─── Form state ────────────────────────────────────────────────────

  // Text corpus state from pipeline context
  const texts = state.textCorpusEntries;
  const yamlContent = state.yamlContent;
  const textCases = state.textCases;
  const protoConditions = state.protoConditions;

  // Local UI state
  const [textInputMode, setTextInputMode] = useState<'upload' | 'paste'>('paste');
  const [pasteContent, setPasteContent] = useState('');
  const [pasteFormat, setPasteFormat] = useState<'csv' | 'json' | 'txt'>('csv');
  const [selectedDomain, setSelectedDomain] = useState<TextDomain>('dissatisfaction');

  // Prototype mode UI state
  const [protoPasteContent, setProtoPasteContent] = useState('');

  const [importedConditionSet, setImportedConditionSet] = useState<ConditionSet | null>(null);
  const dictFileInputRef = useRef<HTMLInputElement>(null);

  // ─── Export state ─────────────────────────────────────────────────────
  const [isExporting, setIsExporting] = useState(false);

  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isBertLoading, setIsBertLoading] = useState(false);
  const [isEmbedding, setIsEmbedding] = useState(false);

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
          setTextCorpus(entries);
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
      setTextCorpus(entries);
      setValidationMessage(t('dataInput.parsedCases', entries.length));
    } catch (err: any) {
      setValidationMessage(`${t('dataInput.parseError')}${err.message}`);
    }
  }, [pasteContent, pasteFormat, loadCorpus, t]);

  const handleYamlChange = useCallback((value: string) => {
    setYamlContentContext(value);
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
          const kwCount = cs.conditions.reduce(
            (sum: number, c: any) => sum + ((c as any).prototypes?.length ?? 0), 0
          );
          if (cs.outcome) {
            const outcomeKws = (cs.outcome as any).prototypes?.length ?? 0;
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
      const kwCount = importedConditionSet.conditions.reduce(
        (sum, c) => sum + ((c as any).prototypes?.length ?? 0), 0
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
        setTextCorpus(entries);
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
      setTextCasesContext(cases);
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
          setTextCasesContext(cases);
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
        setTextCasesContext(cases);
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
    (index: number, field: keyof QCAProjectProtoConditionRow, value: string) => {
      const next = [...state.protoConditions];
      next[index] = { ...next[index], [field]: value };
      setProtoConditionsContext(next);
    },
    [state.protoConditions]
  );

  const addProtoCondition = useCallback(() => {
    setProtoConditionsContext([...state.protoConditions, newProtoRow('', '')]);
  }, [state.protoConditions]);

  const removeProtoCondition = useCallback((index: number) => {
    if (state.protoConditions.length <= 1) return;
    setProtoConditionsContext(state.protoConditions.filter((_, i) => i !== index));
  }, [state.protoConditions]);

  const handleReset = useCallback(() => {
    handleParsePaste();
  }, [handleParsePaste]);

  const handleLoadSampleData = useCallback(async () => {
    try {
      const entries = await loadCorpus('sample_cases.csv', SAMPLE_CSV_CONTENT, 'csv');
      setTextCorpus(entries);

      // Find matching builtin template for the current domain
      const template = getBuiltinTemplates().find(t => t.domain === selectedDomain);
      if (template) {
        const qcaVariant = getQCAVariantFromSettings();
        const cs = {
          name: template.name,
          description: template.description,
          domain: template.domain,
          conditions: template.conditions,
          outcome: template.outcome,
          scoring_source: 'prototype' as const,
          qca_variant: qcaVariant,
        };
        setYamlContentContext(conditionSetToYaml(cs));
      }

      setValidationMessage(t('dataInput.sampleLoaded', entries.length, selectedDomain));
    } catch (err: any) {
      setValidationMessage(`${t('common.error')}: ${err.message}`);
    }
  }, [loadCorpus, setTextCorpus, selectedDomain, setYamlContentContext, t]);

  // ─── BERT handlers ─────────────────────────────────────────────────────

  const handleLoadBert = useCallback(async () => {
    setIsBertLoading(true);
    setValidationMessage(null);
    try {
      await initBert();
      setValidationMessage(t('dataInput.bertLoaded'));
    } catch (err: any) {
      setValidationMessage(`${t('common.error')}: ${err.message}`);
    } finally {
      setIsBertLoading(false);
    }
  }, [initBert, t]);

  const handleBertCalibrate = useCallback(async () => {
    if (texts.length === 0) {
      setValidationMessage(t('dataInput.noTextData'));
      return;
    }
    // Build condition set from YAML or imported
    const cs = importedConditionSet
      ? { ...importedConditionSet, qca_variant: importedConditionSet.qca_variant ?? getQCAVariantFromSettings() }
      : (yamlContent as any);

    setIsEmbedding(true);
    setValidationMessage(null);
    try {
      await runEmbedCalibrate({ texts, conditionSet: cs });
      setValidationMessage(t('dataInput.bertCalibrationComplete'));
    } catch (err: any) {
      setValidationMessage(`${t('dataInput.bertCalibrationFailed')}: ${err.message}`);
    } finally {
      setIsEmbedding(false);
    }
  }, [texts, yamlContent, importedConditionSet, runEmbedCalibrate, t]);

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
    importedConditionSet,
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
    importedConditionSet,
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

      <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h3 className="section-title" style={{ marginBottom: 0, borderBottom: 'none', paddingBottom: 0 }}>
            {t('dataInput.importExportTitle')}
          </h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <ShareLinkButton conditionSet={importedConditionSet} />
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
                <span style={{ color: 'var(--color-text-secondary)' }}> ({(c as any).prototypes?.length ?? 0} {t('dataInput.kw')})</span>
              </span>
            ))}
            {importedConditionSet.outcome && (
              <span>
                | {t('dataInput.outcomeLabel')}: <span style={{ fontWeight: 600 }}>{importedConditionSet.outcome.name}</span>
                <span style={{ color: 'var(--color-text-secondary)' }}> ({(importedConditionSet.outcome as any).prototypes?.length ?? 0} {t('dataInput.kw')})</span>
              </span>
            )}
          </div>
        )}
      </div>

      {/* === Section 0: Calibration Mode Selector === */}
      <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
        <h3 className="section-title">{t('dataInput.calibrationMode')}</h3>
      </div>

      {/* === BERT Embedding Controls === */}
      <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
        <h3 className="section-title">{t('dataInput.bertCalibration')}</h3>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
          {t('dataInput.bertDescription')}
        </p>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            className="btn btn-secondary"
            onClick={handleLoadBert}
            disabled={isBertLoading || isRunning}
            style={{ fontSize: '0.8125rem' }}
          >
            {isBertLoading ? t('dataInput.bertLoadingBtn') : t('dataInput.bertLoadBtn')}
          </button>
          {state.bertStatus === 'ready' && (
            <span style={{ fontSize: '0.75rem', color: 'var(--color-success)', fontWeight: 600 }}>
              {t('dataInput.bertModelReady')}
            </span>
          )}
          {state.bertStatus === 'loading' && (
            <span style={{ fontSize: '0.75rem', color: 'var(--color-warning)' }}>
              {t('dataInput.bertLoading')}
            </span>
          )}
          {state.bertStatus === 'error' && (
            <span style={{ fontSize: '0.75rem', color: 'var(--color-error)' }}>
              {t('dataInput.bertLoadFailed')}{state.bertMessage}
            </span>
          )}
          {state.bertStatus === 'unloaded' && (
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
              {t('dataInput.bertUnloaded')}
            </span>
          )}
          <button
            className="btn btn-primary"
            onClick={handleBertCalibrate}
            disabled={isEmbedding || isRunning || texts.length === 0 || state.bertStatus !== 'ready'}
            style={{ fontSize: '0.8125rem', marginLeft: 'auto' }}
          >
            {isEmbedding ? t('dataInput.bertCalibratingBtn') : t('dataInput.bertCalibrateBtn')}
          </button>
        </div>
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
          <div style={{ display: 'flex', gap: '8px', marginTop: '4px', marginBottom: '12px' }}>
            <button
              className="btn btn-outline"
              onClick={handleLoadSampleData}
              disabled={isRunning || isBertLoading}
              title={t('dataInput.sampleDataTooltip')}
              style={{ fontSize: '0.8125rem' }}
            >
              {t('dataInput.sampleDataBtn')}
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
          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
            <strong>Weight:</strong> Each prototype has a weight (default 1.0) that controls its contribution.
            <HelpTooltip text={t('help.weight')} />
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
                  <HelpTooltip text={t('help.prototypeText')} placement="right" />
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
          disabled={isRunning || isBertLoading || isEmbedding || texts.length === 0}
        >
          {isRunning ? t('dataInput.calibrating') : t('dataInput.calibrateBtn')}
        </button>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleRunPipeline}
          disabled={isRunning || isBertLoading || isEmbedding || texts.length === 0}
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
