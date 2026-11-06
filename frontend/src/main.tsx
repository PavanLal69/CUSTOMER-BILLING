import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { initWebVitals } from './vitals'
import './styles.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

initWebVitals()
