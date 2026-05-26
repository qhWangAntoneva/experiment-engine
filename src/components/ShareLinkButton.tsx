/**
 * ShareLinkButton — generates a shareable URL for the current ConditionSet
 * and copies it to the clipboard. Mounted on the DataInput page.
 */

import React, { useState, useCallback } from 'react';
import { useT } from '../i18n/I18nContext';
import { generateShareUrl } from '../services/templateService';
import type { ConditionSet } from '../types/qca';

interface ShareLinkButtonProps {
  conditionSet: ConditionSet | null;
}

export default function ShareLinkButton({ conditionSet }: ShareLinkButtonProps) {
  const t = useT();
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleShare = useCallback(async () => {
    if (!conditionSet) return;
    setError(null);

    try {
      const url = generateShareUrl(conditionSet);
      // Check URL length (browsers typically limit to ~2048 chars)
      if (url.length > 2000) {
        setError(t('templates.shareUrlTooLong'));
        return;
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(url);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } else {
        // Fallback: show URL in read-only input
        setError(url);
      }
    } catch {
      setError(t('templates.shareFailed'));
    }
  }, [conditionSet, t]);

  if (!conditionSet) {
    return (
      <button
        className="btn btn-secondary"
        disabled
        style={{ fontSize: '0.8125rem' }}
        title={t('dataInput.noTextData')}
      >
        {t('templates.shareLink')}
      </button>
    );
  }

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
      <button
        className={`btn ${copied ? 'btn-success' : 'btn-secondary'}`}
        onClick={handleShare}
        style={{ fontSize: '0.8125rem' }}
      >
        {copied ? t('templates.shareCopied') : t('templates.generateShareLink')}
      </button>
      {error && error !== t('templates.shareFailed') && (
        <input
          type="text"
          readOnly
          value={error}
          style={{
            fontSize: '0.6875rem',
            fontFamily: 'monospace',
            padding: '4px 8px',
            border: '1px solid var(--color-border)',
            borderRadius: '4px',
            background: 'var(--color-bg)',
            width: '280px',
            cursor: 'text',
          }}
          onFocus={(e) => e.target.select()}
        />
      )}
      {error === t('templates.shareFailed') && (
        <span style={{ fontSize: '0.75rem', color: 'var(--color-error)' }}>{error}</span>
      )}
      {error === t('templates.shareUrlTooLong') && (
        <span style={{ fontSize: '0.75rem', color: 'var(--color-error)' }}>{error}</span>
      )}
    </div>
  );
}
