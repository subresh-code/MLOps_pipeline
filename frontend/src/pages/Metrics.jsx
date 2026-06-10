import { useEffect, useState } from 'react'
import { getMetrics, getReportFigures, staticUrl } from '../api'
import StatCard from '../components/StatCard'

export default function Metrics() {
  const [metrics, setMetrics] = useState(null)
  const [figures, setFigures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([getMetrics(), getReportFigures()])
      .then(([m, f]) => {
        setMetrics(m.data)
        setFigures(f.data.figures || [])
      })
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400">Loading…</div>
  if (error) return <div className="bg-red-900/40 border border-red-600 rounded-lg p-4 text-red-300 text-sm">{error}</div>

  const fmt = (v) => (typeof v === 'number' ? v.toFixed(4) : v ?? '—')

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Model Performance</h1>
      <p className="text-slate-400 text-sm mb-6">XGBoost classifier trained on IEEE-CIS Fraud Detection dataset</p>

      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <StatCard label="AUC-ROC" value={fmt(metrics.auc_roc)} color="sky" sub="Higher is better" />
          <StatCard label="Average Precision" value={fmt(metrics.average_precision)} color="purple" />
          <StatCard label="Precision" value={fmt(metrics.precision)} color="green" sub="Fraud predictions correct" />
          <StatCard label="Recall" value={fmt(metrics.recall)} color="amber" sub="Frauds caught" />
          <StatCard label="F1 Score" value={fmt(metrics.f1)} color="sky" />
          <StatCard label="Train Size" value={metrics.train_size?.toLocaleString()} />
          <StatCard label="Test Size" value={metrics.test_size?.toLocaleString()} />
          <StatCard label="Fraud Rate (test)" value={metrics.fraud_rate_test ? `${(metrics.fraud_rate_test * 100).toFixed(2)}%` : '—'} color="red" />
        </div>
      )}

      <h2 className="text-lg font-semibold mb-4">Evaluation Plots</h2>
      {figures.length === 0 ? (
        <p className="text-slate-400 text-sm">No figures found. Run <code className="bg-slate-700 px-1 rounded">make evaluate</code> first.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {figures.map((fname) => (
            <div key={fname} className="bg-slate-800 rounded-lg overflow-hidden">
              <img
                src={staticUrl(`/static/reports/${fname}`)}
                alt={fname.replace(/_/g, ' ').replace('.png', '')}
                className="w-full object-contain bg-white"
                loading="lazy"
              />
              <p className="text-xs text-slate-400 px-3 py-2">
                {fname.replace(/_/g, ' ').replace('.png', '')}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
