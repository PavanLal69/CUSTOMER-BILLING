import { Inbox, MessageSquareText, SearchX } from 'lucide-react'
import { Avatar } from '../kit'
import type { Ticket } from '../data'

export type QueueFilter = 'open' | 'p1' | 'feedback' | 'all'

interface TicketQueueProps {
  tickets: Ticket[]
  selectedId: string
  filter: QueueFilter
  onFilter: (filter: QueueFilter) => void
  onSelect: (id: string) => void
  counts: { open: number; p1: number; feedback: number; all: number }
  detractorCount: number
  search: string
}

const FILTERS: { id: QueueFilter; label: string }[] = [
  { id: 'open', label: 'Open' },
  { id: 'p1', label: 'P1' },
  { id: 'feedback', label: 'Feedback' },
  { id: 'all', label: 'All' },
]

const PRIORITY_ORDER: Record<Ticket['priority'], number> = { P1: 0, P2: 1, P3: 2, P4: 3 }

export function TicketQueue({
  tickets,
  selectedId,
  filter,
  onFilter,
  onSelect,
  counts,
  detractorCount,
  search,
}: TicketQueueProps) {
  const sorted = [...tickets].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority],
  )

  return (
    <section className="cx-queue" aria-label="Ticket queue">
      <div className="cx-queue__head">
        <div className="cx-queue__title">
          <h1>Inbox</h1>
          <span className="cx-queue__count">{counts.open} open</span>
        </div>
        <p className="cx-queue__summary">
          <span className="cx-live-dot" aria-hidden /> {detractorCount} detractor follow-ups due today
        </p>
        <div className="cx-filterbar" role="tablist" aria-label="Filter tickets">
          {FILTERS.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={filter === item.id}
              className="cx-filter"
              data-active={filter === item.id || undefined}
              onClick={() => onFilter(item.id)}
            >
              {item.label}
              <span>{counts[item.id]}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="cx-queue__list">
        {sorted.length === 0 && (
          <div className="cx-empty">
            <SearchX size={22} strokeWidth={1.6} aria-hidden />
            <strong>No tickets match</strong>
            <span>{search ? `Nothing for “${search}”.` : 'Try another filter.'}</span>
          </div>
        )}
        {sorted.map((ticket) => (
          <TicketRow
            key={ticket.id}
            ticket={ticket}
            selected={ticket.id === selectedId}
            onClick={() => onSelect(ticket.id)}
          />
        ))}
      </div>

      <div className="cx-queue__foot">
        <span>
          <Inbox size={12} strokeWidth={1.8} aria-hidden /> Sorted by priority
        </span>
        <span>
          <MessageSquareText size={12} strokeWidth={1.8} aria-hidden /> 92% quality
        </span>
      </div>
    </section>
  )
}

function TicketRow({ ticket, selected, onClick }: { ticket: Ticket; selected: boolean; onClick: () => void }) {
  const detractor = ticket.csat <= 2
  return (
    <button
      type="button"
      className="cx-ticket"
      data-selected={selected || undefined}
      data-unread={ticket.status === 'New' || undefined}
      onClick={onClick}
      aria-current={selected ? 'true' : undefined}
    >
      <Avatar name={ticket.customer} size={30} tone="person" />
      <span className="cx-ticket__body">
        <span className="cx-ticket__top">
          <span className="cx-ticket__customer">{ticket.customer}</span>
          <span className="cx-ticket__time">{ticket.updated}</span>
        </span>
        <span className="cx-ticket__subject">{ticket.subject}</span>
        <span className="cx-ticket__meta">
          <span className="cx-priority" data-priority={ticket.priority}>
            <span className="cx-priority__dot" aria-hidden />
            {ticket.priority}
          </span>
          <span className="cx-ticket__channel">{ticket.channel}</span>
          <span className="cx-ticket__meta-sep" aria-hidden>·</span>
          <span className="cx-ticket__csat" data-risk={detractor || undefined}>
            CSAT {ticket.csat}
          </span>
        </span>
      </span>
    </button>
  )
}
