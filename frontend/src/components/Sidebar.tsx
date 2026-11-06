import {
  BookOpen,
  ChevronDown,
  CircleDot,
  Inbox,
  MessageSquareText,
  Settings2,
  Users,
} from 'lucide-react'
import { Avatar } from '../kit'
import { csatBars, currentUser } from '../data'

export type WorkspaceView = 'inbox' | 'feedback' | 'customers'

interface SidebarProps {
  view: WorkspaceView
  onViewChange: (view: WorkspaceView) => void
  openCount: number
  detractorCount: number
  channelCounts: Record<string, number>
}

const NAV = [
  { id: 'inbox' as const, label: 'Inbox', icon: Inbox },
  { id: 'feedback' as const, label: 'Feedback', icon: MessageSquareText },
  { id: 'customers' as const, label: 'Customers', icon: Users },
]

export function Sidebar({ view, onViewChange, openCount, detractorCount, channelCounts }: SidebarProps) {
  return (
    <aside className="cx-sidebar">
      <div className="cx-brand">
        <span className="cx-brand__name">Northstar</span>
        <span className="cx-brand__product">Orbit CX</span>
      </div>

      <button className="cx-workspace" type="button">
        <span className="cx-workspace__dot" aria-hidden />
        <span>
          <span className="cx-workspace__label">Workspace</span>
          <span className="cx-workspace__name">Northstar Labs</span>
        </span>
        <ChevronDown size={14} strokeWidth={1.8} aria-hidden />
      </button>

      <nav className="cx-nav" aria-label="Workspace">
        {NAV.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              type="button"
              className="cx-nav__item"
              data-active={view === item.id || undefined}
              onClick={() => onViewChange(item.id)}
            >
              <Icon size={15} strokeWidth={1.8} aria-hidden />
              <span>{item.label}</span>
              {item.id === 'inbox' && <span className="cx-nav__count">{openCount}</span>}
              {item.id === 'feedback' && detractorCount > 0 && (
                <span className="cx-nav__count cx-nav__count--quiet">{detractorCount}</span>
              )}
            </button>
          )
        })}
        <button
          type="button"
          className="cx-nav__item"
          onClick={() => window.open('/docs', '_blank', 'noopener,noreferrer')}
        >
          <BookOpen size={15} strokeWidth={1.8} aria-hidden />
          <span>Knowledge</span>
          <span className="cx-nav__external">API</span>
        </button>
      </nav>

      <div className="cx-sidebar__section">
        <div className="cx-sidebar__eyebrow">Views</div>
        <button type="button" className="cx-view" onClick={() => onViewChange('inbox')}>
          <CircleDot size={12} strokeWidth={1.8} aria-hidden />
          <span>Open tickets</span>
          <span>{openCount}</span>
        </button>
        <button type="button" className="cx-view" onClick={() => onViewChange('feedback')}>
          <CircleDot size={12} strokeWidth={1.8} className="cx-view__danger" aria-hidden />
          <span>Detractors</span>
          <span>{detractorCount}</span>
        </button>
      </div>

      <div className="cx-sidebar__section">
        <div className="cx-sidebar__eyebrow">Channels</div>
        {Object.entries(channelCounts).map(([channel, count]) => (
          <div className="cx-channel" key={channel}>
            <span className="cx-channel__mark" aria-hidden />
            <span>{channel}</span>
            <span>{count}</span>
          </div>
        ))}
      </div>

      <div className="cx-pulse" aria-label="CSAT for the last seven days">
        <div className="cx-pulse__head">
          <span>CSAT pulse</span>
        </div>
        <div className="cx-pulse__body">
          <span className="cx-pulse__value">4.3</span>
          <span className="cx-pulse__unit">/ 5</span>
          <div className="cx-pulse__trend" aria-hidden>
            {csatBars.map((height, index) => (
              <span key={index} style={{ height: `${height}%` }} />
            ))}
          </div>
        </div>
        <div className="cx-pulse__foot">38 responses · 7 days</div>
      </div>

      <div className="cx-sidebar__footer">
        <Avatar name={currentUser.name} size={26} tone="accent" />
        <span className="cx-sidebar__user">
          <span>{currentUser.name}</span>
          <span>{currentUser.role}</span>
        </span>
        <button type="button" className="cx-icon-button cx-icon-button--dark" aria-label="Workspace settings">
          <Settings2 size={15} strokeWidth={1.8} />
        </button>
      </div>
    </aside>
  )
}
