import React, { useEffect, useState } from 'react'
import { fetchHealth } from '../api'

export default function HealthScore() {
  const [score, setScore] = useState({ satellite_id: 'SAT-001', score: 100 })

  useEffect(() => {
    let mounted = true
    async function load() {
      const s = await fetchHealth(score.satellite_id)
      if (mounted) setScore(s)
    }
    load()
    const id = setInterval(load, 5000)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  return (
    <div className="card">
      <h2>Satellite Health</h2>
      <div className="health-score">{score.score}%</div>
      <div className="health-meta">Satellite: {score.satellite_id}</div>
    </div>
  )
}
