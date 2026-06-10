import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Predict' },
  { to: '/eda', label: 'EDA' },
  { to: '/metrics', label: 'Metrics' },
  { to: '/monitor', label: 'Monitor' },
  { to: '/analytics', label: 'Analytics' },
]

export default function Navbar() {
  return (
    <nav className="bg-slate-900 border-b border-slate-700 sticky top-0 z-10">
      <div className="container mx-auto px-4 max-w-6xl flex items-center justify-between h-14">
        <span className="font-semibold text-sky-400 text-sm tracking-wide">
          Fraud Detection · MLOps
        </span>
        <div className="flex gap-1">
          {links.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sky-600 text-white'
                    : 'text-slate-300 hover:text-white hover:bg-slate-700'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
