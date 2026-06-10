export default function StatCard({ label, value, sub, color = 'sky' }) {
  const ring = {
    sky: 'border-sky-600',
    green: 'border-green-600',
    red: 'border-red-500',
    amber: 'border-amber-500',
    purple: 'border-purple-500',
  }[color] ?? 'border-sky-600'

  return (
    <div className={`bg-slate-800 border ${ring} rounded-lg p-4`}>
      <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  )
}
