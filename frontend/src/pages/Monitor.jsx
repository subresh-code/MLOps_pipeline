import { useState } from 'react'
import { getDriftSummary } from '../api'
import StatCard from '../components/StatCard'

const SCENARIOS = [
  { value: '', label: 'Actual (test data)' },
  { value: 'a', label: 'Scenario A — Feature / data drift' },
  { value: 'b', label: 'Scenario B — Concept drift (label flip)' },
  { value: 'c', label: 'Scenario C — Covariate shift (no device data)' },
]

export default function Monitor() {
  const [scenario, setScenario] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const run = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const { data } = await getDriftSummary(scenario || null)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Drift Monitoring</h1>
      <p className="text-slate-400 text-sm mb-6">
        Compare feature distributions between the training reference and a selected data window.
      </p>

      <div className="bg-slate-800 rounded-lg p-6 mb-6">
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-xs text-slate-400 mb-1">Data scenario</label>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
            >
              {SCENARIOS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <button
            onClick={run}
            disabled={loading}
            className="bg-sky-600 hover:bg-sky-500 disabled:bg-slate-600 text-white font-semibold px-5 py-2 rounded-lg transition-colors text-sm"
          >
            {loading ? 'Running…' : 'Run Monitor'}
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Scenarios A–C require synthetic drift data. Run <code className="bg-slate-700 px-1 rounded">make generate-drift</code> first.
        </p>
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-600 rounded-lg p-4 text-red-300 text-sm mb-4">
          {error}
        </div>
      )}

      {result && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <StatCard
              label="Drift Detected"
              value={result.drift_detected ? 'YES' : 'NO'}
              color={result.drift_detected ? 'red' : 'green'}
            />
            <StatCard
              label="Drift Share"
              value={`${Math.round((result.drift_share || 0) * 100)}%`}
              color={result.drift_share > 0.2 ? 'red' : 'green'}
              sub="of features drifted"
            />
            <StatCard label="Features Analyzed" value={result.number_of_features ?? '—'} />
            <StatCard label="Drifted Features" value={result.number_of_drifted_features ?? '—'} color="amber" />
          </div>

          {result.drifted_features && result.drifted_features.length > 0 && (
            <div className="bg-slate-800 rounded-lg p-4">
              <h2 className="text-sm font-semibold mb-3 text-slate-300">
                Drifted Features ({result.drifted_features.length})
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-slate-300">
                  <thead>
                    <tr className="border-b border-slate-700 text-slate-400">
                      <th className="text-left py-1.5 pr-4">Feature</th>
                      <th className="text-right pr-4">p-value</th>
                      <th className="text-right pr-4">Threshold</th>
                      <th className="text-left">Test</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.drifted_features.slice(0, 30).map((f, i) => (
                      <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="py-1 pr-4 font-mono">{f.feature}</td>
                        <td className="text-right pr-4 text-red-400">{f.p_value?.toFixed(6) ?? f.change_std?.toFixed(4)}</td>
                        <td className="text-right pr-4">{f.threshold ?? '0.05'}</td>
                        <td className="text-slate-400">{f.stattest || 'statistical'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {result.drifted_features.length > 30 && (
                  <p className="text-xs text-slate-500 mt-2">
                    …and {result.drifted_features.length - 30} more
                  </p>
                )}
              </div>
            </div>
          )}

          <p className="text-xs text-slate-500 mt-3">
            Method: {result.method} · Reference: {result.reference_rows?.toLocaleString()} rows · Current: {result.current_rows?.toLocaleString()} rows
          </p>
        </>
      )}
    </div>
  )
}
