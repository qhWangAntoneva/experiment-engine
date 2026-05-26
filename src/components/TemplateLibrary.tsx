/**
 * TemplateLibrary — displays built-in and imported QCA condition set
 * templates as a card grid on the Dashboard.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { useT } from '../i18n/I18nContext';
import {
  getBuiltinTemplates,
  getImportedTemplates,
  removeImportedTemplate,
} from '../services/templateService';
import { QCAVariant, type ConditionSetTemplate } from '../types/qca';
import { conditionSetToYaml } from '../utils/conditionSetToYaml';
import './TemplateLibrary.css';

const DOMAIN_COLORS: Record<string, string> = {
  dissatisfaction: '#dc2626',
  policy_demand: '#2563eb',
  co_production: '#16a34a',
  trust: '#7c3aed',
  gov_responsiveness: '#0d9488',
};

export default function TemplateLibrary() {
  const navigate = useNavigate();
  const t = useT();
  const { setYamlContent } = useQCAPipeline();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imported, setImported] = useState<ConditionSetTemplate[]>([]);

  // Simulate skeleton loading
  useEffect(() => {
    let canceled = false;
    try {
      const importedTemplates = getImportedTemplates();
      if (!canceled) setImported(importedTemplates);
    } catch {
      if (!canceled) setError(t('templates.importFailed'));
    }
    const timer = setTimeout(() => {
      if (!canceled) setLoading(false);
    }, 150);
    return () => {
      canceled = true;
      clearTimeout(timer);
    };
  }, [t]);

  const builtin = getBuiltinTemplates();
  const allTemplates = [...builtin, ...imported];

  const handleUseTemplate = useCallback(
    (template: ConditionSetTemplate) => {
      const raw = localStorage.getItem('qca-settings');
      const settings = raw ? JSON.parse(raw) : {};
      const qcaVariant = settings.qca_variant === 'csqca' ? QCAVariant.CSQCA : QCAVariant.FSQCA;
      const cs = {
        name: template.name,
        description: template.description,
        domain: template.domain,
        conditions: template.conditions,
        outcome: template.outcome,
        scoring_source: 'prototype' as const,
        qca_variant: qcaVariant,
      };
      setYamlContent(conditionSetToYaml(cs));
      navigate('/input');
    },
    [setYamlContent, navigate]
  );

  const handleRemoveImport = useCallback(
    (id: string) => {
      try {
        removeImportedTemplate(id);
        setImported((prev) => prev.filter((t) => t.id !== id));
      } catch {
        // ignore
      }
    },
    []
  );

  if (loading) {
    return (
      <div className="dashboard-section">
        <h3 className="section-title">{t('templates.libraryTitle')}</h3>
        <div className="template-grid">
          {[1, 2, 3].map((i) => (
            <div key={i} className="template-card skeleton" style={{ minHeight: 160 }}>
              <div className="skeleton-line w-60" />
              <div className="skeleton-line w-80" />
              <div className="skeleton-line w-40" />
              <div className="skeleton-line w-50" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-section">
        <h3 className="section-title">{t('templates.libraryTitle')}</h3>
        <div className="card" style={{ padding: '16px', color: 'var(--color-error)' }}>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-section">
      <h3 className="section-title">{t('templates.libraryTitle')}</h3>
      <p className="section-desc">{t('templates.librarySubtitle')}</p>
      <div className="template-grid">
        {allTemplates.map((tmpl) => {
          const color = DOMAIN_COLORS[tmpl.domain] ?? '#6b7280';
          const isBuiltin = tmpl.source === 'builtin';
          return (
            <div key={tmpl.id} className={`template-card card ${isBuiltin ? '' : 'template-imported'}`}>
              <div className="template-card-header">
                <span
                  className="template-domain-badge"
                  style={{ background: color }}
                >
                  {tmpl.domain}
                </span>
                <span className={`template-source-badge ${isBuiltin ? 'source-builtin' : 'source-imported'}`}>
                  {isBuiltin ? t('templates.builtinLabel') : t('templates.importedLabel')}
                </span>
              </div>
              <h4 className="template-name">{tmpl.name}</h4>
              <p className="template-description">{tmpl.description}</p>
              <div className="template-meta">
                <span className="template-condition-count">
                  {tmpl.conditionCount} {t('templates.conditionCount')}
                </span>
              </div>
              <div className="template-actions">
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => handleUseTemplate(tmpl)}
                >
                  {t('templates.useTemplate')}
                </button>
                {!isBuiltin && (
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => handleRemoveImport(tmpl.id)}
                    title="Remove"
                  >
                    x
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
