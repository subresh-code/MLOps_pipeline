const palette = {
  sky:    { bg: 'bg-sky-600/10',    border: 'border-sky-600/30',    text: 'text-sky-400'    },
  green:  { bg: 'bg-green-600/10',  border: 'border-green-600/30',  text: 'text-green-400'  },
  amber:  { bg: 'bg-amber-600/10',  border: 'border-amber-600/30',  text: 'text-amber-400'  },
  red:    { bg: 'bg-red-600/10',    border: 'border-red-600/30',    text: 'text-red-400'    },
  purple: { bg: 'bg-purple-600/10', border: 'border-purple-600/30', text: 'text-purple-400' },
  slate:  { bg: 'bg-slate-800',     border: 'border-slate-700',     text: 'text-white'      },
}

export default function StatCard({ label, value, sub, color = 'slate', icon: Icon }) {
  const { bg, border, text } = palette[color] || palette.slate
  return (
    <div className={`rounded-xl border ${bg} ${border} p-4`}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs text-slate-400 font-medium">{label}</p>
        {Icon && <Icon size={14} className={`${text} opacity-60 shrink-0`} />}
      </div>
      <p className={`text-2xl font-bold mt-2 ${text}`}>{value ?? '—'}</p>
      {sub && <p className="text-[11px] text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}
