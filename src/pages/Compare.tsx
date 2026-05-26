/**
 * Compare (P1-7)
 *
 * Parameter Comparison / A/B Analysis page.
 * Allows loading two saved snapshots and comparing their:
 * - Parameter diffs (calibration, analysis, variant groups)
 * - Result diffs (solutions, truth table, necessity)
 */

import React, { useState, useMemo } from 'react';
import ParamDiffTable, { computeParamDiffs } from '../components/ParamDiffTable';
import {
  CompareView,
  ComparisonSummary,
} from '../components/CompareView';
import {
  loadSnapshot,
  listSnapshots,
  clearSnapshot,
  swapSnapshots,
} from '../utils/snapshotStorage';
import { useT } from '../i18n/I18nContext';
import type { ParameterSnapshot, ComparisonReport } from '../types/qca';
import './Compare.css';

export default function Compare() {
  const t = useT();

  // Read current snapshot list
  const [snapshotList, setSnapshotList] = useState(() => listSnapshots());

  // Selected snapshot IDs
  const [selectedIdA, setSelectedIdA] = useState<string>(() => {
    const list = listSnapshots();
    return list.find((s) => s.label === 'a')?.id ?? '';
  });
  const [selectedIdB, setSelectedIdB] = useState<string>(() => {
    const list = listSnapshots();
    return list.find((s) => s.label === 'b')?.id ?? '';
  });

  // Loaded snapshots
  const snapA: ParameterSnapshot | null = useMemo(
    () => loadSnapshot('a'),
    [snapshotList]
  );
  const snapB: ParameterSnapshot | null = useMemo(
    () => loadSnapshot('b'),
    [snapshotList]
  );

  const hasBothSnapshots = snapA !== null && snapB !== null;

  const refreshList = () => setSnapshotList(listSnapshots());

  const handleSwap = () => {
    swapSnapshots();
    refreshList();
    const list = listSnapshots();
    setSelectedIdA(list.find((s) => s.label === 'a')?.id ?? '');
    setSelectedIdB(list.find((s) => s.label === 'b')?.id ?? '');
  };

  const handleClear = (label: 'a' | 'b') => {
    clearSnapshot(label);
    refreshList();
    if (label === 'a') setSelectedIdA('');
    else setSelectedIdB('');
  };

  // ── Comparison Report ──
  const report: ComparisonReport | null = useMemo(() => {
    if (!snapA || !snapB) return null;

    const rawFormula = snapA.result.solutions?.complex?.formula ?? '';
    const protoFormula = snapB.result.solutions?.complex?.formula ?? '';
    const rawConsistency = snapA.result.solutions?.complex?.solution_consistency ?? 0;
    const protoConsistency = snapB.result.solutions?.complex?.solution_consistency ?? 0;
    const rawCoverage = snapA.result.solutions?.complex?.solution_coverage ?? 0;
    const protoCoverage = snapB.result.solutions?.complex?.solution_coverage ?? 0;

    // Necessity diffs
    const rawNecessaryMap: Record<string, boolean> = {};
    for (const c of snapA.result.necessity?.conditions ?? []) {
      rawNecessaryMap[c.condition_name] = c.is_necessary;
    }
    const protoNecessaryMap: Record<string, boolean> = {};
    for (const c of snapB.result.necessity?.conditions ?? []) {
      protoNecessaryMap[c.condition_name] = c.is_necessary;
    }
    const allNames = [...new Set([...Object.keys(rawNecessaryMap), ...Object.keys(protoNecessaryMap)])];
    const conditionChanges = allNames
      .filter((name) => rawNecessaryMap[name] !== protoNecessaryMap[name])
      .map((name) => ({
        name,
        necessaryInA: rawNecessaryMap[name] ?? false,
        necessaryInB: protoNecessaryMap[name] ?? false,
      }));

    // Truth table diffs
    const rowsA = snapA.result.truth_table?.n_cases ?? snapA.result.truth_table?.rows?.length ?? 0;
    const rowsB = snapB.result.truth_table?.n_cases ?? snapB.result.truth_table?.rows?.length ?? 0;
    const configsA = snapA.result.truth_table?.rows?.map((r) => r.config_label).join('|') ?? '';
    const configsB = snapB.result.truth_table?.rows?.map((r) => r.config_label).join('|') ?? '';

    return {
      generatedAt: new Date().toISOString(),
      snapshotA: { id: snapA.id, name: snapA.name, timestamp: snapA.timestamp },
      snapshotB: { id: snapB.id, name: snapB.name, timestamp: snapB.timestamp },
      paramDiffs: [], // computed by ParamDiffTable
      resultDiffs: {
        solutionDiff: {
          formulaSame: rawFormula === protoFormula,
          consistencyDelta: protoConsistency - rawConsistency,
          coverageDelta: protoCoverage - rawCoverage,
        },
        necessityDiff: {
          necessaryConditionsChanged: conditionChanges.length > 0,
          conditionChanges,
        },
        truthTableDiff: {
          rowCountDelta: rowsB - rowsA,
          configurationsChanged: configsA !== configsB,
        },
      },
    };
  }, [snapA, snapB]);

  const handleExportReport = () => {
    if (!report || !snapA || !snapB) return;
    const fullReport = {
      ...report,
      paramDiffs: computeParamDiffs(snapA, snapB),
    };
    const json = JSON.stringify(fullReport, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `qca-comparison-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="compare-page">
      <div className="page-header">
        <h2 className="page-title">{t('compare.title')}</h2>
        <p className="page-subtitle">{t('compare.subtitle')}</p>
      </div>

      {/* ── Snapshot Selector Panel ── */}
      <div className="compare-selector-panel">
        {/* Slot A */}
        <div className="compare-slot">
          <label className="compare-slot-label">{t('compare.snapshotA')}</label>
          {snapA ? (
            <div className="compare-slot-info">
              <span className="compare-slot-name">{snapA.name}</span>
              <span className="compare-slot-meta">
                {snapA.conditionSet?.conditions?.length ?? 0} {t('compare.conditions')}
                {' · '}
                {snapA.result?.fuzzy_data?.membership?.length ?? 0} {t('compare.cases')}
              </span>
              <span className="compare-slot-meta">
                {new Date(snapA.timestamp).toLocaleString()}
              </span>
            </div>
          ) : (
            <div className="compare-slot-empty">{t('compare.selectSnapshot')}</div>
          )}
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.75rem', marginTop: '8px' }}
            onClick={() => handleClear('a')}
            disabled={!snapA}
          >
            {t('compare.clear')}
          </button>
        </div>

        {/* Swap */}
        <button
          className="btn btn-secondary"
          style={{ alignSelf: 'center', fontSize: '0.8125rem' }}
          onClick={handleSwap}
          disabled={!hasBothSnapshots}
          title={t('compare.swap')}
        >
          {t('compare.swap')}
        </button>

        {/* Slot B */}
        <div className="compare-slot">
          <label className="compare-slot-label">{t('compare.snapshotB')}</label>
          {snapB ? (
            <div className="compare-slot-info">
              <span className="compare-slot-name">{snapB.name}</span>
              <span className="compare-slot-meta">
                {snapB.conditionSet?.conditions?.length ?? 0} {t('compare.conditions')}
                {' · '}
                {snapB.result?.fuzzy_data?.membership?.length ?? 0} {t('compare.cases')}
              </span>
              <span className="compare-slot-meta">
                {new Date(snapB.timestamp).toLocaleString()}
              </span>
            </div>
          ) : (
            <div className="compare-slot-empty">{t('compare.selectSnapshot')}</div>
          )}
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.75rem', marginTop: '8px' }}
            onClick={() => handleClear('b')}
            disabled={!snapB}
          >
            {t('compare.clear')}
          </button>
        </div>
      </div>

      {/* ── Empty state ── */}
      {!hasBothSnapshots && (
        <div className="compare-empty">
          <p style={{ fontSize: '0.875rem', marginBottom: '8px' }}>{t('compare.noSnapshots')}</p>
          <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
            {t('compare.noSnapshotsHint')}
          </p>
        </div>
      )}

      {/* ── Comparison Content ── */}
      {hasBothSnapshots && snapA && snapB && report && (
        <>
          {/* Export button */}
          <div className="compare-toolbar">
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.8125rem' }}
              onClick={handleExportReport}
            >
              {t('compare.exportReport')}
            </button>
          </div>

          {/* Parameter Diffs */}
          <div className="card" style={{ padding: '16px', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '12px' }}>
              {t('compare.paramDiffs')}
            </h3>
            <ParamDiffTable snapshotA={snapA} snapshotB={snapB} />
          </div>

          {/* Summary */}
          <ComparisonSummary raw={snapA.result} prototype={snapB.result} t={(path: string, ...args: any[]) => t(path, ...args)} />

          {/* Side-by-side compare view */}
          <div style={{ marginTop: '20px' }}>
            <CompareView raw={snapA.result} prototype={snapB.result} t={(path: string, ...args: any[]) => t(path, ...args)} />
          </div>
        </>
      )}
    </div>
  );
}
