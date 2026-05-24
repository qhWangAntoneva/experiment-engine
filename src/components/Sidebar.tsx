import { NavLink } from 'react-router-dom'
import { useT } from '../i18n/I18nContext'
import { LanguageSwitcher } from '../i18n/I18nContext'
import './Sidebar.css'

export default function Sidebar() {
  const t = useT()

  const navItems = [
    { label: t('sidebar.dashboard'), path: '/dashboard', icon: '⊞' },
    { label: t('sidebar.dataInput'), path: '/input', icon: '↥' },
    { label: t('sidebar.results'), path: '/results', icon: '≡' },
    { label: t('sidebar.settings'), path: '/settings', icon: '⚙' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-logo">{'◈'}</span>
        <div>
          <h1 className="sidebar-title">{t('sidebar.appTitle')}</h1>
          <p className="sidebar-version">{t('sidebar.version')}</p>
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
          <span>{t('sidebar.engineLabel')}</span>
        </div>
        <LanguageSwitcher variant="text" />
        <p className="sidebar-footer-text">{t('sidebar.appSubtitle')}</p>
      </div>
    </aside>
  )
}
