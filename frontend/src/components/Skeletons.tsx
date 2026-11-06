import { Avatar } from '../kit'

export function QueueSkeleton() {
  return (
    <div className="cx-skeleton-list" aria-hidden>
      {Array.from({ length: 6 }).map((_, index) => (
        <div className="cx-ticket-skeleton" key={index}>
          <span className="cx-sk cx-sk--avatar" />
          <span className="cx-ticket-skeleton__body">
            <span className="cx-sk cx-sk--line" style={{ width: `${44 + (index % 3) * 9}%` }} />
            <span className="cx-sk cx-sk--line" style={{ width: `${72 - (index % 2) * 11}%` }} />
            <span className="cx-sk cx-sk--line cx-sk--short" style={{ width: `${34 + (index % 4) * 5}%` }} />
          </span>
        </div>
      ))}
    </div>
  )
}

export function WorkspaceSkeleton() {
  return (
    <section className="cx-ticket-workspace cx-workspace-skeleton" aria-label="Loading ticket">
      <div className="cx-workspace-skeleton__head">
        <span className="cx-sk cx-sk--eyebrow" />
        <span className="cx-sk cx-sk--title" />
        <div className="cx-workspace-skeleton__meta">
          <span className="cx-sk cx-sk--pill" />
          <span className="cx-sk cx-sk--pill" />
          <span className="cx-sk cx-sk--pill" />
        </div>
      </div>
      <div className="cx-tabs">
        <span className="cx-workspace-skeleton__tab" />
        <span className="cx-workspace-skeleton__tab" />
        <span className="cx-workspace-skeleton__tab" />
      </div>
      <div className="cx-detail-body">
        <div className="cx-detail-main">
          <div className="cx-workspace-skeleton__thread">
            {[0, 1, 2].map((index) => (
              <div className="cx-message-skeleton" key={index}>
                <Avatar plain size={28} />
                <div>
                  <span className="cx-sk cx-sk--line cx-sk--short" style={{ width: '22%' }} />
                  <span className="cx-sk cx-sk--line" style={{ width: '92%' }} />
                  <span className="cx-sk cx-sk--line" style={{ width: '74%' }} />
                  {index === 1 && <span className="cx-sk cx-sk--line" style={{ width: '55%' }} />}
                </div>
              </div>
            ))}
          </div>
          <div className="cx-composer">
            <span className="cx-sk cx-sk--line cx-sk--short" style={{ width: '18%' }} />
            <span className="cx-sk cx-sk--composer" />
          </div>
        </div>
        <aside className="cx-rail">
          <AssistantSkeleton />
          <div className="cx-rail-card">
            <span className="cx-sk cx-sk--line cx-sk--short" style={{ width: '24%' }} />
            <span className="cx-sk cx-sk--line" style={{ width: '80%', marginTop: 10 }} />
            <span className="cx-sk cx-sk--line" style={{ width: '62%' }} />
          </div>
        </aside>
      </div>
    </section>
  )
}

export function AssistantSkeleton() {
  return (
    <div className="cx-rail-card cx-ai-skeleton" aria-label="Loading knowledge assistant">
      <div className="cx-ai-skeleton__head">
        <span className="cx-sk cx-sk--avatar cx-sk--small" />
        <span className="cx-sk cx-sk--line cx-sk--short" style={{ width: '38%' }} />
      </div>
      <span className="cx-sk cx-sk--line" style={{ width: '90%', marginTop: 10 }} />
      <span className="cx-sk cx-sk--line" style={{ width: '72%' }} />
      <span className="cx-sk cx-sk--composer" style={{ marginTop: 10 }} />
    </div>
  )
}
