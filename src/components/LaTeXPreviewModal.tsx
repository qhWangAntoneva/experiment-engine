/**
 * LaTeXPreviewModal — modal for previewing LaTeX export content before download.
 *
 * Shows a read-only textarea with LaTeX content and two buttons:
 *  - Download: trigger the download
 *  - Close: dismiss the modal
 */

import React, { useEffect, useCallback } from 'react';

interface LaTeXPreviewModalProps {
  /** LaTeX content string to preview */
  content: string;
  /** Called when user clicks Download */
  onDownload: () => void;
  /** Called when user closes the modal */
  onClose: () => void;
  /** Whether the download is in progress */
  exporting?: boolean;
}

const OVERLAY_STYLE: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(0, 0, 0, 0.5)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 2000,
  padding: '20px',
};

const MODAL_STYLE: React.CSSProperties = {
  background: 'var(--color-bg-primary, #fff)',
  borderRadius: 'var(--radius-lg, 8px)',
  boxShadow: '0 8px 32px rgba(0,0,0,0.25)',
  width: '100%',
  maxWidth: '720px',
  maxHeight: '80vh',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
};

const HEADER_STYLE: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '16px 20px',
  borderBottom: '1px solid var(--color-border, #e0e0e0)',
  flexShrink: 0,
};

const BODY_STYLE: React.CSSProperties = {
  flex: 1,
  overflow: 'auto',
  padding: '20px',
};

const FOOTER_STYLE: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'flex-end',
  gap: '8px',
  padding: '12px 20px',
  borderTop: '1px solid var(--color-border, #e0e0e0)',
  flexShrink: 0,
};

const TEXTAREA_STYLE: React.CSSProperties = {
  width: '100%',
  minHeight: '300px',
  fontFamily: 'var(--font-mono, "SF Mono", monospace)',
  fontSize: '0.75rem',
  lineHeight: 1.6,
  padding: '12px',
  border: '1px solid var(--color-border, #e0e0e0)',
  borderRadius: 'var(--radius-sm, 4px)',
  background: 'var(--color-bg-input, #f5f5f5)',
  color: 'var(--color-text-primary, #333)',
  resize: 'vertical',
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
  tabSize: 2,
};

export default function LaTeXPreviewModal({
  content,
  onDownload,
  onClose,
  exporting = false,
}: LaTeXPreviewModalProps) {
  // Close on Escape key
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Prevent body scroll while modal is open
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) onClose();
    },
    [onClose]
  );

  return (
    <div style={OVERLAY_STYLE} onClick={handleOverlayClick} role="dialog" aria-modal="true" aria-label="LaTeX Preview">
      <div style={MODAL_STYLE}>
        {/* Header */}
        <div style={HEADER_STYLE}>
          <h3
            style={{
              fontSize: '0.9375rem',
              fontWeight: 600,
              margin: 0,
              color: 'var(--color-text-primary)',
            }}
          >
            LaTeX Preview
          </h3>
          <button
            className="btn btn-secondary"
            onClick={onClose}
            style={{ fontSize: '0.75rem', padding: '4px 10px', lineHeight: 1.4 }}
            aria-label="Close"
          >
            x
          </button>
        </div>

        {/* Body — read-only LaTeX textarea */}
        <div style={BODY_STYLE}>
          <textarea
            readOnly
            value={content}
            style={TEXTAREA_STYLE}
            spellCheck={false}
            onClick={(e) => {
              // Select all text on click for easy copying
              (e.target as HTMLTextAreaElement).select();
            }}
          />
        </div>

        {/* Footer */}
        <div style={FOOTER_STYLE}>
          <button
            className="btn btn-secondary"
            onClick={onClose}
            style={{ fontSize: '0.8125rem' }}
            disabled={exporting}
          >
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={onDownload}
            style={{ fontSize: '0.8125rem' }}
            disabled={exporting}
          >
            {exporting ? 'Downloading...' : 'Download .tex'}
          </button>
        </div>
      </div>
    </div>
  );
}
