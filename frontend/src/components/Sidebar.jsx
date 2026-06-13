import { NavLink } from 'react-router-dom'
import { useEffect, useState } from 'react'
import {
  LayoutDashboard, Zap, BarChart2, LineChart,
  Activity, Database, ShieldCheck, Circle
} from 'lucide-react'
import { getHealth } from '../api'

const links = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/predict',   icon: Zap,             label: 'Predict' },
  { to: '/metrics',   icon: BarChart2,        label: 'Metrics' },
  { to: '/eda',       icon: LineChart,        label: 'EDA' },
  { to: '/monitor',   icon: Activity,         label: 'Monitor' },
  { to: '/analytics', icon: Database,         label: 'Analytics' },
]

export default function Sidebar() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    getHealth()
      .then(r => setHealth(r.data))
      .catch(() => setHealth(null))
    const t = setInterval(() => {
      getHealth().then(r => setHealth(r.data)).catch(() => setHealth(null))
    }, 15000)
    return () => clearInterval(t)
  }, [])

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-slate-900 border-r border-slate-800 flex flex-col z-20">

      {/* Logo */}
      <div className="px-5 py-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-sky-600 rounded-lg flex items-center justify-center shrink-0">
            <ShieldCheck size={16} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white leading-tight">FraudGuard</p>
            <p className="text-[10px] text-slate-400 leading-tight">MLOps Pipeline</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest px-2 mb-2">
          Navigation
        </p>
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-sky-600/20 text-sky-400 border border-sky-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={16} className={isActive ? 'text-sky-400' : 'text-slate-500'} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* System status */}
      <div className="px-4 py-4 border-t border-slate-800 space-y-2">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2">
          System Status
        </p>
        <StatusRow label="API"        ok={health?.status === 'healthy'} />
        <StatusRow label="Model"      ok={health?.model_loaded === true} />
        <StatusRow label="Redis Cache" ok={health?.redis_connected === true} />
      </div>
    </aside>
  )
}

function StatusRow({ label, ok }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-400">{label}</span>
      <div className="flex items-center gap-1.5">
        <Circle
          size={7}
          className={ok ? 'text-green-400 fill-green-400' : 'text-red-400 fill-red-400'}
        />
        <span className={`text-[11px] font-medium ${ok ? 'text-green-400' : 'text-red-400'}`}>
          {ok == null ? '…' : ok ? 'Online' : 'Offline'}
        </span>
      </div>
    </div>
  )
}
