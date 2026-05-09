import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../utils/api'
import {
  LayoutDashboard, BarChart3, Brain, FileText,
  LogOut, Menu, X, Activity, ChevronRight, Zap,
  CheckCircle, AlertCircle
} from 'lucide-react'

const NAV = [
  { path: '/dashboard',       icon: LayoutDashboard, label: 'Dashboard'       },
  { path: '/analysis',        icon: BarChart3,        label: 'Risk Analysis'   },
  { path: '/explainability',  icon: Brain,            label: 'Explainability'  },
  { path: '/cam',             icon: FileText,         label: 'CAM Report'      },
]

export default function Layout({ children }) {
  const { user, logout }        = useAuth()
  const location                = useLocation()
  const navigate                = useNavigate()
  const [open, setOpen]         = useState(false)
  const [health, setHealth]     = useState(null)

  useEffect(() => {
    api.get('/health').then(r => setHealth(r.data)).catch(() => {})
  }, [])

  const handleLogout = () => { logout(); navigate('/') }

  const active = (path) =>
    location.pathname.startsWith(path)
      ? 'bg-neon/10 text-neon border-l-2 border-neon'
      : 'text-slate-400 hover:text-white hover:bg-white/5 border-l-2 border-transparent'

  return (
    <div className="flex h-screen bg-dark overflow-hidden">
      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 flex flex-col
        bg-dark-2 border-r border-dark-border
        transition-transform duration-300
        ${open ? 'translate-x-0' : '-translate-x-full'}
        lg:relative lg:translate-x-0
      `}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-dark-border">
          <div className="w-8 h-8 rounded-lg bg-neon/20 flex items-center justify-center">
            <Zap className="w-4 h-4 text-neon" />
          </div>
          <div>
            <p className="font-black text-white text-sm leading-none">INTELLI</p>
            <p className="text-neon text-xs font-bold leading-none">CREDIT</p>
          </div>
          <button onClick={() => setOpen(false)} className="ml-auto lg:hidden text-slate-400">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.map(({ path, icon: Icon, label }) => (
            <Link key={path} to={path} onClick={() => setOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${active(path)}`}>
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
              {location.pathname.startsWith(path) && (
                <ChevronRight className="w-3 h-3 ml-auto" />
              )}
            </Link>
          ))}
        </nav>

        {/* Integration Status */}
        {health && (
          <div className="px-4 py-3 border-t border-dark-border">
            <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-2">
              API Status
            </p>
            {Object.entries(health.integrations || {}).map(([key, active]) => (
              <div key={key} className="flex items-center gap-2 py-0.5">
                {active
                  ? <CheckCircle className="w-3 h-3 text-neon flex-shrink-0" />
                  : <AlertCircle className="w-3 h-3 text-slate-600 flex-shrink-0" />}
                <span className={`text-xs capitalize ${active ? 'text-slate-300' : 'text-slate-600'}`}>
                  {key.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* User */}
        <div className="px-4 py-4 border-t border-dark-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-neon/20 flex items-center justify-center text-neon font-bold text-sm">
              {user?.name?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.name}</p>
              <p className="text-xs text-slate-500 capitalize">{user?.role?.replace('_', ' ')}</p>
            </div>
            <button onClick={handleLogout} className="text-slate-500 hover:text-red-400 transition-colors">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {open && (
        <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setOpen(false)} />
      )}

      {/* ── Main Content ────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-14 flex items-center px-4 lg:px-6 border-b border-dark-border bg-dark-2/50 backdrop-blur gap-4">
          <button onClick={() => setOpen(true)} className="lg:hidden text-slate-400">
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2 ml-auto">
            <div className="flex items-center gap-1.5 text-xs text-neon bg-neon/10 px-2.5 py-1 rounded-full border border-neon/20">
              <Activity className="w-3 h-3" />
              System Active
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6 grid-bg">
          {children}
        </main>
      </div>
    </div>
  )
}
