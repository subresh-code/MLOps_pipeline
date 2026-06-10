import { useEffect, useState } from 'react'
import { getEdaSummary, getEdaFigures, staticUrl } from '../api'
import StatCard from '../components/StatCard'

export default function EDA() {
  const [summary, setSummary] = useState(null)
  const [figures, setFigures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([getEdaSummary(), getEdaFigures()])
      .then(([s, f]) => {
        setSummary(s.data)
        setFigures(f.data.figures || [])
      })
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />
  if (error) return <ErrorBox msg={error} />

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Exploratory Data Analysis</h1>
      <p className="text-slate-400 text-sm mb-6">IEEE-CIS Fraud Detection dataset — 590,540 e-commerce transactions</p>

      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Transactions" value={summary.total_transactions?.toLocaleString()} />
          <StatCard label="Fraud Cases" value={summary.fraud_count?.toLocaleString()} color="red" />
          <StatCard label="Fraud Rate" value={`${summary.fraud_rate_pct}%`} color="amber" sub="Severe class imbalance" />
          <StatCard label="Features" value={summary.total_features} color="purple" />
          <StatCard label="Median Legit Amount" value={`$${summary.median_amount_legit}`} color="green" />
          <StatCard label="Median Fraud Amount" value={`$${summary.median_amount_fraud}`} color="red" />
          <StatCard label="Features w/ Missing" value={summary.features_with_missing} color="amber" sub="Mostly identity cols" />
          <StatCard label="Peak Fraud Hour" value={`${summary.peak_fraud_hour}:00`} color="sky" sub="UTC" />
        </div>
      )}

      <h2 className="text-lg font-semibold mb-4">EDA Figures</h2>
      {figures.length === 0 ? (
        <p className="text-slate-400 text-sm">No figures found. Run the EDA notebook first.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {figures.map((fname) => (
            <div key={fname} className="bg-slate-800 rounded-lg overflow-hidden">
              <img
                src={staticUrl(`/static/eda/${fname}`)}
                alt={fname.replace(/^\d+_/, '').replace(/_/g, ' ').replace('.png', '')}
                className="w-full object-contain bg-white"
                loading="lazy"
              />
              <p className="text-xs text-slate-400 px-3 py-2">
                {fname.replace(/^\d+_/, '').replace(/_/g, ' ').replace('.png', '')}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Spinner() {
  return (
    <div className="flex items-center justify-center h-64 text-slate-400">
      Loading…
    </div>
  )
}

function ErrorBox({ msg }) {
  return (
    <div className="bg-red-900/40 border border-red-600 rounded-lg p-4 text-red-300 text-sm">
      {msg}
    </div>
  )
}
