import { BookOpen, CircleHelp, Command, Plus, Search, X } from 'lucide-react'
import type { RefObject } from 'react'
import { Avatar } from '../kit'
import { currentUser } from '../data'
import type { RagHealth } from '../api'

interface TopbarProps {
  search: string
  onSearch: (value: string) => void
  searchRef: RefObject<HTMLInputElement>
  health: RagHealth | null
  onNewTicket: () => void
  onAsk: () => void
  viewLabel: string
}

export function Topbar({ search, onSearch, searchRef, health, onNewTicket, onAsk, viewLabel }: TopbarProps) {
  return (
    <header className="cx-topbar">
      <div className="cx-topbar__left">
        <div className="cx-breadcrumb">
          <span>Support</span>
          <span className="cx-breadcrumb__sep">/</span>
          <strong>{viewLabel}</strong>
        </div>
        <span className="cx-topbar__date">Wed, 4 Nov</span>
      </div>

      <label className="cx-search">
        <Search size={15} strokeWidth={1.8} aria-hidden />
        <input
          ref={searchRef}
          value={search}
          onChange={(event) => onSearch(event.target.value)}
          placeholder="Search tickets, customers, or feedback"
          aria-label="Search tickets, customers, or feedback"
        />
        {search ? (
          <button type="button" className="cx-search__clear" onClick={() => onSearch('')} aria-label="Clear search">
            <X size={13} strokeWidth={2} />
          </button>
        ) : (
          <kbd className="cx-kbd">
            <Command size={10} strokeWidth={2} aria-hidden />K
          </kbd>
        )}
      </label>

      <div className="cx-topbar__right">
        <span
          className="cx-model"
          data-ready={health?.ready ? 'true' : undefined}
          title={health ? `${health.llm_provider} · ${health.llm_model}` : 'Knowledge API offline'}
        >
          <span className="cx-model__dot" aria-hidden />
          {health ? health.llm_model.replace(':3b', ' 3B') : 'API offline'}
        </span>
        <button type="button" className="cx-ghost-button cx-ask-button" onClick={onAsk}>
          <BookOpen size={13} strokeWidth={1.8} aria-hidden />
          Ask Northstar
        </button>
        <button type="button" className="cx-icon-button" aria-label="Help">
          <CircleHelp size={16} strokeWidth={1.8} />
        </button>
        <button type="button" className="cx-primary-button" onClick={onNewTicket}>
          <Plus size={14} strokeWidth={2} aria-hidden />
          New ticket
        </button>
        <Avatar name={currentUser.name} size={28} tone="person" />
      </div>
    </header>
  )
}
