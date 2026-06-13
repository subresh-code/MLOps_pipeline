import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Zap, BarChart2, Activity, Database, LineChart,
  ArrowRight, ShieldCheck, ShieldAlert, Server,
  Cpu, GitBranch, Clock
} from 'lucide-react'
import { getHealth, getMetrics, getModelInfo } from '../api'
import StatCard from '../components/StatCard'

export default function Dashboard() {
  const [health,    setHealth]    = useState(null)
  const [metrics,   setMetrics]   = useState(null)
  const [modelInfo, setModelInfo] = useState(null)

  useEffect(() => {
    getHealth().then(r => setHealth(r.data)).catch(() => {})
    getMetrics().then(r => setMetrics(r.data)).catch(() => {})
    getModelInfo().then(r => setModelInfo(r.data)).catch(() => {})
  }, [])

  const fmt = (v, dec = 3) => typeof v === 'number' ? v.toFixed(dec) : '—'

  return (
    <div className="space-y-8">

      {/* ── Header ── */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-slate-400 mt-1 text-sm">
          IEEE-CIS Fraud Detection · XGBoost · MLOps Pipeline
        </p>
      </div>

      {/* ── System Health Banner ── */}
      <div className={`rounded-xl border px-5 py-4 flex items-center gap-4 ${
        health?.status === 'healthy'
          ? 'bg-green-600/10 border-green-600/30'
          : 'bg-red-600/10 border-red-600/30'
      }`}>
        {health?.status === 'healthy'
          ? <ShieldCheck size={22} className="text-green-400 shrink-0" />
          : <ShieldAlert size={22} className="text-red-400 shrink-0" />}
        <div className="flex-1">
          <p className={`text-sm font-semibold ${health?.status === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
            {health?.status === 'healthy' ? 'All systems operational' : 'System health check failed'}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            API {health?.status ?? '…'} · Model {health?.model_loaded ? 'loaded' : 'not loaded'} · Redis {health?.redis_connected ? 'connected' : 'disconnected'}
          </p>
        </div>
        <div className="flex gap-4 text-xs text-slate-400">
          <span>:8000 API</span>
          <span>:5001 MLflow</span>
          <span>:8080 Airflow</span>
        </div>
      </div>

      {/* ── Model Metrics ── */}
      <section>
        <SectionTitle icon={BarChart2} title="Model Performance" sub="XGBoost — temporal 80/20 test split" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="AUC-ROC"          value={fmt(metrics?.auc_roc)}           color="sky"    sub="Primary metric" />
          <StatCard label="Average Precision" value={fmt(metrics?.average_precision)} color="purple" sub="Imbalanced classes" />
          <StatCard label="Recall"            value={fmt(metrics?.recall)}            color="amber"  sub="Frauds caught" />
          <StatCard label="Precision"         value={fmt(metrics?.precision)}         color="green"  sub="Correct alerts" />
          <StatCard label="F1 Score"          value={fmt(metrics?.f1)}                color="slate" />
          <StatCard label="Train Rows"        value={metrics?.train_size?.toLocaleString()} color="slate" />
          <StatCard label="Test Rows"         value={metrics?.test_size?.toLocaleString()}  color="slate" />
          <StatCard
            label="Fraud Rate (test)"
            value={metrics?.fraud_rate_test ? `${(metrics.fraud_rate_test * 100).toFixed(2)}%` : '—'}
            color="red"
            sub="3.5% · 27:1 imbalance"
          />
        </div>
      </section>

      {/* ── Stack Info ── */}
      <section>
        <SectionTitle icon={Server} title="Stack" sub="Containerised services" />
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <StackCard icon={Cpu}       title="XGBoost Classifier"   desc={modelInfo?.model_type ?? 'XGBClassifier'} badge="Model" color="sky" />
          <StackCard icon={Server}    title="FastAPI + Uvicorn"     desc="REST prediction API · port 8000" badge="Serving" color="green" />
          <StackCard icon={Database}  title="MariaDB ColumnStore"  desc="Columnar analytical store · port 3307" badge="Storage" color="purple" />
          <StackCard icon={Activity}  title="Redis 7"              desc="Prediction cache · TTL 3600s" badge="Cache" color="amber" />
          <StackCard icon={GitBranch} title="Apache Airflow 2.9"   desc="4-task DAG orchestration · port 8080" badge="Orchestration" color="sky" />
          <StackCard icon={BarChart2} title="MLflow"               desc="Experiment tracking · port 5001" badge="Tracking" color="purple" />
        </div>
      </section>

      {/* ── Quick Links ── */}
      <section>
        <SectionTitle icon={Zap} title="Quick Actions" />
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <QuickLink to="/predict"   icon={Zap}      label="Score a transaction"  desc="Submit a single transaction for fraud scoring" color="sky" />
          <QuickLink to="/metrics"   icon={BarChart2} label="View model metrics"   desc="ROC curve, PR curve, confusion matrix" color="purple" />
          <QuickLink to="/eda"       icon={LineChart}  label="Explore EDA"         desc="590k transactions, class imbalance analysis" color="green" />
          <QuickLink to="/monitor"   icon={Activity}  label="Run drift monitor"    desc="Compare feature distributions (3 scenarios)" color="amber" />
          <QuickLink to="/analytics" icon={Database}  label="ColumnStore analytics" desc="SQL aggregations on 590k rows" color="purple" />
          <ExternalLink href="http://localhost:5001" icon={BarChart2} label="MLflow UI"  desc="Experiment runs, parameters, artefacts" />
        </div>
      </section>

      {/* ── Dataset Facts ── */}
      <section>
        <SectionTitle icon={Clock} title="Dataset" sub="IEEE-CIS Fraud Detection" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total Transactions" value="590,540"  color="slate" />
          <StatCard label="Fraud Cases"         value="20,663"  color="red"   sub="3.5% fraud rate" />
          <StatCard label="Class Imbalance"     value="27 : 1"  color="amber" sub="scale_pos_weight=20" />
          <StatCard label="Raw Features"        value="434"     color="slate" sub="After LEFT JOIN" />
        </div>
      </section>

    </div>
  )
}

function SectionTitle({ icon: Icon, title, sub }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon size={16} className="text-sky-400" />
      <h2 className="text-base font-semibold text-white">{title}</h2>
      {sub && <span className="text-xs text-slate-500">{sub}</span>}
    </div>
  )
}

function StackCard({ icon: Icon, title, desc, badge, color }) {
  const badgeColors = {
    sky:    'bg-sky-600/20 text-sky-400',
    green:  'bg-green-600/20 text-green-400',
    purple: 'bg-purple-600/20 text-purple-400',
    amber:  'bg-amber-600/20 text-amber-400',
  }
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-start gap-3">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${badgeColors[color]}`}>
        <Icon size={15} />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium text-white truncate">{title}</p>
        <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{desc}</p>
        <span className={`inline-block text-[10px] font-semibold mt-1.5 px-1.5 py-0.5 rounded ${badgeColors[color]}`}>
          {badge}
        </span>
      </div>
    </div>
  )
}

function QuickLink({ to, icon: Icon, label, desc, color }) {
  const cls = {
    sky:    'hover:border-sky-600/50 hover:bg-sky-600/5',
    purple: 'hover:border-purple-600/50 hover:bg-purple-600/5',
    green:  'hover:border-green-600/50 hover:bg-green-600/5',
    amber:  'hover:border-amber-600/50 hover:bg-amber-600/5',
  }[color] || ''
  return (
    <Link
      to={to}
      className={`bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-3 transition-all group ${cls}`}
    >
      <Icon size={16} className="text-slate-400 group-hover:text-sky-400 shrink-0 transition-colors" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white">{label}</p>
        <p className="text-[11px] text-slate-500 truncate">{desc}</p>
      </div>
      <ArrowRight size={14} className="text-slate-600 group-hover:text-sky-400 shrink-0 transition-colors" />
    </Link>
  )
}

function ExternalLink({ href, icon: Icon, label, desc }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-3 hover:border-slate-600 hover:bg-slate-800/50 transition-all group"
    >
      <Icon size={16} className="text-slate-400 group-hover:text-white shrink-0 transition-colors" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white">{label}</p>
        <p className="text-[11px] text-slate-500 truncate">{desc}</p>
      </div>
      <ArrowRight size={14} className="text-slate-600 group-hover:text-white shrink-0 transition-colors" />
    </a>
  )
}
