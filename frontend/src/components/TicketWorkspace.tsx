import {
  ArrowLeft,
  BookOpen,
  Check,
  ChevronRight,
  Clock3,
  CornerDownRight,
  LockKeyhole,
  MessageSquareText,
  MoreHorizontal,
  Paperclip,
  Send,
  ShieldCheck,
  Star,
  Tag,
} from 'lucide-react'
import { useEffect, useRef, useState, type RefObject } from 'react'
import { Avatar, Badge } from '../kit'
import { AssistantPanel } from './AssistantPanel'
import type { Ticket } from '../data'
import type { RagHealth } from '../api'

type DetailTab = 'conversation' | 'feedback' | 'customer'

interface WorkspaceProps {
  ticket: Ticket
  allTickets: Ticket[]
  health: RagHealth | null
  assistantRef: RefObject<HTMLTextAreaElement>
  onResolve: (id: string) => void
  onReopen: (id: string) => void
  onCloseLoop: (id: string) => void
  onReply: (id: string, body: string) => void
}

const PRIORITY_LABEL: Record<Ticket['priority'], string> = {
  P1: 'Critical',
  P2: 'High',
  P3: 'Normal',
  P4: 'Low',
}

const RESPONSE_TARGET: Record<Ticket['priority'], string> = {
  P1: '15m',
  P2: '1h',
  P3: '8h',
  P4: '2d',
}

function minutes(value: string): number {
  const match = value.match(/^(\d+)([mhd])$/)
  if (!match) return 0
  const amount = Number(match[1])
  return match[2] === 'm' ? amount : match[2] === 'h' ? amount * 60 : amount * 1440
}

function firstResponseProgress(ticket: Ticket): number {
  if (ticket.firstResponse === '—') return 0
  const target = minutes(RESPONSE_TARGET[ticket.priority])
  if (!target) return 0
  return Math.min(100, Math.round((minutes(ticket.firstResponse) / target) * 100))
}

export function TicketWorkspace({
  ticket,
  allTickets,
  health,
  assistantRef,
  onResolve,
  onReopen,
  onCloseLoop,
  onReply,
}: WorkspaceProps) {
  const [tab, setTab] = useState<DetailTab>('conversation')
  const [reply, setReply] = useState('')
  const replyRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    setTab('conversation')
    setReply('')
  }, [ticket.id])

  const useAssistantReply = (text: string) => {
    setReply(text)
    setTab('conversation')
    requestAnimationFrame(() => replyRef.current?.focus())
  }

  const sendReply = () => {
    const body = reply.trim()
    if (!body) return
    onReply(ticket.id, body)
    setReply('')
  }

  return (
    <section className="cx-ticket-workspace" aria-label={`Ticket ${ticket.id}`}>
      <header className="cx-detail-head">
        <div className="cx-detail-head__top">
          <div className="cx-detail-head__id">
            <span>{ticket.id}</span>
            <ChevronRight size={12} strokeWidth={1.8} aria-hidden />
            <span>{ticket.customer}</span>
          </div>
          <div className="cx-detail-head__actions">
            <button type="button" className="cx-icon-button" aria-label="More ticket actions">
              <MoreHorizontal size={17} strokeWidth={1.8} />
            </button>
            <button
              type="button"
              className={ticket.status === 'Resolved' ? 'cx-secondary-button' : 'cx-primary-button'}
              onClick={() => (ticket.status === 'Resolved' ? onReopen(ticket.id) : onResolve(ticket.id))}
            >
              {ticket.status === 'Resolved' ? (
                <ArrowLeft size={14} strokeWidth={1.9} aria-hidden />
              ) : (
                <Check size={14} strokeWidth={2} aria-hidden />
              )}
              {ticket.status === 'Resolved' ? 'Reopen' : 'Resolve'}
            </button>
          </div>
        </div>

        <div className="cx-detail-head__title">
          <h2>{ticket.subject}</h2>
          <div className="cx-detail-head__badges">
            <Badge tone={ticket.status === 'Resolved' ? 'success' : ticket.status === 'New' ? 'warning' : 'accent'} dot>
              {ticket.status}
            </Badge>
            <span className="cx-priority cx-priority--large" data-priority={ticket.priority}>
              <span className="cx-priority__dot" aria-hidden />
              {ticket.priority} {PRIORITY_LABEL[ticket.priority]}
            </span>
          </div>
        </div>

        <div className="cx-detail-meta">
          <span className="cx-detail-meta__item">
            <Avatar name={ticket.assignee} size={20} tone="person" />
            {ticket.assignee}
          </span>
          <span className="cx-detail-meta__sep" aria-hidden />
          <span className="cx-detail-meta__item">
            <MessageSquareText size={13} strokeWidth={1.8} aria-hidden />
            {ticket.channel}
          </span>
          <span className="cx-detail-meta__sep" aria-hidden />
          <span className="cx-detail-meta__item">
            <Clock3 size={13} strokeWidth={1.8} aria-hidden />
            {ticket.age} old
          </span>
          <span className="cx-detail-meta__sep" aria-hidden />
          <span className="cx-detail-meta__item" data-warn="true">
            <span className="cx-sla-dot" aria-hidden /> First response {ticket.firstResponse} · resolve {ticket.target}
          </span>
        </div>
      </header>

      <div className="cx-tabs" role="tablist" aria-label="Ticket detail">
        {[
          { id: 'conversation' as const, label: 'Conversation', count: ticket.messages.length },
          { id: 'feedback' as const, label: 'Feedback', count: 1 },
          { id: 'customer' as const, label: 'Customer', count: null },
        ].map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={tab === item.id}
            className="cx-tab"
            data-active={tab === item.id || undefined}
            onClick={() => setTab(item.id)}
          >
            {item.label}
            {item.count !== null && <span>{item.count}</span>}
          </button>
        ))}
      </div>

      <div className="cx-detail-body">
        <div className="cx-detail-main">
          {tab === 'conversation' && (
            <>
              <div className="cx-thread">
                <div className="cx-thread__date">
                  <span>Today</span>
                </div>
                {ticket.messages.map((message) => (
                  <article className="cx-message" data-role={message.role} key={message.id}>
                    <Avatar
                      name={message.author}
                      size={28}
                      tone={message.role === 'note' ? 'ink' : 'person'}
                    />
                    <div className="cx-message__body">
                      <div className="cx-message__head">
                        <strong>{message.author}</strong>
                        <span>{message.role === 'customer' ? ticket.customer : 'Northstar support'}</span>
                        <span className="cx-message__time">{message.time}</span>
                      </div>
                      {message.role === 'note' && (
                        <div className="cx-message__note-label">
                          <LockKeyhole size={11} strokeWidth={1.9} aria-hidden />
                          Internal note · visible to the team only
                        </div>
                      )}
                      <p>{message.body}</p>
                    </div>
                  </article>
                ))}
                <div className="cx-next-update">
                  <Clock3 size={14} strokeWidth={1.8} aria-hidden />
                  <div>
                    <strong>Next update due in 36 minutes</strong>
                    <span>Priya was promised an ETA by 10:00 IST.</span>
                  </div>
                  <button
                    type="button"
                    className="cx-text-button"
                    onClick={() => assistantRef.current?.focus()}
                  >
                    Ask for a draft
                  </button>
                </div>
              </div>

              <div className="cx-composer">
                <div className="cx-composer__head">
                  <span>
                    Reply to <strong>{ticket.contact}</strong>
                  </span>
                  <span className="cx-composer__channel">{ticket.channel}</span>
                </div>
                <textarea
                  ref={replyRef}
                  value={reply}
                  onChange={(event) => setReply(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
                      event.preventDefault()
                      sendReply()
                    }
                  }}
                  placeholder="Write a customer-safe reply, or use a cited answer from Northstar AI."
                  rows={3}
                  aria-label="Reply to customer"
                />
                <div className="cx-composer__foot">
                  <div className="cx-composer__tools">
                    <button type="button" className="cx-icon-button" aria-label="Attach a file">
                      <Paperclip size={15} strokeWidth={1.8} />
                    </button>
                    <button type="button" className="cx-text-button">
                      Insert macro
                    </button>
                    <button
                      type="button"
                      className="cx-text-button"
                      onClick={() => assistantRef.current?.focus()}
                    >
                      <BookOpen size={13} strokeWidth={1.8} aria-hidden />
                      Ask Northstar
                    </button>
                  </div>
                  <div className="cx-composer__send">
                    <span className="cx-composer__hint">⌘↵ to send</span>
                    <button
                      type="button"
                      className="cx-primary-button"
                      onClick={sendReply}
                      disabled={!reply.trim()}
                    >
                      <Send size={13} strokeWidth={1.9} aria-hidden />
                      Send reply
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}

          {tab === 'feedback' && (
            <FeedbackView ticket={ticket} onCloseLoop={() => onCloseLoop(ticket.id)} />
          )}

          {tab === 'customer' && <CustomerView ticket={ticket} allTickets={allTickets} />}
        </div>

        <aside className="cx-rail" aria-label="Ticket context">
          <AssistantPanel health={health} inputRef={assistantRef} onUseReply={useAssistantReply} />

          <section className="cx-rail-card cx-sla-card">
            <div className="cx-rail-card__head">
              <span>Service level</span>
              <Badge tone={ticket.priority === 'P1' ? 'danger' : 'neutral'} dot>
                {ticket.priority}
              </Badge>
            </div>
            <div className="cx-sla-row">
              <span>First response</span>
              <strong>{ticket.firstResponse} / {RESPONSE_TARGET[ticket.priority]}</strong>
            </div>
            <div className="cx-progress" aria-hidden>
              <span style={{ width: `${firstResponseProgress(ticket)}%` }} />
            </div>
            <div className="cx-sla-row">
              <span>Resolution target</span>
              <strong>{ticket.target}</strong>
            </div>
            <div className="cx-sla-row">
              <span>Owner</span>
              <span className="cx-sla-owner">
                <Avatar name={ticket.assignee} size={18} tone="person" />
                {ticket.assignee}
              </span>
            </div>
            <div className="cx-sla-tags">
              {ticket.tags.map((tag) => (
                <span className="cx-tag" key={tag}>
                  {tag}
                </span>
              ))}
            </div>
          </section>

          <section className="cx-rail-card cx-related">
            <div className="cx-rail-card__head">
              <span>Related knowledge</span>
              <BookOpen size={13} strokeWidth={1.8} aria-hidden />
            </div>
            <button type="button" className="cx-related__item" onClick={() => assistantRef.current?.focus()}>
              <span>P1 ticket priority matrix</span>
              <ChevronRight size={13} strokeWidth={1.8} aria-hidden />
            </button>
            <button type="button" className="cx-related__item" onClick={() => assistantRef.current?.focus()}>
              <span>Refunds and service credits</span>
              <ChevronRight size={13} strokeWidth={1.8} aria-hidden />
            </button>
            <button type="button" className="cx-related__item" onClick={() => assistantRef.current?.focus()}>
              <span>Customer feedback closed-loop</span>
              <ChevronRight size={13} strokeWidth={1.8} aria-hidden />
            </button>
          </section>
        </aside>
      </div>
    </section>
  )
}

function FeedbackView({ ticket, onCloseLoop }: { ticket: Ticket; onCloseLoop: () => void }) {
  const closed = ticket.acknowledged
  const detractor = ticket.csat <= 2
  const steps = [
    { label: 'Survey response received', detail: 'Post-resolution CSAT', done: true },
    { label: 'Owner contacts the customer', detail: 'Within one business day', done: closed },
    { label: 'Root cause documented', detail: 'Theme and journey stage', done: closed },
    { label: 'Product review', detail: 'First Tuesday of the month', done: closed },
  ]

  return (
    <div className="cx-feedback-view">
      <div className="cx-feedback-view__head">
        <div>
          <span className="cx-eyebrow">{ticket.status === 'Resolved' ? 'Post-resolution survey' : 'Last survey response'}</span>
          <h3>{detractor ? 'A detractor needs a follow-up' : 'A promoter shared feedback'}</h3>
          <p>One response from {ticket.customer}. The score still counts in aggregate reporting.</p>
        </div>
        <div className="cx-csat-big" data-risk={detractor || undefined}>
          <span>{ticket.csat}</span>
          <small>/ 5</small>
          <span className="cx-csat-big__label">{ticket.sentiment}</span>
        </div>
      </div>

      <div className="cx-feedback-quote">
        <MessageSquareText size={17} strokeWidth={1.7} aria-hidden />
        <blockquote>{ticket.feedback}</blockquote>
        <div className="cx-feedback-quote__meta">
          <span>{ticket.contact}</span>
          <span>·</span>
          <span>{ticket.theme}</span>
        </div>
      </div>

      <div className="cx-feedback-grid">
        <section className="cx-panel">
          <div className="cx-panel__head">
            <span>Closed-loop checklist</span>
            <span className={closed ? 'cx-state cx-state--done' : 'cx-state'}>{closed ? 'Complete' : '1 of 4'}</span>
          </div>
          <ol className="cx-steps">
            {steps.map((step) => (
              <li key={step.label} data-done={step.done || undefined}>
                <span className="cx-step__mark">
                  {step.done ? <Check size={12} strokeWidth={2.2} /> : <span />}
                </span>
                <span>
                  <strong>{step.label}</strong>
                  <small>{step.detail}</small>
                </span>
              </li>
            ))}
          </ol>
          <button
            type="button"
            className={closed ? 'cx-secondary-button' : 'cx-primary-button'}
            onClick={onCloseLoop}
            disabled={closed}
          >
            {closed ? (
              <>
                <Check size={13} strokeWidth={2} aria-hidden /> Loop closed
              </>
            ) : (
              'Log follow-up and close the loop'
            )}
          </button>
        </section>

        <section className="cx-panel">
          <div className="cx-panel__head">
            <span>Signal</span>
            <Tag size={13} strokeWidth={1.8} aria-hidden />
          </div>
          <dl className="cx-signal">
            <div><dt>Theme</dt><dd>{ticket.theme}</dd></div>
            <div><dt>Journey stage</dt><dd>Resolve</dd></div>
            <div><dt>Product area</dt><dd>{ticket.tags[0]}</dd></div>
            <div><dt>Follow-up due</dt><dd>{closed ? 'Logged' : 'Within 1 business day'}</dd></div>
          </dl>
          <p className="cx-panel__note">
            <ShieldCheck size={13} strokeWidth={1.8} aria-hidden />
            Detractor follow-ups are due within one business day. Never edit or delete a survey response.
          </p>
        </section>
      </div>
    </div>
  )
}

function CustomerView({ ticket, allTickets }: { ticket: Ticket; allTickets: Ticket[] }) {
  const related = allTickets.filter((item) => item.customer === ticket.customer && item.id !== ticket.id)
  const atRisk = ticket.csat <= 2
  return (
    <div className="cx-customer-view">
      <div className="cx-customer-hero">
        <Avatar name={ticket.customer} size={48} tone="person" />
        <div>
          <span className="cx-eyebrow">Customer</span>
          <h3>{ticket.customer}</h3>
          <p>{ticket.plan} · {ticket.seats} seats · {ticket.channel} support</p>
        </div>
        <Badge tone={atRisk ? 'danger' : 'success'} dot>{atRisk ? 'At risk' : 'Healthy'}</Badge>
      </div>

      <div className="cx-customer-grid">
        <section className="cx-panel">
          <div className="cx-panel__head"><span>Account</span><span>Northstar CRM</span></div>
          <dl className="cx-signal">
            <div><dt>Plan</dt><dd>{ticket.plan}</dd></div>
            <div><dt>Seats</dt><dd>{ticket.seats}</dd></div>
            <div><dt>Renewal</dt><dd>12 Jan 2027</dd></div>
            <div><dt>Owner</dt><dd>Maya Chen</dd></div>
          </dl>
        </section>
        <section className="cx-panel">
          <div className="cx-panel__head"><span>Primary contact</span><span>Verified</span></div>
          <div className="cx-contact">
            <Avatar name={ticket.contact} size={30} tone="person" />
            <div><strong>{ticket.contact}</strong><span>{ticket.email}</span></div>
          </div>
          <p className="cx-panel__note">
            <Star size={13} strokeWidth={1.8} aria-hidden />
            Last CSAT: {ticket.csat}/5 · {ticket.sentiment}
          </p>
        </section>
      </div>

      <section className="cx-panel">
        <div className="cx-panel__head"><span>Recent tickets</span><span>{related.length} found</span></div>
        <div className="cx-related-tickets">
          {related.length === 0 && <p className="cx-panel__note">No other tickets for this account.</p>}
          {related.map((item) => (
            <div className="cx-related-ticket" key={item.id}>
              <span className="cx-related-ticket__id">{item.id}</span>
              <span>{item.subject}</span>
              <span className="cx-related-ticket__time">{item.updated}</span>
            </div>
          ))}
        </div>
      </section>

      <div className="cx-customer-footer">
        <CornerDownRight size={13} strokeWidth={1.8} aria-hidden />
        Account changes require identity verification. Never ask for a password or one-time code.
      </div>
    </div>
  )
}
