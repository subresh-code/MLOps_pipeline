import { useState } from 'react'
import { Database, PlayCircle } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell, CartesianGrid
} from 'recharts'
import { getAnalyticsQueries } from '../api'

const CHART_KEYS = ['fraud_rate_by_product', 'fraud_rate_by_card_type']

const QUERY_META = {
  fraud_rate_by_product:     { label: 'Fraud Rate by Product Code',           chart: true,  xKey: 'ProductCD',  yKey: 'fraud_rate' },
  amount_by_fraud:           { label: 'Avg Transaction Amount: Fraud vs Legit', chart: false },
  fraud_rate_by_card_type:   { label: 'Fraud Rate by Card Type',              chart: true,  xKey: 'card4',      yKey: 'fraud_rate' },
  c_features_fraud_vs_legit: { label: 'C-Features: Fraud vs Legitimate',      chart: false },
  summary:                   { label: 'Overall Summary',                       chart: false },
}

const BAR_COLORS = ['#38bdf8', '#818cf8', '#34d399', '#fbbf24', '#f87171']

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-slate-300 font-medium mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(4) : p.value}</p>
      ))}
    </div>
  )
}

export default function Analytics() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const run = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data: res } = await getAnalyticsQueries()
      setData(res)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Columnar Analytics</h1>
        <p className="text-slate-400 text-sm mt-1">
          SQL aggregations running against MariaDB ColumnStore — 590,540 transactions
        </p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Database size={18} className="text-purple-400" />
          <div>
            <p className="text-sm font-medium">MariaDB ColumnStore</p>
            <p className="text-xs text-slate-400">5 analytical queries · fraud rates, amounts, card types, C-features</p>
          </div>
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="flex items-center gap-2 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors text-sm"
        >
          <PlayCircle size={15} />
          {loading ? 'Querying…' : 'Run Queries'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-600/50 rounded-xl p-4 text-red-300 text-sm">
          <p className="font-semibold mb-1">Query failed</p>
          <p className="text-xs opacity-80">{error}</p>
          <p className="text-xs text-red-400/70 mt-2">
            Run <code className="bg-red-900/40 px-1 rounded">make load-columnstore</code> first to load data into ColumnStore.
          </p>
        </div>
      )}

      {data && (
        <div className="space-y-5">
          {/* Charts for fraud rate queries */}
          {CHART_KEYS.filter(k => data[k]?.length).length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {CHART_KEYS.map(key => {
                const rows = data[key]
                const meta = QUERY_META[key]
                if (!rows?.length || !meta.chart) return null
                return (
                  <div key={key} className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <p className="text-sm font-semibold text-white mb-4">{meta.label}</p>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={rows} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey={meta.xKey} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                        <YAxis tickFormatter={v => `${(v * 100).toFixed(1)}%`} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey={meta.yKey} radius={[4, 4, 0, 0]}>
                          {rows.map((_, i) => (
                            <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )
              })}
            </div>
          )}

          {/* Tables for all queries */}
          {Object.entries(data).map(([key, rows]) => {
            const meta = QUERY_META[key] || { label: key }
            if (!Array.isArray(rows) || !rows.length) return null
            return (
              <div key={key} className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-slate-800 flex items-center gap-2">
                  <Database size={13} className="text-purple-400" />
                  <p className="text-sm font-semibold text-white">{meta.label}</p>
                  <span className="ml-auto text-[11px] text-slate-500">{rows.length} rows</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-slate-300">
                    <thead>
                      <tr className="border-b border-slate-800 bg-slate-800/50">
                        {Object.keys(rows[0]).map(col => (
                          <th key={col} className="text-left py-2 px-4 font-medium text-slate-400">{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row, i) => (
                        <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/40 transition-colors">
                          {Object.values(row).map((val, j) => (
                            <td key={j} className="py-2 px-4 font-mono">
                              {val === null
                                ? <span className="text-slate-600">NULL</span>
                                : typeof val === 'number' && val < 1 && val > 0
                                  ? <span className="text-sky-400">{(val * 100).toFixed(2)}%</span>
                                  : String(val)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
