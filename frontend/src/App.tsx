import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { getHealth, type RagHealth } from './api'
import { currentUser, tickets as initialTickets, type Channel, type Priority, type Ticket } from './data'
import { StageshowRoot } from './kit'
import { Sidebar, type WorkspaceView } from './components/Sidebar'
import { Topbar } from './components/Topbar'
import { TicketQueue, type QueueFilter } from './components/TicketQueue'
import { TicketWorkspace } from './components/TicketWorkspace'
import { NewTicketDialog } from './components/NewTicketDialog'

const TARGET_BY_PRIORITY: Record<Priority, string> = {
  P1: '4h',
  P2: '1d',
  P3: '3d',
  P4: '10d',
}

const VIEW_LABEL: Record<WorkspaceView, string> = {
  inbox: 'Inbox',
  feedback: 'Feedback',
  customers: 'Customers',
}

const FILTER_LABEL: Record<QueueFilter, string> = {
  open: 'Open',
  p1: 'P1',
  feedback: 'Feedback',
  all: 'All',
}

export default function App() {
  const [ticketList, setTicketList] = useState<Ticket[]>(initialTickets)
  const [selectedId, setSelectedId] = useState('T-1042')
  const [filter, setFilter] = useState<QueueFilter>('open')
  const [view, setView] = useState<WorkspaceView>('inbox')
  const [search, setSearch] = useState('')
  const [health, setHealth] = useState<RagHealth | null>(null)
  const [toast, setToast] = useState<string | null>(null)
  const [newTicketOpen, setNewTicketOpen] = useState(false)
  const searchRef = useRef<HTMLInputElement>(null)
  const assistantRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    let alive = true
    const load = async () => {
      try {
        const next = await getHealth()
        if (alive) setHealth(next)
      } catch {
        if (alive) setHealth(null)
      }
    }
    void load()
    const timer = window.setInterval(load, 30_000)
    return () => {
      alive = false
      window.clearInterval(timer)
    }
  }, [])

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(null), 3200)
    return () => window.clearTimeout(timer)
  }, [toast])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      const typing =
        target?.tagName === 'INPUT' ||
        target?.tagName === 'TEXTAREA' ||
        target?.tagName === 'SELECT' ||
        target?.isContentEditable
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        searchRef.current?.focus()
      }
      if (!typing && event.key === '/') {
        event.preventDefault()
        searchRef.current?.focus()
      }
      if (event.key === 'Escape' && document.activeElement === searchRef.current) {
        setSearch('')
        searchRef.current?.blur()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const counts = useMemo(
    () => ({
      open: ticketList.filter((ticket) => ticket.status !== 'Resolved').length,
      p1: ticketList.filter((ticket) => ticket.priority === 'P1' && ticket.status !== 'Resolved').length,
      feedback: ticketList.filter((ticket) => ticket.csat <= 2).length,
      all: ticketList.length,
    }),
    [ticketList],
  )

  const detractorCount = useMemo(
    () => ticketList.filter((ticket) => ticket.status !== 'Resolved' && ticket.csat <= 2).length,
    [ticketList],
  )

  const channelCounts = useMemo(
    () =>
      ticketList.reduce<Record<string, number>>((counts, ticket) => {
        counts[ticket.channel] = (counts[ticket.channel] ?? 0) + 1
        return counts
      }, {}),
    [ticketList],
  )

  const filteredTickets = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return ticketList.filter((ticket) => {
      const matchesFilter =
        filter === 'all'
          ? true
          : filter === 'open'
            ? ticket.status !== 'Resolved'
            : filter === 'p1'
              ? ticket.priority === 'P1'
              : ticket.csat <= 2
      if (!matchesFilter) return false
      if (!needle) return true
      return [ticket.id, ticket.subject, ticket.customer, ticket.contact, ticket.feedback, ...ticket.tags]
        .join(' ')
        .toLowerCase()
        .includes(needle)
    })
  }, [ticketList, filter, search])

  const selected = ticketList.find((ticket) => ticket.id === selectedId) ?? filteredTickets[0] ?? ticketList[0]

  useEffect(() => {
    if (filteredTickets.length && !filteredTickets.some((ticket) => ticket.id === selectedId)) {
      setSelectedId(filteredTickets[0].id)
    }
  }, [filteredTickets, selectedId])

  const changeView = (next: WorkspaceView) => {
    setView(next)
    if (next === 'feedback') {
      const firstDetractor = ticketList.find((ticket) => ticket.csat <= 2)
      setFilter('feedback')
      if (firstDetractor) setSelectedId(firstDetractor.id)
    } else if (next === 'inbox') {
      setFilter('open')
    } else {
      setFilter('all')
    }
  }

  const changeFilter = (next: QueueFilter) => {
    setFilter(next)
    setView(next === 'feedback' ? 'feedback' : 'inbox')
  }

  const updateTicket = (id: string, update: (ticket: Ticket) => Ticket) => {
    setTicketList((current) => current.map((ticket) => (ticket.id === id ? update(ticket) : ticket)))
  }

  const resolveTicket = (id: string) => {
    updateTicket(id, (ticket) => ({ ...ticket, status: 'Resolved', updated: 'now' }))
    setToast(`${id} resolved. The post-resolution survey will send automatically.`)
  }

  const reopenTicket = (id: string) => {
    updateTicket(id, (ticket) => ({ ...ticket, status: 'In progress', updated: 'now' }))
    setToast(`${id} reopened and assigned to ${currentUser.name}.`)
  }

  const closeLoop = (id: string) => {
    updateTicket(id, (ticket) => ({ ...ticket, acknowledged: true }))
    setToast('Follow-up logged. The detractor loop is closed.')
  }

  const sendReply = (id: string, body: string) => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    updateTicket(id, (ticket) => ({
      ...ticket,
      status: ticket.status === 'Resolved' ? 'Resolved' : 'In progress',
      updated: 'now',
      messages: [
        ...ticket.messages,
        {
          id: `m-${Date.now()}`,
          role: 'agent',
          author: currentUser.name,
          time,
          body,
        },
      ],
    }))
    setToast('Reply sent to the customer.')
  }

  const createTicket = (values: { customer: string; subject: string; priority: Priority; channel: Channel }) => {
    const nextNumber = Math.max(...ticketList.map((ticket) => Number(ticket.id.replace('T-', '')) || 0)) + 1
    const id = `T-${nextNumber}`
    const ticket: Ticket = {
      id,
      subject: values.subject,
      customer: values.customer,
      contact: values.customer,
      email: 'contact@example.com',
      plan: 'Growth',
      seats: 1,
      channel: values.channel,
      priority: values.priority,
      status: 'New',
      assignee: currentUser.name,
      updated: 'now',
      age: 'now',
      firstResponse: '—',
      target: TARGET_BY_PRIORITY[values.priority],
      tags: ['New'],
      csat: 3,
      feedback: 'No survey response yet.',
      theme: 'Awaiting survey',
      sentiment: 'Passive',
      acknowledged: true,
      messages: [
        {
          id: 'm-created',
          role: 'customer',
          author: values.customer,
          time: 'now',
          body: values.subject,
        },
      ],
    }
    setTicketList((current) => [ticket, ...current])
    setSelectedId(id)
    setFilter('all')
    setView('inbox')
    setNewTicketOpen(false)
    setToast(`${id} created and added to the inbox.`)
  }

  const focusAssistant = useCallback(() => {
    assistantRef.current?.focus()
    assistantRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [])

  if (!selected) {
    return (
      <StageshowRoot>
        <div className="cx-empty-app">No tickets yet.</div>
      </StageshowRoot>
    )
  }

  return (
    <StageshowRoot>
      <Sidebar
        view={view}
        onViewChange={changeView}
        openCount={counts.open}
        detractorCount={detractorCount}
        channelCounts={channelCounts}
      />

      <div className="cx-shell">
        <Topbar
          search={search}
          onSearch={setSearch}
          searchRef={searchRef}
          health={health}
          onNewTicket={() => setNewTicketOpen(true)}
          onAsk={focusAssistant}
          viewLabel={VIEW_LABEL[view]}
        />

        <main className="cx-content">
          <TicketQueue
            tickets={filteredTickets}
            selectedId={selected.id}
            filter={filter}
            onFilter={changeFilter}
            onSelect={setSelectedId}
            counts={counts}
            detractorCount={detractorCount}
            search={search}
          />
          <TicketWorkspace
            ticket={selected}
            allTickets={ticketList}
            health={health}
            assistantRef={assistantRef}
            onResolve={resolveTicket}
            onReopen={reopenTicket}
            onCloseLoop={closeLoop}
            onReply={sendReply}
          />
        </main>
        <div className="cx-statusbar">
          <span>{filteredTickets.length} of {ticketList.length} tickets · {FILTER_LABEL[filter]}</span>
          <span>
            <span className="cx-statusbar__dot" aria-hidden /> Local knowledge base · {health?.chunks ?? 58} chunks
          </span>
        </div>
      </div>

      <NewTicketDialog open={newTicketOpen} onClose={() => setNewTicketOpen(false)} onCreate={createTicket} />
      {toast && <div className="cx-toast" role="status">{toast}</div>}
    </StageshowRoot>
  )
}
