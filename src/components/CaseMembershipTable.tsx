/**
 * CaseMembershipTable — displays every text case with its membership scores
 * per condition in a sortable, filterable, expandable interactive table.
 *
 * Features:
 * - Sortable columns (Case ID, Text, Conditions, Outcome)
 * - Text search filter
 * - Condition-level min/max range filters (toggleable)
 * - Expandable rows showing full text
 * - Color-coded membership scores: red(0.0) → yellow(0.5) → green(1.0)
 * - Case count display
 * - Empty state when filters produce 0 results
 */

import React, { useMemo, useState, useCallback } from 'react';
import { useT } from '../i18n/I18nContext';
import type { MembershipDataJSON } from '../types/qca';

interface Props {
  data: MembershipDataJSON;
}

interface CaseRow {
  idx: number;
  caseId: string;
  text: string | null;
  scores: number[]; // [condition_0, ..., condition_N-1, outcome]
}

function scoreColor(score: number): string {
  // red(0.0) → yellow(0.5) → green(1.0)
  const clamped = Math.max(0, Math.min(1, score));
  let r: number, g: number, b: number;
  if (clamped < 0.5) {
    // red(255,80,80) → yellow(255,220,80)
    const t = clamped / 0.5;
    r = 255;
    g = Math.round(80 + t * (220 - 80));
    b = 80;
  } else {
    // yellow(255,220,80) → green(80,180,80)
    const t = (clamped - 0.5) / 0.5;
    r = Math.round(255 - t * (255 - 80));
    g = Math.round(220 - t * (220 - 180));
    b = 80;
  }
  return `rgba(${r},${g},${b},0.25)`;
}

type SortKey = 'caseId' | 'text' | 'outcome' | number; // number means condition index

export default function CaseMembershipTable({ data }: Props) {
  const t = useT();

  // ── State ──
  const [searchText, setSearchText] = useState('');
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [expandedRowIdx, setExpandedRowIdx] = useState<number | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Per-condition range filters: [min, max], initialized to [0.0, 1.0]
  const numConditions = data.condition_names?.length ?? 0;
  const [rangeFilters, setRangeFilters] = useState<[number, number][]>(() =>
    Array.from({ length: numConditions }, () => [0.0, 1.0] as [number, number])
  );

  // Reset range filters when data changes (keyed by case count)
  const caseCountKey = data.membership?.length ?? 0;
  const conditionCountKey = numConditions;
  React.useEffect(() => {
    setRangeFilters(
      Array.from({ length: numConditions }, () => [0.0, 1.0] as [number, number])
    );
    setExpandedRowIdx(null);
  }, [caseCountKey, conditionCountKey]);

  // ── Build rows ──
  const allRows = useMemo<CaseRow[]>(() => {
    const membership = data.membership ?? [];
    const caseIds = data.case_ids ?? [];
    const texts = data.texts ?? [];

    const rowCount = Math.min(membership.length, caseIds.length);
    return membership.slice(0, rowCount).map((scores, i) => ({
      idx: i,
      caseId: caseIds[i] ?? `Case ${i + 1}`,
      text: texts[i] ?? null,
      scores: [...scores],
    }));
  }, [data.membership, data.case_ids, data.texts]);

  // ── Filter + sort pipeline ──
  const rows = useMemo(() => {
    let filtered = allRows;

    // Filter by search text
    if (searchText.trim()) {
      const lower = searchText.trim().toLowerCase();
      filtered = filtered.filter(
        (r) =>
          r.caseId.toLowerCase().includes(lower) ||
          (r.text ?? '').toLowerCase().includes(lower)
      );
    }

    // Filter by condition ranges
    if (showFilters && numConditions > 0) {
      filtered = filtered.filter((r) => {
        for (let c = 0; c < numConditions; c++) {
          const score = r.scores[c] ?? 0;
          const [min, max] = rangeFilters[c] ?? [0, 1];
          if (score < min || score > max) return false;
        }
        return true;
      });
    }

    // Sort
    if (sortKey !== null) {
      filtered = [...filtered].sort((a, b) => {
        let va: number | string;
        let vb: number | string;

        if (sortKey === 'caseId') {
          va = a.caseId;
          vb = b.caseId;
        } else if (sortKey === 'text') {
          va = a.text ?? '';
          vb = b.text ?? '';
        } else if (sortKey === 'outcome') {
          va = a.scores[a.scores.length - 1] ?? 0;
          vb = b.scores[b.scores.length - 1] ?? 0;
        } else if (typeof sortKey === 'number') {
          va = a.scores[sortKey] ?? 0;
          vb = b.scores[sortKey] ?? 0;
        } else {
          return 0;
        }

        if (typeof va === 'number' && typeof vb === 'number') {
          return sortDir === 'asc' ? va - vb : vb - va;
        }
        if (typeof va === 'string' && typeof vb === 'string') {
          return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
        }
        return 0;
      });
    }

    return filtered;
  }, [allRows, searchText, showFilters, rangeFilters, sortKey, sortDir, numConditions]);

  // ── Sort handlers ──
  const handleSort = useCallback(
    (key: SortKey) => {
      if (sortKey === key) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
      } else {
        setSortKey(key);
        setSortDir('asc');
      }
    },
    [sortKey]
  );

  const sortIcon = (key: SortKey) => {
    if (sortKey !== key) return ' ↕';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  };

  // ── Range filter handlers ──
  const handleRangeChange = useCallback(
    (condIdx: number, bound: 0 | 1, rawVal: string) => {
      const val = parseFloat(rawVal);
      setRangeFilters((prev) => {
        const next = prev.map((r) => [...r] as [number, number]);
        if (!isNaN(val)) {
          next[condIdx][bound] = Math.max(0, Math.min(1, val));
        }
        return next;
      });
    },
    []
  );

  // ── Outcome column header ──
  const outcomeName = data.outcome_name || 'Outcome';

  return (
    <div className="case-table-wrapper">
      {/* ── Search + Filter Toggle ── */}
      <div className="case-search-bar">
        <input
          type="text"
          className="case-search-input"
          placeholder={t('results.caseSearch')}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{
            flex: 1,
            padding: '6px 10px',
            fontSize: '0.8125rem',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
          }}
        />
        <button
          className={`btn ${showFilters ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setShowFilters(!showFilters)}
          style={{ fontSize: '0.8125rem', padding: '6px 12px' }}
        >
          {t('results.caseFilterToggle')}
        </button>
      </div>

      {/* ── Case count ── */}
      <div className="case-count-info">
        {t('results.caseCount', rows.length)}
      </div>

      {/* ── Table or Empty State ── */}
      {rows.length === 0 ? (
        <div className="case-no-results">{t('results.caseNoMatch')}</div>
      ) : (
        <div className="table-container">
          <table style={{ fontSize: '0.8125rem' }}>
            <thead>
              <tr>
                <th
                  onClick={() => handleSort('caseId')}
                  style={{ cursor: 'pointer', whiteSpace: 'nowrap', minWidth: '100px' }}
                >
                  {t('results.caseId')}{sortIcon('caseId')}
                </th>
                <th
                  onClick={() => handleSort('text')}
                  style={{ cursor: 'pointer', minWidth: '200px' }}
                >
                  {t('results.caseText')}{sortIcon('text')}
                </th>
                {data.condition_names.slice(0, numConditions).map((condName, ci) => (
                  <th
                    key={ci}
                    onClick={() => handleSort(ci)}
                    style={{ cursor: 'pointer', whiteSpace: 'nowrap', minWidth: '80px' }}
                  >
                    {condName}{sortIcon(ci)}
                  </th>
                ))}
                <th
                  onClick={() => handleSort('outcome')}
                  style={{ cursor: 'pointer', whiteSpace: 'nowrap', minWidth: '80px' }}
                >
                  {outcomeName}{sortIcon('outcome')}
                </th>
              </tr>

              {/* ── Range Filter Row ── */}
              {showFilters && (
                <tr className="case-filter-row">
                  <th></th>
                  <th></th>
                  {Array.from({ length: numConditions }).map((_, ci) => (
                    <th key={ci}>
                      <div style={{ display: 'flex', gap: '4px', justifyContent: 'center' }}>
                        <input
                          type="number"
                          className="case-filter-input"
                          min={0}
                          max={1}
                          step={0.05}
                          value={rangeFilters[ci]?.[0] ?? 0}
                          onChange={(e) => handleRangeChange(ci, 0, e.target.value)}
                          title={t('results.caseFilterMin')}
                          placeholder={t('results.caseFilterMin')}
                        />
                        <span style={{ fontSize: '0.65rem', alignSelf: 'center', color: 'var(--color-text-secondary)' }}>–</span>
                        <input
                          type="number"
                          className="case-filter-input"
                          min={0}
                          max={1}
                          step={0.05}
                          value={rangeFilters[ci]?.[1] ?? 1}
                          onChange={(e) => handleRangeChange(ci, 1, e.target.value)}
                          title={t('results.caseFilterMax')}
                          placeholder={t('results.caseFilterMax')}
                        />
                      </div>
                    </th>
                  ))}
                  <th></th>
                </tr>
              )}
            </thead>
            <tbody>
              {rows.map((row) => {
                const isExpanded = expandedRowIdx === row.idx;
                const outcomeScore = row.scores[row.scores.length - 1] ?? 0;

                return (
                  <React.Fragment key={row.idx}>
                    <tr
                      onClick={() =>
                        setExpandedRowIdx(isExpanded ? null : row.idx)
                      }
                      style={{
                        cursor: 'pointer',
                        background: isExpanded ? 'rgba(59, 130, 246, 0.04)' : undefined,
                      }}
                    >
                      <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
                        {row.caseId}
                      </td>
                      <td className="case-text-preview">
                        {row.text ? row.text : <span style={{ fontStyle: 'italic', color: 'var(--color-text-secondary)' }}>{t('results.caseNoText')}</span>}
                      </td>
                      {row.scores.slice(0, numConditions).map((score, si) => (
                        <td
                          key={si}
                          className="case-score-cell"
                          style={{ background: scoreColor(score) }}
                        >
                          {score.toFixed(3)}
                        </td>
                      ))}
                      <td
                        className="case-score-cell"
                        style={{ background: scoreColor(outcomeScore), fontWeight: 600 }}
                      >
                        {outcomeScore.toFixed(3)}
                      </td>
                    </tr>

                    {/* ── Expanded row with full text ── */}
                    {isExpanded && (
                      <tr className="case-expanded-row">
                        <td colSpan={2 + numConditions + 1}>
                          <div className="case-expanded-content">
                            <div
                              style={{
                                fontSize: '0.7rem',
                                color: 'var(--color-text-secondary)',
                                marginBottom: '6px',
                                fontWeight: 600,
                                textTransform: 'uppercase',
                                letterSpacing: '0.04em',
                              }}
                            >
                              {t('results.caseExpandedLabel', row.caseId)}
                            </div>
                            <div className="case-expanded-text">
                              {row.text ?? t('results.caseNoText')}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
