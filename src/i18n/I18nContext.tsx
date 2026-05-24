/**
 * Lightweight i18n via React Context.
 *
 * Usage:
 *   import { useT } from '../i18n/I18nContext';
 *   const t = useT();
 *   <span>{t('dataInput.title')}</span>
 */

import React, { createContext, useContext, useState, useCallback, useEffect, useMemo } from 'react';
import type { Language, TranslationDict } from './translations';
import { translations, detectLanguage } from './translations';

// ─── Storage key ──────────────────────────────────────────────────────────────

const STORAGE_KEY = 'qca-language';

// ─── Context type ─────────────────────────────────────────────────────────────

interface I18nContextValue {
  /** Current language code */
  lang: Language;
  /** Switch language */
  setLang: (lang: Language) => void;
  /** Full translation dictionary for current language */
  dict: TranslationDict;
}

const I18nContext = createContext<I18nContextValue | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Language>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === 'en' || stored === 'zh') return stored;
    } catch {}
    return detectLanguage();
  });

  const setLang = useCallback((next: Language) => {
    setLangState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {}
  }, []);

  // Set html lang attribute for accessibility
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo<I18nContextValue>(
    () => ({ lang, setLang, dict: translations[lang] }),
    [lang, setLang]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

// ─── useT hook ────────────────────────────────────────────────────────────────

/**
 * Returns a translation function. Supports dot-separated paths.
 *
 * Example:
 *   const t = useT();
 *   t('dashboard.title')   // "首页" or "Dashboard"
 *   t('dataInput.loadedCases', 42, 'data.csv')  // function values
 */
export function useT() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error('useT must be used within an I18nProvider');
  }

  return useCallback(
    (path: string, ...args: any[]): string => {
      const parts = path.split('.');
      let value: any = ctx.dict;
      for (const part of parts) {
        if (value == null) break;
        value = value[part];
      }
      if (typeof value === 'function') {
        return (value as (...a: any[]) => string)(...args);
      }
      if (typeof value === 'string') {
        return value;
      }
      // Fallback: return the path itself
      return path;
    },
    [ctx.dict]
  );
}

/**
 * Hook that returns { lang, setLang } for language switching.
 */
export function useLanguage() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error('useLanguage must be used within an I18nProvider');
  }
  return { lang: ctx.lang, setLang: ctx.setLang };
}

// ─── LanguageSwitcher component ──────────────────────────────────────────────

interface LanguageSwitcherProps {
  /** CSS class name for the wrapper element */
  className?: string;
  /** Display mode: 'icon' (flags only), 'text' (language names), 'dropdown' (select) */
  variant?: 'icon' | 'text' | 'dropdown';
}

export function LanguageSwitcher({ className, variant = 'icon' }: LanguageSwitcherProps) {
  const { lang, setLang } = useLanguage();

  const toggle = useCallback(() => {
    setLang(lang === 'zh' ? 'en' : 'zh');
  }, [lang, setLang]);

  if (variant === 'dropdown') {
    return (
      <select
        className={className}
        value={lang}
        onChange={(e) => setLang(e.target.value as Language)}
        style={{ fontSize: '0.8125rem', padding: '4px 8px', cursor: 'pointer' }}
      >
        <option value="zh">中文</option>
        <option value="en">English</option>
      </select>
    );
  }

  if (variant === 'text') {
    return (
      <button
        className={className}
        onClick={toggle}
        style={{
          fontSize: '0.8125rem',
          fontWeight: 600,
          cursor: 'pointer',
          background: 'none',
          border: 'none',
          color: 'inherit',
          padding: '4px 8px',
        }}
        title={lang === 'zh' ? 'Switch to English' : '切换到中文'}
      >
        {lang === 'zh' ? 'EN' : '中'}
      </button>
    );
  }

  // 'icon' variant (default)
  return (
    <button
      className={className}
      onClick={toggle}
      style={{
        fontSize: '1rem',
        cursor: 'pointer',
        background: 'none',
        border: 'none',
        color: 'inherit',
        padding: '2px 6px',
        lineHeight: 1,
      }}
      title={lang === 'zh' ? 'Switch to English' : '切换到中文'}
      aria-label={lang === 'zh' ? 'Switch to English' : '切换到中文'}
    >
      {lang === 'zh' ? '\u{1F1EC}\u{1F1E7}' : '\u{1F1E8}\u{1F1F3}'}
    </button>
  );
}
