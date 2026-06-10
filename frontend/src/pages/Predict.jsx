import { useState } from 'react'
import { predict } from '../api'

const DEFAULTS = {
  TransactionAmt: 100,
  ProductCD: 'W',
  card4: 'visa',
  card6: 'debit',
  P_emaildomain: 'gmail.com',
  C1: 1,
  C2: 1,
  C9: 0,
  C11: 1,
  D1: 0,
  D2: 0,
  addr1: 299,
  addr2: 87,
}

export default function Predict() {
  const [form, setForm] = useState(DEFAULTS)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((f) => ({ ...f, [name]: isNaN(value) || value === '' ? value : Number(value) }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const { data } = await predict(form)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const pct = result ? Math.round(result.fraud_probability * 100) : 0
  const riskColor = pct >= 70 ? 'text-red-400' : pct >= 40 ? 'text-amber-400' : 'text-green-400'

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Fraud Prediction</h1>
      <p className="text-slate-400 text-sm mb-6">
        Submit a transaction to score it against the deployed XGBoost model.
      </p>

      <form onSubmit={handleSubmit} className="bg-slate-800 rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Transaction Amount ($)" name="TransactionAmt" type="number" value={form.TransactionAmt} onChange={handleChange} />
          <Field label="Product Code" name="ProductCD" value={form.ProductCD} onChange={handleChange} placeholder="W / H / C / S / R" />
          <Field label="Card Network" name="card4" value={form.card4} onChange={handleChange} placeholder="visa / mastercard / etc." />
          <Field label="Card Type" name="card6" value={form.card6} onChange={handleChange} placeholder="debit / credit" />
          <Field label="Purchaser Email Domain" name="P_emaildomain" value={form.P_emaildomain} onChange={handleChange} />
          <Field label="Address 1" name="addr1" type="number" value={form.addr1} onChange={handleChange} />
          <Field label="C1 (count feature)" name="C1" type="number" value={form.C1} onChange={handleChange} />
          <Field label="C2 (count feature)" name="C2" type="number" value={form.C2} onChange={handleChange} />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-sky-600 hover:bg-sky-500 disabled:bg-slate-600 text-white font-semibold py-2.5 rounded-lg transition-colors"
        >
          {loading ? 'Scoring…' : 'Predict Fraud Risk'}
        </button>
      </form>

      {error && (
        <div className="mt-4 bg-red-900/40 border border-red-600 rounded-lg p-4 text-red-300 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 bg-slate-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Result</h2>
            {result.cached && (
              <span className="text-xs bg-purple-800 text-purple-200 px-2 py-0.5 rounded-full">
                Redis cache hit
              </span>
            )}
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-slate-400 mb-1">Fraud Probability</p>
              <p className={`text-4xl font-bold ${riskColor}`}>{pct}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">Verdict</p>
              <span className={`inline-block mt-1 px-3 py-1 rounded-full text-sm font-semibold ${result.is_fraud ? 'bg-red-900 text-red-300' : 'bg-green-900 text-green-300'}`}>
                {result.is_fraud ? 'FRAUD' : 'LEGITIMATE'}
              </span>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">Confidence</p>
              <p className="text-4xl font-bold text-white">{Math.round(result.confidence * 100)}%</p>
            </div>
          </div>
          {/* Risk bar */}
          <div className="mt-4">
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${pct >= 70 ? 'bg-red-500' : pct >= 40 ? 'bg-amber-500' : 'bg-green-500'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>Low risk</span>
              <span>High risk</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, name, type = 'text', value, onChange, placeholder }) {
  return (
    <div>
      <label className="block text-xs text-slate-400 mb-1">{label}</label>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
      />
    </div>
  )
}
