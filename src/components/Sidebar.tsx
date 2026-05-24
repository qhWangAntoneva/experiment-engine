import { NavLink } from 'react-router-dom'
import type { NavItem } from '../types'
import './Sidebar.css'

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: '⊞' },
  { label: 'Data Input', path: '/input', icon: '↥' },
  { label: 'Results', path: '/results', icon: '≡' },
  { label: 'Settings', path: '/settings', icon: '⚙' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-logo">{'◈'}</span>
        <div>
          <h1 className="sidebar-title">QCA Text</h1>
          <p className="sidebar-version">v0.2.0</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar-link${isActive ? ' active' : ''}`
            }
          >
            <span className="sidebar-link-icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className="sidebar-status-dot" />
          <span>QCA Engine</span>
        </div>
        <p className="sidebar-footer-text">Pyodide + React</p>
      </div>
    </aside>
  )
}
