import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE })

export const predict = (data) => api.post('/predict', data)
export const getHealth = () => api.get('/health')
export const getModelInfo = () => api.get('/model-info')
export const getEdaSummary = () => api.get('/eda-summary')
export const getEdaFigures = () => api.get('/eda-figures')
export const getReportFigures = () => api.get('/report-figures')
export const getMetrics = () => api.get('/metrics')
export const getDriftSummary = (scenario) =>
  api.get('/drift-summary' + (scenario ? `?scenario=${scenario}` : ''))
export const getAnalyticsQueries = () => api.get('/analytics/queries')

export const staticUrl = (path) => `${BASE}${path}`
