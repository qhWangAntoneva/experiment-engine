/**
 * PerformancePanel — collapsible BERT inference performance metrics display.
 *
 * Shows average inference time, cache hit rate, texts processed, last batch
 * timing, and the active model name.  Appears on the Dashboard when
 * inference has been performed.
 */

import React, { useState } from 'react';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { useT } from '../i18n/I18nContext';

// ─── Metric Item ─────────────────────────────────────────────────────────────

function MetricItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="metric-label">{label}</div>
      <div className="metric-value">
        <span className="metric-number">{value}</span>
      </div>
    </div>
  );
}

// ─── PerformancePanel ────────────────────────────────────────────────────────

export default function PerformancePanel() {
  const { state } = useQCAPipeline();
  const t = useT();
  const [expanded, setExpanded] = useState(false);

  const m = state.performanceMetrics;

  // Empty state — no inference has been performed yet
  if (!m || m.totalInferences === 0) {
    return (
      <div className="card" style={{ padding: '16px 20px', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontWeight: 600 }}>{t('performance.title')}</span>
          <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem' }}>
            {t('performance.noData')}
          </span>
        </div>
      </div>
    );
  }

  const hitRate = (m.cacheHits + m.cacheMisses) > 0
    ? ((m.cacheHits / (m.cacheHits + m.cacheMisses)) * 100).toFixed(1)
    : '0.0';
  const avgMs = m.totalInferences > 0
    ? (m.totalInferenceMs / m.totalInferences).toFixed(1)
    : '—';

  return (
    <div
      className="card"
      style={{ padding: '16px 20px', marginBottom: 16, cursor: 'pointer' }}
      onClick={() => setExpanded(!expanded)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setExpanded(!expanded); }}
      aria-expanded={expanded}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontWeight: 600 }}>
          {t('performance.title')}
          <span style={{
            fontSize: '0.8125rem',
            fontWeight: 400,
            color: 'var(--color-text-secondary)',
            marginLeft: 8,
          }}>
            (avg {avgMs}{t('performance.ms')}, {hitRate}% cache hits)
          </span>
        </span>
        <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.75rem' }}>
          {expanded ? '▼' : '▶'}
        </span>
      </div>

      {expanded && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
          gap: 16,
          marginTop: 16,
        }}>
          <MetricItem label={t('performance.avgInferenceTime')} value={`${avgMs} ${t('performance.ms')}`} />
          <MetricItem label={t('performance.cacheHitRate')} value={`${hitRate}%`} />
          <MetricItem label={t('performance.textsProcessed')} value={String(m.totalTextsProcessed)} />
          <MetricItem label={t('performance.lastBatchMs')} value={`${m.lastInferenceBatchMs.toFixed(1)} ${t('performance.ms')}`} />
          <MetricItem label={t('performance.activeModel')} value={m.modelName?.replace('Xenova/', '') || '—'} />
        </div>
      )}
    </div>
  );
}
