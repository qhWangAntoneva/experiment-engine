/**
 * Truth Table Viewer — renders the QCA truth table as a sortable/filterable
 * data table with visual indicators for frequency, consistency, and outcome.
 */

import React, { useMemo, useState } from 'react';
import type { TruthTableJSON } from '../types/qca';

interface Props {
  truthTable: TruthTableJSON;
}

export default function TruthTableViewer({ truthTable }: Props) {
  const [showExcluded, setShowExcluded] = useState(false);
  const [sortKey, setSortKey] = useState<keyof typeof truthTable.rows[0] | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const rows = useMemo(() => {
    let filtered = showExcluded
      ? truthTable.rows
      : truthTable.rows.filter((r) => r.included);

    if (sortKey) {
      filtered = [...filtered].sort((a, b) => {
        const va = a[sortKey];
        const vb = b[sortKey];
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
  }, [truthTable.rows, showExcluded, sortKey, sortDir]);

  const handleSort = (key: keyof typeof truthTable.rows[0]) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sortIcon = (key: string) => {
    if (sortKey !== key) return ' ↕';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  };

  return (
    <div style={{ width: '100%' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
        }}
      >
        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
          Truth Table ({truthTable.condition_names.join(', ')} → {truthTable.outcome_name})
        </span>
        <label style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={showExcluded}
            onChange={(e) => setShowExcluded(e.target.checked)}
          />
          Show excluded rows
        </label>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th onClick={() => handleSort('config_label')} style={{ cursor: 'pointer' }}>
                Config{sortIcon('config_label')}
              </th>
              <th onClick={() => handleSort('frequency')} style={{ cursor: 'pointer' }}>
                N{sortIcon('frequency')}
              </th>
              <th onClick={() => handleSort('raw_consistency')} style={{ cursor: 'pointer' }}>
                Consistency{sortIcon('raw_consistency')}
              </th>
              <th>Outcome</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr
                key={idx}
                style={{
                  opacity: row.included ? 1 : 0.4,
                  background: row.outcome_value === 1 ? 'rgba(5, 150, 105, 0.04)' : undefined,
                }}
              >
                <td className="mono" style={{ fontWeight: 600 }}>
                  {row.config_label}
                </td>
                <td className="mono">{row.frequency.toFixed(1)}</td>
                <td className="mono">
                  <span
                    style={{
                      color:
                        row.raw_consistency >= truthTable.consistency_threshold
                          ? 'var(--color-success)'
                          : 'var(--color-error)',
                      fontWeight: 600,
                    }}
                  >
                    {row.raw_consistency.toFixed(3)}
                  </span>
                </td>
                <td>
                  <span
                    className={`badge ${row.outcome_value === 1 ? 'badge-success' : row.outcome_value === 0 ? 'badge-error' : 'badge-warning'}`}
                  >
                    {row.outcome_value === 1 ? '1' : '0'}
                  </span>
                </td>
                <td>
                  {row.included ? (
                    <span className="badge badge-success">included</span>
                  ) : (
                    <span className="badge badge-warning">excluded</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: '8px', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
        Thresholds: consistency &ge; {truthTable.consistency_threshold}, frequency &ge; {truthTable.frequency_threshold}
        {' | '}
        {truthTable.rows.length} rows total, {truthTable.rows.filter((r) => r.included).length} included,{' '}
        {truthTable.rows.filter((r) => r.included && r.outcome_value === 1).length} positive
      </div>
    </div>
  );
}
