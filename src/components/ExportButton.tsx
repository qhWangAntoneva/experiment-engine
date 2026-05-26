/**
 * ExportButton — configurable export button with toast notifications and
 * LaTeX preview modal support.
 *
 * Features:
 *  - Consistent styling across all pages
 *  - Shows a toast "Exporting..." then "Export complete" on click
 *  - For LaTeX exports: shows a preview modal before download
 *  - Disabled state during export
 */

import React, { useState, useCallback } from 'react';
import LaTeXPreviewModal from './LaTeXPreviewModal';

export type ExportFormat = 'csv' | 'json' | 'latex' | 'docx';

interface ExportButtonProps {
  /** Export format */
  format: ExportFormat;
  /** Label displayed on the button */
  label: string;
  /** Export handler — must return a Blob (e.g. CSV, JSON, LaTeX, DOCX) */
  onExport: (format: ExportFormat) => Promise<Blob>;
  /** Optional: LaTeX preview content string (only used when format === 'latex') */
  latexPreview?: string;
  /** Optional: filename for download (without extension) */
  filename?: string;
  /** Optional: disabled state */
  disabled?: boolean;
  /** Optional: className override */
  className?: string;
  /** Optional: inline style overrides */
  style?: React.CSSProperties;
  /** Callback when export starts */
  onExportStart?: () => void;
  /** Callback when export succeeds */
  onExportSuccess?: () => void;
  /** Callback when export fails */
  onExportError?: (error: string) => void;
}

const EXT_MAP: Record<ExportFormat, string> = {
  csv: 'csv',
  json: 'json',
  latex: 'tex',
  docx: 'docx',
};

export default function ExportButton({
  format,
  label,
  onExport,
  latexPreview,
  filename = 'qca-analysis',
  disabled = false,
  className,
  style: externalStyle,
  onExportStart,
  onExportSuccess,
  onExportError,
}: ExportButtonProps) {
  const [exporting, setExporting] = useState(false);
  const [showLaTeXModal, setShowLaTeXModal] = useState(false);
  const [latexContent, setLatexContent] = useState<string>('');

  const handleClick = useCallback(async () => {
    if (disabled || exporting) return;

    if (format === 'latex' && latexPreview) {
      // For LaTeX, show preview modal first
      setLatexContent(latexPreview);
      setShowLaTeXModal(true);
      return;
    }

    setExporting(true);
    onExportStart?.();

    try {
      const blob = await onExport(format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.${EXT_MAP[format]}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      onExportSuccess?.();
    } catch (err: any) {
      onExportError?.(err.message ?? 'Export failed');
    } finally {
      setExporting(false);
    }
  }, [disabled, exporting, format, latexPreview, onExport, filename, onExportStart, onExportSuccess, onExportError]);

  const handleLaTeXDownload = useCallback(async () => {
    setShowLaTeXModal(false);
    setExporting(true);
    onExportStart?.();

    try {
      const blob = await onExport('latex');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.tex`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      onExportSuccess?.();
    } catch (err: any) {
      onExportError?.(err.message ?? 'Export failed');
    } finally {
      setExporting(false);
    }
  }, [onExport, filename, onExportStart, onExportSuccess, onExportError]);

  return (
    <>
      <button
        className={className ?? 'btn btn-secondary'}
        onClick={handleClick}
        disabled={disabled || exporting}
        style={{
          fontSize: '0.8125rem',
          ...externalStyle,
        }}
      >
        {exporting ? 'Exporting...' : label}
      </button>

      {showLaTeXModal && (
        <LaTeXPreviewModal
          content={latexContent}
          onDownload={handleLaTeXDownload}
          onClose={() => setShowLaTeXModal(false)}
          exporting={exporting}
        />
      )}
    </>
  );
}
