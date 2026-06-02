import React, { useEffect, useState } from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'
import { fetchTelemetry } from '../api'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

export default function LiveCharts() {
  const [points, setPoints] = useState([])

  useEffect(() => {
    let mounted = true
    async function load() {
      const data = await fetchTelemetry(100)
      if (mounted) setPoints(data)
    }
    load()
    const id = setInterval(load, 2000)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  const labels = points.map(p => new Date(p.timestamp).toLocaleTimeString())
  const battery = points.map(p => p.battery_voltage)
  const temp = points.map(p => p.cpu_temperature)

  const data = {
    labels,
    datasets: [
      { label: 'Battery (V)', data: battery, borderColor: '#2b8cff', tension: 0.3 },
      { label: 'CPU Temp (°C)', data: temp, borderColor: '#ff7b00', tension: 0.3 },
    ],
  }

  return (
    <div className="card">
      <h2>Live Telemetry</h2>
      <Line data={data} />
    </div>
  )
}
