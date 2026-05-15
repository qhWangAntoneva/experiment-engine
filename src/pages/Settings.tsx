import { useState } from 'react'
import './Settings.css'

interface SettingField {
  key: string
  label: string
  type: 'text' | 'number' | 'select' | 'boolean'
  default: string | number | boolean
  options?: string[]
  description: string
}

const settings: SettingField[] = [
  { key: 'sim_engine', label: 'Simulation Engine', type: 'select', default: 'auto', options: ['auto', 'cpu', 'gpu'], description: 'Compute backend for simulation' },
  { key: 'max_threads', label: 'Max Threads', type: 'number', default: 4, description: 'Maximum CPU threads for parallel computation' },
  { key: 'precision', label: 'Precision Mode', type: 'select', default: 'double', options: ['single', 'double', 'extended'], description: 'Floating-point precision for calculations' },
  { key: 'auto_save', label: 'Auto-Save Results', type: 'boolean', default: true, description: 'Automatically save results after each simulation' },
  { key: 'log_level', label: 'Log Level', type: 'select', default: 'info', options: ['debug', 'info', 'warn', 'error'], description: 'Console logging verbosity' },
  { key: 'max_results', label: 'Max Stored Results', type: 'number', default: 50, description: 'Maximum number of results kept in history' },
]

export default function Settings() {
  const [values, setValues] = useState<Record<string, string | number | boolean>>(() => {
    const initial: Record<string, string | number | boolean> = {}
    for (const s of settings) {
      initial[s.key] = s.default
    }
    return initial
  })

  const updateValue = (key: string, value: string | number | boolean) => {
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Settings saved:', values)
    alert('Settings saved!')
  }

  return (
    <div className="settings">
      <div className="page-header">
        <h2 className="page-title">Settings</h2>
        <p className="page-subtitle">System configuration and preferences</p>
      </div>

      <form onSubmit={handleSave}>
        <div className="settings-section card">
          {settings.map((s) => (
            <div key={s.key} className="setting-row">
              <div className="setting-info">
                <label className="setting-label" htmlFor={s.key}>{s.label}</label>
                <p className="setting-desc">{s.description}</p>
              </div>
              <div className="setting-control">
                {s.type === 'number' && (
                  <input
                    id={s.key}
                    className="input input-mono"
                    type="number"
                    value={values[s.key] as number}
                    onChange={(e) => updateValue(s.key, e.target.valueAsNumber || 0)}
                    style={{ width: 160 }}
                  />
                )}
                {s.type === 'text' && (
                  <input
                    id={s.key}
                    className="input"
                    type="text"
                    value={values[s.key] as string}
                    onChange={(e) => updateValue(s.key, e.target.value)}
                    style={{ width: 240 }}
                  />
                )}
                {s.type === 'select' && (
                  <select
                    id={s.key}
                    className="input"
                    value={values[s.key] as string}
                    onChange={(e) => updateValue(s.key, e.target.value)}
                    style={{ width: 160 }}
                  >
                    {s.options?.map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                )}
                {s.type === 'boolean' && (
                  <label className="toggle-label">
                    <input
                      type="checkbox"
                      checked={values[s.key] as boolean}
                      onChange={(e) => updateValue(s.key, e.target.checked)}
                    />
                    <span className="toggle-text">{values[s.key] ? 'Enabled' : 'Disabled'}</span>
                  </label>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="settings-section card">
          <h3 className="section-title">About</h3>
          <div className="about-grid">
            <div className="about-item">
              <span className="about-label">Application</span>
              <span className="about-value">QCA Simulation Tool</span>
            </div>
            <div className="about-item">
              <span className="about-label">Version</span>
              <span className="about-value mono">0.1.0</span>
            </div>
            <div className="about-item">
              <span className="about-label">Framework</span>
              <span className="about-value">React 18 + Vite 5</span>
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary">
            ✓ Save Settings
          </button>
        </div>
      </form>
    </div>
  )
}
