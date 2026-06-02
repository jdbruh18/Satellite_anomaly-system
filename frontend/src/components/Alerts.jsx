import React, { useEffect, useState } from 'react'
import { fetchAnomalies } from '../api'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    let mounted = true
    async function load() {
      const data = await fetchAnomalies(50)
      if (mounted) setAlerts(data)
    }
    load()
    const id = setInterval(load, 2000)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  return (
    <div className="card">
      <h2>Anomaly Alerts</h2>
      <ul className="alerts">
        {alerts.map(a => (
          <li key={a.id} className={`alert ${a.severity?.toLowerCase() || 'info'}`}>
            <div className="alert-header">
              <strong>{a.severity}</strong> — {a.reason}
            </div>
            <div className="alert-body">{a.explanation || a.anomaly_types.join(', ')}</div>
            <div className="alert-meta">satellite: {a.telemetry?.satellite_id || a.satellite_id} • score: {a.score}</div>
          </li>
        ))}
      </ul>
    </div>
  )
}
