import { useState } from 'react'
import './DataInput.css'

interface FieldDef {
  key: string
  label: string
  type: 'number' | 'text' | 'select' | 'boolean'
  default: string | number | boolean
  options?: string[]
  unit?: string
  description?: string
}

const fieldGroups: { title: string; fields: FieldDef[] }[] = [
  {
    title: 'Cell Configuration',
    fields: [
      { key: 'cell_size', label: 'Cell Size', type: 'number', default: 18, unit: 'nm', description: 'Quantum dot cell dimension' },
      { key: 'dot_radius', label: 'Dot Radius', type: 'number', default: 2.5, unit: 'nm' },
      { key: 'tunnel_barrier', label: 'Tunnel Barrier', type: 'select', default: 'medium', options: ['low', 'medium', 'high'] },
    ],
  },
  {
    title: 'Array Parameters',
    fields: [
      { key: 'rows', label: 'Rows', type: 'number', default: 4 },
      { key: 'cols', label: 'Columns', type: 'number', default: 4 },
      { key: 'pitch_x', label: 'Horizontal Pitch', type: 'number', default: 20, unit: 'nm' },
      { key: 'pitch_y', label: 'Vertical Pitch', type: 'number', default: 20, unit: 'nm' },
    ],
  },
  {
    title: 'Simulation Settings',
    fields: [
      { key: 'temperature', label: 'Temperature', type: 'number', default: 4.2, unit: 'K', description: 'Operating temperature in Kelvin' },
      { key: 'relaxation_steps', label: 'Relaxation Steps', type: 'number', default: 1000 },
      { key: 'convergence_threshold', label: 'Convergence Threshold', type: 'number', default: 1e-6 },
      { key: 'output_mode', label: 'Output Mode', type: 'select', default: 'full', options: ['full', 'compact', 'minimal'] },
    ],
  },
]

export default function DataInput() {
  const [values, setValues] = useState<Record<string, string | number | boolean>>(() => {
    const initial: Record<string, string | number | boolean> = {}
    for (const group of fieldGroups) {
      for (const field of group.fields) {
        initial[field.key] = field.default
      }
    }
    return initial
  })

  const [simName, setSimName] = useState('')
  const [description, setDescription] = useState('')

  const updateValue = (key: string, value: string | number | boolean) => {
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Simulation params:', { name: simName, description, parameters: values })
    alert('Simulation submitted! (Integration pending)')
  }

  const handleReset = () => {
    const initial: Record<string, string | number | boolean> = {}
    for (const group of fieldGroups) {
      for (const field of group.fields) {
        initial[field.key] = field.default
      }
    }
    setValues(initial)
    setSimName('')
    setDescription('')
  }

  return (
    <div className="data-input">
      <div className="page-header">
        <h2 className="page-title">Data Input</h2>
        <p className="page-subtitle">Configure simulation parameters</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="input-section card">
          <h3 className="section-title">General Information</h3>
          <div className="form-row">
            <div className="form-group">
              <label className="label" htmlFor="simName">Simulation Name</label>
              <input
                id="simName"
                className="input"
                type="text"
                value={simName}
                onChange={(e) => setSimName(e.target.value)}
                placeholder="e.g. QCA Cell Array 4x4"
                required
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="label" htmlFor="desc">Description</label>
              <textarea
                id="desc"
                className="input"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description of this simulation run"
                style={{ resize: 'vertical' }}
              />
            </div>
          </div>
        </div>

        {fieldGroups.map((group) => (
          <div key={group.title} className="input-section card">
            <h3 className="section-title">{group.title}</h3>
            <div className="form-grid">
              {group.fields.map((field) => (
                <div key={field.key} className="form-group">
                  <label className="label" htmlFor={field.key}>
                    {field.label}
                    {field.unit && <span className="field-unit"> ({field.unit})</span>}
                  </label>
                  {field.type === 'number' && (
                    <input
                      id={field.key}
                      className="input input-mono"
                      type="number"
                      value={values[field.key] as number}
                      onChange={(e) => updateValue(field.key, e.target.valueAsNumber || 0)}
                      step={typeof values[field.key] === 'number' && values[field.key] < 1 ? 'any' : '1'}
                    />
                  )}
                  {field.type === 'text' && (
                    <input
                      id={field.key}
                      className="input"
                      type="text"
                      value={values[field.key] as string}
                      onChange={(e) => updateValue(field.key, e.target.value)}
                    />
                  )}
                  {field.type === 'select' && (
                    <select
                      id={field.key}
                      className="input"
                      value={values[field.key] as string}
                      onChange={(e) => updateValue(field.key, e.target.value)}
                    >
                      {field.options?.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  )}
                  {field.type === 'boolean' && (
                    <div className="checkbox-wrapper">
                      <input
                        id={field.key}
                        type="checkbox"
                        checked={values[field.key] as boolean}
                        onChange={(e) => updateValue(field.key, e.target.checked)}
                      />
                    </div>
                  )}
                  {field.description && (
                    <p className="field-desc">{field.description}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}

        <div className="form-actions">
          <button type="submit" className="btn btn-primary">
            ▶ Run Simulation
          </button>
          <button type="button" className="btn btn-secondary" onClick={handleReset}>
            ↺ Reset
          </button>
        </div>
      </form>
    </div>
  )
}
