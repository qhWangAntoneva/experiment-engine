/**
 * Solution Viewer — displays one or all QCA solution types (complex,
 * parsimonious, intermediate) as formula strings with term-level metrics.
 */

import React from 'react';
import type { QCASolution, QCASolutions } from '../types/qca';

interface Props {
  solutions: QCASolutions;
  showAll?: boolean;
}

function SolutionCard({ solution, label }: { solution: QCASolution; label: string }) {
  if (!solution || solution.terms.length === 0) {
    return (
      <div className="card" style={{ padding: '16px', marginBottom: '12px' }}>
        <h4 style={{ marginBottom: '8px', fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
          {label} Solution
        </h4>
        <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
          No solution found (possibly insufficient consistent configurations).
        </p>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: '16px', marginBottom: '12px' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '12px',
        }}
      >
        <h4 style={{ fontSize: '0.875rem', fontWeight: 600 }}>
          {label} Solution
        </h4>
        <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem' }}>
          <span>
            <span style={{ color: 'var(--color-text-secondary)' }}>Consistency: </span>
            <span className="mono" style={{ fontWeight: 600 }}>
              {solution.solution_consistency.toFixed(3)}
            </span>
          </span>
          <span>
            <span style={{ color: 'var(--color-text-secondary)' }}>Coverage: </span>
            <span className="mono" style={{ fontWeight: 600 }}>
              {solution.solution_coverage.toFixed(3)}
            </span>
          </span>
        </div>
      </div>

      {/* Formula */}
      <div
        className="mono"
        style={{
          background: 'var(--color-accent-light)',
          color: 'var(--color-accent)',
          padding: '8px 12px',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.8125rem',
          marginBottom: '12px',
          wordBreak: 'break-all',
          overflowX: 'auto',
          whiteSpace: 'pre-wrap',
        }}
      >
        {solution.formula}
      </div>

      {/* Individual terms */}
      <div className="table-container">
        <table style={{ fontSize: '0.8125rem' }}>
          <thead>
            <tr>
              <th>Term</th>
              <th>Consistency</th>
              <th>Raw Coverage</th>
              <th>Unique Coverage</th>
            </tr>
          </thead>
          <tbody>
            {solution.terms.map((term, idx) => (
              <tr key={idx}>
                <td className="mono" style={{ fontWeight: 600 }}>
                  {term.label}
                </td>
                <td className="mono">{term.consistency.toFixed(3)}</td>
                <td className="mono">{term.raw_coverage.toFixed(3)}</td>
                <td className="mono">{term.unique_coverage.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function SolutionViewer({ solutions, showAll = false }: Props) {
  const types: Array<{ key: keyof QCASolutions; label: string }> = [
    { key: 'complex', label: 'Complex' },
    { key: 'parsimonious', label: 'Parsimonious' },
    { key: 'intermediate', label: 'Intermediate' },
  ];

  // By default, show only the best available solution (parsimonious > intermediate > complex)
  const visibleTypes = showAll
    ? types
    : types.filter((t) => solutions[t.key]).slice(0, 1);

  if (visibleTypes.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        No solutions available. Run QCA analysis to generate solutions.
      </div>
    );
  }

  return (
    <div>
      {visibleTypes.map(({ key, label }) => (
        solutions[key] ? (
          <SolutionCard key={key} solution={solutions[key]!} label={label} />
        ) : null
      ))}
    </div>
  );
}
