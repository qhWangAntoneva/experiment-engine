import './Results.css'

const results = [
  {
    id: 'SIM-001',
    name: 'QCA Cell Array 4x4',
    status: 'success' as const,
    date: '2026-05-12 14:32',
    duration: '1.24s',
    polarization: 0.987,
    energy: -2.34e-19,
    output: [
      { cell: '(0,0)', value: 'P+', polarization: 0.99 },
      { cell: '(0,1)', value: 'P-', polarization: -0.98 },
      { cell: '(1,0)', value: 'P-', polarization: -0.97 },
      { cell: '(1,1)', value: 'P+', polarization: 0.99 },
    ],
  },
  {
    id: 'SIM-002',
    name: 'Majority Gate Analysis',
    status: 'success' as const,
    date: '2026-05-12 11:15',
    duration: '2.87s',
    polarization: 0.921,
    energy: -1.89e-19,
    output: [
      { cell: 'A', value: 'P+', polarization: 0.95 },
      { cell: 'B', value: 'P+', polarization: 0.93 },
      { cell: 'C', value: 'P-', polarization: -0.94 },
      { cell: 'OUT', value: 'P+', polarization: 0.91 },
    ],
  },
]

const statusLabel = {
  success: { text: 'Completed', cls: 'badge-success' },
  running: { text: 'Running', cls: 'badge-warning' },
  failed: { text: 'Failed', cls: 'badge-error' },
}

export default function Results() {
  return (
    <div className="results">
      <div className="page-header">
        <h2 className="page-title">Results</h2>
        <p className="page-subtitle">Simulation output and analysis</p>
      </div>

      <div className="results-toolbar">
        <div className="toolbar-left">
          <button className="btn btn-secondary">⟳ Refresh</button>
          <button className="btn btn-secondary">⬇ Export CSV</button>
        </div>
        <div className="toolbar-right">
          <input className="input" type="text" placeholder="Filter by name or ID..." style={{ width: 240 }} />
        </div>
      </div>

      {results.map((result) => {
        const s = statusLabel[result.status]
        return (
          <div key={result.id} className="result-card card">
            <div className="result-header">
              <div>
                <h3 className="result-name">{result.name}</h3>
                <span className="mono result-id">{result.id}</span>
              </div>
              <div className="result-meta">
                <span className={`badge ${s.cls}`}>{s.text}</span>
                <span className="result-stat">{result.date}</span>
                <span className="result-stat mono">{result.duration}</span>
              </div>
            </div>

            <div className="result-summary">
              <div className="summary-item">
                <span className="summary-label">Polarization</span>
                <span className="summary-value mono">{result.polarization.toFixed(3)}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Ground State Energy</span>
                <span className="summary-value mono">{result.energy.toExponential(3)} J</span>
              </div>
            </div>

            <div className="result-section">
              <h4 className="result-subtitle">Cell Output</h4>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Cell</th>
                      <th>State</th>
                      <th>Polarization</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.output.map((o) => (
                      <tr key={o.cell}>
                        <td className="mono">{o.cell}</td>
                        <td><span className={`badge ${o.value === 'P+' ? 'badge-success' : 'badge-warning'}`}>{o.value}</span></td>
                        <td className="mono">{o.polarization.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )
      })}

      {results.length === 0 && (
        <div className="results-empty">
          <p>No simulation results yet. Run a simulation from the Data Input page.</p>
        </div>
      )}
    </div>
  )
}
