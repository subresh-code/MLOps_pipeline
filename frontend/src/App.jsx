import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Predict from './pages/Predict'
import EDA from './pages/EDA'
import Monitor from './pages/Monitor'
import Metrics from './pages/Metrics'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <div className="min-h-screen flex bg-slate-950 text-white">
      <Sidebar />
      <div className="flex-1 ml-60 min-h-screen overflow-x-hidden">
        <main className="p-6 max-w-6xl">
          <Routes>
            <Route path="/"          element={<Dashboard />} />
            <Route path="/predict"   element={<Predict />} />
            <Route path="/eda"       element={<EDA />} />
            <Route path="/metrics"   element={<Metrics />} />
            <Route path="/monitor"   element={<Monitor />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
