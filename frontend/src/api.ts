export interface RagCitation {
  index: number
  source: string
  title: string
  section: string
}

export interface RagSource extends RagCitation {
  citation: number
  id: string
  chunk_index: number
  score: number
  vector_score: number
  lexical_score: number
  cited: boolean
  text: string
}

export interface RagAnswer {
  question: string
  answer: string
  citations: RagCitation[]
  sources: RagSource[]
  model: string
  mode: string
  latency_ms: number
  warnings: string[]
}

export interface RagHealth {
  status: string
  ready: boolean
  chunks: number
  documents: number
  embedding_backend: string
  embedding_model: string
  vector_backend: string
  vector_store: string
  llm_provider: string
  llm_model: string
  version: string
}

export interface RagSourceRow {
  source: string
  title: string
  chunks: number
}

export interface RagSourcesPage {
  count: number
  total: number
  limit: number
  offset: number
  sources: RagSourceRow[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const HEALTH_TTL_MS = 8_000

let healthCache: { at: number; value: RagHealth } | null = null
let healthInFlight: Promise<RagHealth> | null = null
const queryInFlight = new Map<string, Promise<RagAnswer>>()

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string; hint?: string }
    return [body.detail, body.hint].filter(Boolean).join(' ') || `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

/** Deduplicate identical in-flight questions; the UI still guards its button. */
export function askKnowledge(question: string): Promise<RagAnswer> {
  const clean = question.trim()
  const key = clean.toLowerCase()
  const existing = queryInFlight.get(key)
  if (existing) return existing

  const request = fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: clean, top_k: 4 }),
  })
    .then(async (response) => {
      if (!response.ok) throw new Error(await parseError(response))
      return (await response.json()) as RagAnswer
    })
    .finally(() => queryInFlight.delete(key))

  queryInFlight.set(key, request)
  return request
}

/** Health is polled; cache it briefly and share one in-flight request. */
export function getHealth(force = false): Promise<RagHealth> {
  if (!force && healthCache && Date.now() - healthCache.at < HEALTH_TTL_MS) {
    return Promise.resolve(healthCache.value)
  }
  if (healthInFlight) return healthInFlight

  healthInFlight = fetch(`${API_BASE}/health`)
    .then(async (response) => {
      if (!response.ok) throw new Error(await parseError(response))
      const value = (await response.json()) as RagHealth
      healthCache = { at: Date.now(), value }
      return value
    })
    .finally(() => {
      healthInFlight = null
    })

  return healthInFlight
}

export async function getSources(limit = 20, offset = 0): Promise<RagSourcesPage> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  const response = await fetch(`${API_BASE}/sources?${params}`)
  if (!response.ok) throw new Error(await parseError(response))
  return (await response.json()) as RagSourcesPage
}

export function stripCitations(answer: string): string {
  return answer
    .replace(/\s*\[\d+(?:\s*,\s*\d+)*\]/g, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\s{2,}/g, ' ')
    .trim()
}
