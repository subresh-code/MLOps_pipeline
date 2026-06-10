import { useState } from 'react'
import { getAnalyticsQueries } from '../api'

const QUERY_LABELS = {
  fraud_rate_by_product: 'Fraud Rate by Product Code',
  amount_by_fraud: 'Transaction Amount: Fraud vs Legitimate',
  fraud_rate_by_card_type: 'Fraud Rate by Card Type',
  c_features_fraud_vs_legit: 'C-Features: Fraud vs Legitimate',
  summary: 'Overall Summary',
}

export default function Analytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

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
    <div>
      <h1 className="text-2xl font-bold mb-1">Columnar Analytics</h1>
      <p className="text-slate-400 text-sm mb-2">
        SQL analytical queries running against MariaDB ColumnStore.
      </p>
      <p className="text-xs text-slate-500 mb-6">
        Requires <code className="bg-slate-700 px-1 rounded">make load-columnstore</code> to be run first (loads ~590k rows into ColumnStore).
      </p>

      <button
        onClick={run}
        disabled={loading}
        className="mb-6 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-600 text-white font-semibold px-5 py-2 rounded-lg transition-colors text-sm"
      >
        {loading ? 'Querying ColumnStore…' : 'Run Analytical Queries'}
      </button>

      {error && (
        <div className="bg-red-900/40 border border-red-600 rounded-lg p-4 text-red-300 text-sm mb-4">
          {error}
        </div>
      )}

      {data && Object.entries(data).map(([key, rows]) => (
        <div key={key} className="bg-slate-800 rounded-lg p-4 mb-4">
          <h2 className="text-sm font-semibold text-sky-400 mb-3">
            {QUERY_LABELS[key] || key}
          </h2>
          {Array.isArray(rows) && rows.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-slate-300">
                <thead>
                  <tr className="border-b border-slate-700 text-slate-400">
                    {Object.keys(rows[0]).map((col) => (
                      <th key={col} className="text-left py-1.5 pr-4 font-medium">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      {Object.values(row).map((val, j) => (
                        <td key={j} className="py-1 pr-4 font-mono">
                          {val === null ? <span className="text-slate-500">NULL</span> : String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-slate-500 text-xs">No data</p>
          )}
        </div>
      ))}
    </div>
  )
}
