import React, { useEffect, useRef, useState } from 'react'

function drawEarth(ctx, cx, cy, radius) {
  // simple Earth: gradient blue
  const grad = ctx.createRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 0.1, cx, cy, radius)
  grad.addColorStop(0, '#6fb3ff')
  grad.addColorStop(1, '#0b3b66')
  ctx.fillStyle = grad
  ctx.beginPath()
  ctx.arc(cx, cy, radius, 0, Math.PI * 2)
  ctx.fill()
  // equator line
  ctx.strokeStyle = 'rgba(255,255,255,0.15)'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.ellipse(cx, cy, radius * 0.98, radius * 0.25, 0, 0, Math.PI * 2)
  ctx.stroke()
}

export default function OrbitVisualizer({ altitude = 20000, inclination = 45, period = 5400, speedMultiplier = 1.0 }) {
  const canvasRef = useRef(null)
  const [running, setRunning] = useState(true)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let raf = null

    function resize() {
      const dpr = window.devicePixelRatio || 1
      canvas.width = canvas.clientWidth * dpr
      canvas.height = canvas.clientHeight * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    resize()
    window.addEventListener('resize', resize)

    const earthRadiusPx = Math.min(canvas.clientWidth, canvas.clientHeight) * 0.25
    const orbitRadius = earthRadiusPx + (altitude / 20000) * earthRadiusPx * 1.8

    function render(t) {
      if (!running) return
      ctx.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight)
      const cx = canvas.clientWidth / 2
      const cy = canvas.clientHeight / 2

      // draw Earth
      drawEarth(ctx, cx, cy, earthRadiusPx)

      // draw orbit ellipse (inclination projects to ellipse)
      const incRad = (inclination * Math.PI) / 180
      ctx.strokeStyle = 'rgba(255,255,255,0.25)'
      ctx.beginPath()
      ctx.ellipse(cx, cy, orbitRadius, orbitRadius * Math.cos(incRad), 0, 0, Math.PI * 2)
      ctx.stroke()

      // compute satellite position on orbit
      const now = Date.now() / 1000
      const ang = ((now * speedMultiplier) / period) * Math.PI * 2
      const x = cx + orbitRadius * Math.cos(ang)
      const y = cy + orbitRadius * Math.sin(ang) * Math.cos(incRad)

      // draw satellite
      ctx.fillStyle = '#ffcc00'
      ctx.beginPath()
      ctx.arc(x, y, 6, 0, Math.PI * 2)
      ctx.fill()

      // draw trail
      ctx.strokeStyle = 'rgba(255,204,0,0.6)'
      ctx.beginPath()
      const trailSteps = 40
      for (let i = 0; i < trailSteps; i++) {
        const a = ang - (i * 0.15)
        const tx = cx + orbitRadius * Math.cos(a)
        const ty = cy + orbitRadius * Math.sin(a) * Math.cos(incRad)
        if (i === 0) ctx.moveTo(tx, ty)
        else ctx.lineTo(tx, ty)
      }
      ctx.stroke()

      // overlay text
      ctx.fillStyle = '#fff'
      ctx.font = '12px sans-serif'
      ctx.fillText(`Altitude: ${altitude} km`, 12, 18)
      ctx.fillText(`Inclination: ${inclination}°`, 12, 36)
      ctx.fillText(`Period: ${Math.round(period)} s`, 12, 54)

      raf = requestAnimationFrame(render)
    }

    raf = requestAnimationFrame(render)

    return () => {
      window.removeEventListener('resize', resize)
      if (raf) cancelAnimationFrame(raf)
    }
  }, [altitude, inclination, period, running, speedMultiplier])

  return (
    <div className="card">
      <h2>Orbit Visualizer</h2>
      <div style={{ height: 320 }}>
        <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
      </div>
      <div style={{ marginTop: 8 }}>
        <button onClick={() => setRunning(r => !r)}>{running ? 'Pause' : 'Resume'}</button>
      </div>
    </div>
  )
}
