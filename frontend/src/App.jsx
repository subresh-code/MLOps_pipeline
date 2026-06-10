import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Predict from './pages/Predict'
import EDA from './pages/EDA'
import Monitor from './pages/Monitor'
import Metrics from './pages/Metrics'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 container mx-auto px-4 py-8 max-w-6xl">
        <Routes>
          <Route path="/" element={<Predict />} />
          <Route path="/eda" element={<EDA />} />
          <Route path="/monitor" element={<Monitor />} />
          <Route path="/metrics" element={<Metrics />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </main>
    </div>
  )
}
