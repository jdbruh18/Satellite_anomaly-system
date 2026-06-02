import React, { useEffect, useState } from 'react'
import { fetchEvents } from '../api'

export default function EventLogs() {
  const [events, setEvents] = useState([])

  useEffect(() => {
    let mounted = true
    async function load() {
      const data = await fetchEvents(100)
      if (mounted) setEvents(data)
    }
    load()
    const id = setInterval(load, 3000)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  return (
    <div className="card">
      <h2>Event Logs</h2>
      <div className="logs">
        {events.map(e => (
          <div key={e.id} className="log">
            <div><strong>{e.reason}</strong> — {e.anomaly_types?.join(', ')}</div>
            <div className="log-meta">{new Date(e.created_at).toLocaleString()} • severity: {e.severity}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
