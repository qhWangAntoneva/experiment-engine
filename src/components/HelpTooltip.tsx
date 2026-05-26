/**
 * HelpTooltip — shows a `?` icon in a circle with a tooltip popover on hover/focus.
 *
 * Usage:
 *   <HelpTooltip text="Explanatory text here" />
 *   <HelpTooltip text={t('help.someKey')} />
 *
 * Style: subtle, non-intrusive, positioned relative to the icon.
 * Pure inline styles — no new CSS framework dependency.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';

interface HelpTooltipProps {
  /** Tooltip text to display on hover */
  text: string;
  /** Optional aria-label for accessibility (defaults to text) */
  ariaLabel?: string;
  /** Optional inline style overrides for the wrapper */
  style?: React.CSSProperties;
  /** Optional placement: 'right' (default), 'left', 'top', 'bottom' */
  placement?: 'right' | 'left' | 'top' | 'bottom';
  /** Optional width override for the tooltip popover (default '260px') */
  width?: string;
}

const ICON_BASE: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: '18px',
  height: '18px',
  borderRadius: '50%',
  border: '1px solid var(--color-text-secondary, #888)',
  color: 'var(--color-text-secondary, #888)',
  fontSize: '12px',
  fontWeight: 700,
  fontFamily: 'var(--font-sans, sans-serif)',
  lineHeight: 1,
  cursor: 'help',
  userSelect: 'none',
  flexShrink: 0,
  transition: 'border-color 150ms ease, color 150ms ease, background 150ms ease',
};

export default function HelpTooltip({
  text,
  ariaLabel,
  style,
  placement = 'right',
  width = '260px',
}: HelpTooltipProps) {
  const [visible, setVisible] = useState(false);
  const wrapperRef = useRef<HTMLSpanElement>(null);

  const show = useCallback(() => setVisible(true), []);
  const hide = useCallback(() => setVisible(false), []);

  // Hide on click outside
  useEffect(() => {
    if (!visible) return;
    const handleClick = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setVisible(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [visible]);

  // Position offsets
  const posStyle: React.CSSProperties =
    placement === 'top'
      ? { bottom: 'calc(100% + 6px)', left: '50%', transform: 'translateX(-50%)' }
      : placement === 'bottom'
        ? { top: 'calc(100% + 6px)', left: '50%', transform: 'translateX(-50%)' }
        : placement === 'left'
          ? { right: 'calc(100% + 6px)', top: '50%', transform: 'translateY(-50%)' }
          : { left: 'calc(100% + 6px)', top: '50%', transform: 'translateY(-50%)' };

  return (
    <span
      ref={wrapperRef}
      style={{
        position: 'relative',
        display: 'inline-flex',
        alignItems: 'center',
        marginLeft: '4px',
        verticalAlign: 'middle',
        ...style,
      }}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      aria-label={ariaLabel ?? text}
      role="tooltip"
      tabIndex={0}
    >
      <span
        style={{
          ...ICON_BASE,
          color: visible ? 'var(--color-accent, #4a90d9)' : 'var(--color-text-secondary, #888)',
          borderColor: visible ? 'var(--color-accent, #4a90d9)' : 'var(--color-text-secondary, #888)',
          background: visible ? 'rgba(74, 144, 217, 0.08)' : 'transparent',
        }}
      >
        ?
      </span>
      {visible && (
        <span
          style={{
            position: 'absolute',
            ...posStyle,
            width,
            padding: '8px 12px',
            fontSize: '0.75rem',
            lineHeight: 1.5,
            color: 'var(--color-bg-primary, #fff)',
            background: 'var(--color-text-primary, #333)',
            borderRadius: '6px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
            zIndex: 1000,
            pointerEvents: 'none',
            whiteSpace: 'normal',
            wordBreak: 'break-word',
          }}
        >
          {text}
        </span>
      )}
    </span>
  );
}
