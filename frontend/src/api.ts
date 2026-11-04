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

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string; hint?: string }
    return [body.detail, body.hint].filter(Boolean).join(' ') || `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

export async function askKnowledge(question: string): Promise<RagAnswer> {
  const response = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: 4 }),
  })
  if (!response.ok) throw new Error(await parseError(response))
  return (await response.json()) as RagAnswer
}

export async function getHealth(): Promise<RagHealth> {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) throw new Error(await parseError(response))
  return (await response.json()) as RagHealth
}

export function stripCitations(answer: string): string {
  return answer
    .replace(/\s*\[\d+(?:\s*,\s*\d+)*\]/g, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\s{2,}/g, ' ')
    .trim()
}
