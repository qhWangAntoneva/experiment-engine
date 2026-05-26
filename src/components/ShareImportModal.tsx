/**
 * ShareImportModal — mounted on the Dashboard. On mount, checks for
 * ?share= parameter in the URL. If found, decodes and shows an import
 * modal with options to import or load-and-go.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQCAPipeline } from '../store/QCAPipelineContext';
import { useT } from '../i18n/I18nContext';
import {
  decodeSharedConditionSet,
  saveImportedTemplate,
} from '../services/templateService';
import type { ConditionSetTemplate, ConditionSet } from '../types/qca';

export default function ShareImportModal() {
  const navigate = useNavigate();
  const t = useT();
  const { setConditionSet } = useQCAPipeline();

  const [show, setShow] = useState(false);
  const [conditionSet, setConditionSetLocal] = useState<ConditionSet | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    // Check for ?share= param
    try {
      const params = new URLSearchParams(window.location.search);
      const sharePayload = params.get('share');
      if (!sharePayload) return;

      const cs = decodeSharedConditionSet(sharePayload);
      if (!cs) {
        setError(t('templates.importErrorInvalid'));
        setShow(true);
        return;
      }

      setConditionSetLocal(cs);
      setShow(true);
    } catch {
      // No share param — don't show modal
    }
  }, [t]);

  const cleanUrl = useCallback(() => {
    try {
      const url = new URL(window.location.href);
      url.searchParams.delete('share');
      window.history.replaceState(null, '', url.toString());
    } catch {
      // ignore
    }
  }, []);

  const handleImport = useCallback(() => {
    if (!conditionSet) return;
    try {
      const template: ConditionSetTemplate = {
        id: `imported-${Date.now()}`,
        name: conditionSet.name,
        description: conditionSet.description,
        domain: conditionSet.domain,
        conditions: conditionSet.conditions,
        outcome: conditionSet.outcome,
        conditionCount: conditionSet.conditions.length,
        source: 'imported',
        createdAt: new Date().toISOString(),
      };
      saveImportedTemplate(template);
      setActionMessage(t('templates.importSuccess'));
      setTimeout(() => {
        setShow(false);
        cleanUrl();
      }, 1000);
    } catch {
      setError(t('templates.importErrorIncomplete'));
    }
  }, [conditionSet, t, cleanUrl]);

  const handleLoadAndGo = useCallback(() => {
    if (!conditionSet) return;
    try {
      const template: ConditionSetTemplate = {
        id: `imported-${Date.now()}`,
        name: conditionSet.name,
        description: conditionSet.description,
        domain: conditionSet.domain,
        conditions: conditionSet.conditions,
        outcome: conditionSet.outcome,
        conditionCount: conditionSet.conditions.length,
        source: 'imported',
        createdAt: new Date().toISOString(),
      };
      saveImportedTemplate(template);
      setConditionSet(conditionSet);
      cleanUrl();
      setShow(false);
      navigate('/input');
    } catch {
      setError(t('templates.importErrorIncomplete'));
    }
  }, [conditionSet, setConditionSet, navigate, t, cleanUrl]);

  const handleDismiss = useCallback(() => {
    setShow(false);
    cleanUrl();
  }, [cleanUrl]);

  if (!show) return null;

  return (
    <div className="modal-overlay" style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.4)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div className="card" style={{
        maxWidth: 480,
        width: '90%',
        padding: '24px',
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
      }}>
        {error ? (
          <>
            <h3 style={{ fontSize: '1rem', marginBottom: '12px', color: 'var(--color-error)' }}>
              {t('templates.importErrorInvalid')}
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
              {error}
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={handleDismiss} style={{ fontSize: '0.8125rem' }}>
                {t('templates.importDismiss')}
              </button>
            </div>
          </>
        ) : actionMessage ? (
          <>
            <h3 style={{ fontSize: '1rem', marginBottom: '12px', color: 'var(--color-success)' }}>
              {t('templates.importSuccess')}
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
              {actionMessage}
            </p>
          </>
        ) : conditionSet ? (
          <>
            <h3 style={{ fontSize: '1rem', marginBottom: '4px' }}>
              {t('templates.importTitle')}
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
              {t('templates.importFromLink')}
            </p>

            <div style={{
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px 14px',
              marginBottom: '16px',
            }}>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '4px' }}>
                {conditionSet.name}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
                {conditionSet.description}
              </div>
              <div style={{ display: 'flex', gap: '8px', fontSize: '0.6875rem', color: 'var(--color-text-secondary)' }}>
                <span style={{
                  display: 'inline-block',
                  padding: '1px 6px',
                  background: 'var(--color-accent-bg, #eff6ff)',
                  borderRadius: '4px',
                  fontWeight: 500,
                }}>
                  {conditionSet.domain}
                </span>
                <span>{conditionSet.conditions.length} {t('templates.conditionCount')}</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button className="btn btn-outline" onClick={handleDismiss} style={{ fontSize: '0.8125rem' }}>
                {t('templates.importDismiss')}
              </button>
              <button className="btn btn-secondary" onClick={handleImport} style={{ fontSize: '0.8125rem' }}>
                {t('templates.importConfirm')}
              </button>
              <button className="btn btn-primary" onClick={handleLoadAndGo} style={{ fontSize: '0.8125rem' }}>
                {t('templates.importLoadAndGo')}
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
