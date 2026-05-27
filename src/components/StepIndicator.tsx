import React from 'react';

interface StepIndicatorProps {
  currentStep: number; // 0 = Load Data, 1 = Calibrate, 2 = Analyze, 3 = Results
  className?: string;
}

const STEPS = ['Load Data', 'Calibrate', 'Analyze', 'Results'];

export default function StepIndicator({ currentStep, className }: StepIndicatorProps) {
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0',
        padding: '16px 0',
        width: '100%',
      }}
    >
      {STEPS.map((label, i) => (
        <React.Fragment key={label}>
          {/* Step circle + label */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: i === currentStep
                  ? 'var(--color-primary, #0066cc)'
                  : i < currentStep
                    ? 'var(--color-text-secondary, #888)'
                    : 'transparent',
                color: i <= currentStep ? '#fff' : 'var(--color-text-secondary, #888)',
                border: i <= currentStep ? 'none' : '2px solid var(--color-border, #ddd)',
                transition: 'all 0.2s ease',
              }}
            >
              {i < currentStep ? '✓' : i + 1}
            </div>
            <span
              style={{
                fontSize: '0.75rem',
                color: i === currentStep ? 'var(--color-primary, #0066cc)' : 'var(--color-text-secondary, #888)',
                fontWeight: i === currentStep ? 600 : 400,
                whiteSpace: 'nowrap',
              }}
            >
              {label}
            </span>
          </div>
          {/* Connector line between steps */}
          {i < STEPS.length - 1 && (
            <div
              style={{
                width: '60px',
                height: '2px',
                background: i < currentStep ? 'var(--color-primary, #0066cc)' : 'var(--color-border, #ddd)',
                margin: '0 4px',
                marginBottom: '24px',
                transition: 'background 0.2s ease',
              }}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
