import axios from 'axios'

const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000') + '/api/v1'

export async function fetchTelemetry(limit = 50) {
  const resp = await axios.get(`${API_BASE}/telemetry?limit=${limit}`)
  return resp.data
}

export async function fetchAnomalies(limit = 50) {
  const resp = await axios.get(`${API_BASE}/anomalies?limit=${limit}`)
  return resp.data
}

export async function fetchHealth(satelliteId = 'SAT-001') {
  // Simple synthetic health score via anomalies recent count
  const resp = await axios.get(`${API_BASE}/anomalies?limit=100`)
  const anomalies = resp.data || []
  const recent = anomalies.filter(a => a.satellite_id === satelliteId)
  const score = Math.max(0, 100 - recent.length)
  return { satellite_id: satelliteId, score }
}

export async function fetchEvents(limit = 100) {
  const resp = await axios.get(`${API_BASE}/anomalies?limit=${limit}`)
  return resp.data
}
