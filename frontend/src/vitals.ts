import type { Metric } from 'web-vitals'

type VitalPayload = {
  name: string
  value: number
  rating: string
  id: string
  navigationType: string
}

function report(metric: Metric) {
  const payload: VitalPayload = {
    name: metric.name,
    value: Math.round(metric.value * 1000) / 1000,
    rating: metric.rating,
    id: metric.id,
    navigationType: metric.navigationType,
  }
  const body = JSON.stringify(payload)

  if (navigator.sendBeacon) {
    const blob = new Blob([body], { type: 'application/json' })
    if (navigator.sendBeacon('/metrics/web-vitals', blob)) return
  }

  void fetch('/metrics/web-vitals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    keepalive: true,
  }).catch(() => {
    // Metrics must never break the app.
  })
}

/** Real-user LCP, INP, CLS, and TTFB, reported to the local API. */
export function initWebVitals() {
  const start = () => {
    void import('web-vitals').then(({ onCLS, onINP, onLCP, onTTFB }) => {
      onLCP(report)
      onINP(report)
      onCLS(report)
      onTTFB(report)
    })
  }
  if (document.readyState === 'complete') {
    window.setTimeout(start, 0)
  } else {
    window.addEventListener('load', () => window.setTimeout(start, 0), { once: true })
  }
}
