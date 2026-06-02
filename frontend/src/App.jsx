import React from 'react'
import OrbitVisualizer from './components/OrbitVisualizer'
import LiveCharts from './components/LiveCharts'
import Alerts from './components/Alerts'
import HealthScore from './components/HealthScore'
import EventLogs from './components/EventLogs'

export default function App() {
  return (
    <div className="app">
      <header>
        <h1>Satellite Dashboard</h1>
      </header>
      <main>
        <section className="left">
          <OrbitVisualizer />
          <LiveCharts />
          <HealthScore />
        </section>
        <section className="right">
          <Alerts />
          <EventLogs />
        </section>
      </main>
    </div>
  )
}
