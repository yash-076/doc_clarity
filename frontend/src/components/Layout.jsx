import { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  Upload,
  MessageSquare,
  Settings,
  Sparkles,
  Menu,
  X,
  Zap,
} from 'lucide-react'
import './Layout.css'

export default function Layout() {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <Link to="/" className="sidebar-logo">
            <div className="sidebar-logo-icon">
              <Sparkles size={20} />
            </div>
            <div className="sidebar-logo-text">
              <span className="sidebar-logo-title">Doc Clarity</span>
              <span className="sidebar-logo-subtitle">AI Intelligence</span>
            </div>
          </Link>
        </div>

        <nav className="sidebar-nav">
          <span className="sidebar-nav-label">Main</span>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-nav-item ${isActive(item.path) ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </Link>
          ))}

          <span className="sidebar-nav-label" style={{ marginTop: 'var(--space-4)' }}>Quick Actions</span>
          <Link
            to="/dashboard"
            state={{ openUpload: true }}
            className="sidebar-nav-item"
            onClick={() => setSidebarOpen(false)}
          >
            <Upload size={18} />
            <span>Upload Document</span>
          </Link>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-footer-version">
            <Zap size={14} style={{ color: 'var(--color-primary-400)' }} />
            <span>Advanced AI Engine</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="top-bar">
          <div className="top-bar-left">
            <button
              className="btn btn-ghost mobile-menu-btn"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              id="mobile-menu-toggle"
            >
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <nav className="top-bar-breadcrumb">
              <Link to="/dashboard">Home</Link>
              <span className="top-bar-breadcrumb-sep">/</span>
              <span className="top-bar-breadcrumb-current">
                {location.pathname === '/dashboard' ? 'Dashboard' : 'Document'}
              </span>
            </nav>
          </div>
          <div className="top-bar-right">
            <div className="pulse-dot" data-tooltip="Backend Connected" />
          </div>
        </header>

        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
