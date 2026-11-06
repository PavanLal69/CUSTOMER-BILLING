import { ArrowUp, BookOpen, Check, ChevronDown, CornerDownLeft, RotateCcw } from 'lucide-react'
import { memo, useRef, useState, type RefObject } from 'react'
import { askKnowledge, stripCitations, type RagAnswer, type RagHealth } from '../api'
import { assistantSuggestions } from '../data'

interface AssistantPanelProps {
  health: RagHealth | null
  inputRef: RefObject<HTMLTextAreaElement>
  onUseReply: (text: string) => void
}

function AssistantPanelBase({ health, inputRef, onUseReply }: AssistantPanelProps) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<RagAnswer | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [openSource, setOpenSource] = useState<string | null>(null)
  const inFlight = useRef(false)
  const requestId = useRef(0)

  const ask = async (prompt = question) => {
    const clean = prompt.trim()
    if (!clean || inFlight.current) return

    inFlight.current = true
    const id = ++requestId.current

    setQuestion(clean)
    setLoading(true)
    setError(null)
    setAnswer(null)
    setOpenSource(null)
    try {
      const result = await askKnowledge(clean)
      if (id !== requestId.current) return
      setAnswer(result)
    } catch (reason) {
      if (id !== requestId.current) return
      setError(reason instanceof Error ? reason.message : 'The knowledge API is unavailable.')
    } finally {
      if (id === requestId.current) {
        inFlight.current = false
        setLoading(false)
      }
    }
  }

  const reset = () => {
    requestId.current += 1
    inFlight.current = false
    setLoading(false)
    setQuestion('')
    setAnswer(null)
    setError(null)
    setOpenSource(null)
    inputRef.current?.focus()
  }

  const citedSources = answer
    ? answer.sources.filter((source) => source.cited || answer.citations.length === 0).slice(0, 3)
    : []

  return (
    <section className="cx-rail-card cx-ai" aria-label="Knowledge assistant">
      <div className="cx-ai__head">
        <span className="cx-ai__icon" aria-hidden>
          <BookOpen size={15} strokeWidth={1.8} />
        </span>
        <span className="cx-ai__title">
          <strong>Northstar AI</strong>
          <span>Answers from internal policy</span>
        </span>
        <span className="cx-ai__state" data-ready={health?.ready ? 'true' : undefined}>
          <span className="cx-ai__dot" aria-hidden />
          {health?.ready ? 'Local' : 'Offline'}
        </span>
      </div>

      {!answer && !loading && !error && (
        <div className="cx-ai__intro">
          <p>Ask the support playbook, security policy, or product FAQ. Every answer comes with a source.</p>
          <div className="cx-ai__suggestions">
            {assistantSuggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                className="cx-ai__suggestion"
                onClick={() => void ask(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div className="cx-ai__loading" role="status" aria-live="polite">
          <span className="cx-spinner" aria-hidden />
          <div className="cx-ai__loading-copy">
            <span>
              Searching {health?.chunks ?? 58} chunks
              <small>Retrieval, then local generation</small>
            </span>
            <span className="cx-ai__loading-skeleton" aria-hidden>
              <i style={{ width: '95%' }} />
              <i style={{ width: '82%' }} />
              <i style={{ width: '61%' }} />
            </span>
          </div>
        </div>
      )}

      {error && (
        <div className="cx-ai__error" role="alert">
          <strong>Assistant unavailable</strong>
          <span>{error}</span>
          <button type="button" onClick={() => void ask()} className="cx-text-button">
            Try again
          </button>
        </div>
      )}

      {answer && (
        <div className="cx-ai__answer" aria-live="polite">
          <div className="cx-ai__answer-head">
            <span>Answer</span>
            <span>Answered in {formatLatency(answer.latency_ms)}</span>
            <button type="button" className="cx-ai__reset" onClick={reset} aria-label="Clear answer">
              <RotateCcw size={12} strokeWidth={1.8} />
            </button>
          </div>
          <p className="cx-ai__text">{renderAnswer(answer.answer, (index) => setOpenSource(`source-${index}`))}</p>

          {citedSources.length > 0 && (
            <div className="cx-ai__sources">
              <div className="cx-ai__sources-label">
                <span>Sources</span>
                <span>{answer.citations.length || citedSources.length} cited</span>
              </div>
              {citedSources.map((source) => {
                const key = `source-${source.citation}`
                const open = openSource === key
                return (
                  <div className="cx-source" key={key} data-open={open || undefined}>
                    <button
                      type="button"
                      className="cx-source__button"
                      onClick={() => setOpenSource(open ? null : key)}
                      aria-expanded={open}
                    >
                      <span className="cx-source__index">{source.citation}</span>
                      <span className="cx-source__name">
                        <strong>{source.source}</strong>
                        <span>{source.section.replace(/^.*? > /, '')}</span>
                      </span>
                      <ChevronDown size={13} strokeWidth={1.8} className="cx-source__chevron" aria-hidden />
                    </button>
                    {open && (
                      <div className="cx-source__text">
                        {source.text}
                        <span className="cx-source__score">score {source.score.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          <div className="cx-ai__actions">
            <button
              type="button"
              className="cx-secondary-button cx-secondary-button--small"
              onClick={() => onUseReply(stripCitations(answer.answer))}
              disabled={!answer.citations.length}
            >
              <Check size={13} strokeWidth={1.9} aria-hidden />
              Use as reply
            </button>
            <span className="cx-ai__model">
              {answer.model.replace(':3b', ' 3B')} · {answer.mode.startsWith('llm') ? 'grounded' : answer.mode}
            </span>
          </div>
          {answer.warnings.length > 0 && <p className="cx-ai__warning">{answer.warnings[0]}</p>}
        </div>
      )}

      <div className="cx-ai__composer">
        <textarea
          ref={inputRef}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              void ask()
            }
          }}
          placeholder="Ask about a policy or playbook…"
          rows={2}
          aria-label="Ask the knowledge assistant"
        />
        <button
          type="button"
          className="cx-ai__send"
          onClick={() => void ask()}
          disabled={!question.trim() || loading}
          aria-label="Ask assistant"
        >
          <ArrowUp size={15} strokeWidth={2} />
        </button>
      </div>
      <div className="cx-ai__hint">
        <CornerDownLeft size={11} strokeWidth={1.8} aria-hidden />
        Enter to ask · answers cite the source document
      </div>
    </section>
  )
}

export const AssistantPanel = memo(AssistantPanelBase)

function formatLatency(latencyMs: number): string {
  return latencyMs >= 1000
    ? `${(latencyMs / 1000).toFixed(1)} s`
    : `${Math.round(latencyMs)} ms`
}

function renderAnswer(text: string, onCitation: (index: string) => void) {
  const normalized = text.replace(/\*\*(.*?)\*\*/g, '$1')
  const parts = normalized.split(/(\[\d+(?:\s*,\s*\d+)*\])/g)
  return parts.map((part, index) => {
    const match = part.match(/^\[(\d+(?:\s*,\s*\d+)*)\]$/)
    if (!match) return <span key={index}>{part}</span>
    return (
      <button
        type="button"
        key={index}
        className="cx-citation"
        onClick={() => onCitation(match[1].split(',')[0].trim())}
      >
        {match[1]}
      </button>
    )
  })
}
