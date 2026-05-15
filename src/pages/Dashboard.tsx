import type { MetricCardData } from '../types'
import './Dashboard.css'

const metrics: MetricCardData[] = [
  { label: 'Total Simulations', value: 128, trend: 'up', change: 12.5, status: 'normal' },
  { label: 'Success Rate', value: '94.2', unit: '%', trend: 'stable', change: 0.3, status: 'normal' },
  { label: 'Avg Duration', value: 2.34, unit: 's', trend: 'down', change: 8.1, status: 'normal' },
  { label: 'Active Jobs', value: 3, trend: 'up', change: 1, status: 'warning' },
]

const recentRuns = [
  { id: 'SIM-001', name: 'QCA Cell Array 4x4', status: 'success' as const, duration: '1.24s', date: '2026-05-12' },
  { id: 'SIM-002', name: 'Majority Gate Analysis', status: 'success' as const, duration: '2.87s', date: '2026-05-12' },
  { id: 'SIM-003', name: 'Crossbar Network v2', status: 'running' as const, duration: '--', date: '2026-05-11' },
  { id: 'SIM-004', name: 'Wire Crossing Test', status: 'failed' as const, duration: '0.92s', date: '2026-05-11' },
]

const statusLabel = {
  success: { text: 'Completed', cls: 'badge-success' },
  running: { text: 'Running', cls: 'badge-warning' },
  failed: { text: 'Failed', cls: 'badge-error' },
}

export default function Dashboard() {
  return (
    <div className="dashboard">
      <div className="page-header">
        <h2 className="page-title">Dashboard</h2>
        <p className="page-subtitle">QCA Simulation System Overview</p>
      </div>

      <div className="metric-grid">
        {metrics.map((m) => (
          <div key={m.label} className={`metric-card card ${m.status === 'warning' ? 'metric-warning' : ''}`}>
            <div className="metric-header">
              <span className="metric-label">{m.label}</span>
              {m.status === 'warning' && <span className="badge badge-warning">Active</span>}
            </div>
            <div className="metric-value">
              <span className="metric-number">{m.value}</span>
              {m.unit && <span className="metric-unit">{m.unit}</span>}
            </div>
            <div className="metric-trend">
              <span className={`trend-arrow trend-${m.trend}`}>
                {m.trend === 'up' ? '↑' : m.trend === 'down' ? '↓' : '→'}
              </span>
              <span className="trend-change">{m.change}%</span>
              <span className="trend-label">vs last week</span>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-section">
        <h3 className="section-title">Recent Simulation Runs</h3>
        <div className="card table-container">
          <table>
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Name</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {recentRuns.map((run) => {
                const s = statusLabel[run.status]
                return (
                  <tr key={run.id}>
                    <td className="mono">{run.id}</td>
                    <td>{run.name}</td>
                    <td><span className={`badge ${s.cls}`}>{s.text}</span></td>
                    <td className="mono">{run.duration}</td>
                    <td>{run.date}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
