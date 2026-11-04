import { X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import type { Channel, Priority } from '../data'

interface NewTicketDialogProps {
  open: boolean
  onClose: () => void
  onCreate: (values: { customer: string; subject: string; priority: Priority; channel: Channel }) => void
}

export function NewTicketDialog({ open, onClose, onCreate }: NewTicketDialogProps) {
  const customerRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!open) return
    const timer = window.setTimeout(() => customerRef.current?.focus(), 40)
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => {
      window.clearTimeout(timer)
      window.removeEventListener('keydown', onKey)
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="cx-modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div className="cx-modal" role="dialog" aria-modal="true" aria-labelledby="new-ticket-title">
        <div className="cx-modal__head">
          <div>
            <span className="cx-eyebrow">Support inbox</span>
            <h2 id="new-ticket-title">New ticket</h2>
          </div>
          <button type="button" className="cx-icon-button" onClick={onClose} aria-label="Close">
            <X size={17} strokeWidth={1.8} />
          </button>
        </div>

        <form
          onSubmit={(event) => {
            event.preventDefault()
            const form = new FormData(event.currentTarget)
            onCreate({
              customer: String(form.get('customer') ?? '').trim(),
              subject: String(form.get('subject') ?? '').trim(),
              priority: form.get('priority') as Priority,
              channel: form.get('channel') as Channel,
            })
          }}
        >
          <label className="cx-field">
            <span>Customer</span>
            <input ref={customerRef} name="customer" placeholder="e.g. Lumen Studio" required maxLength={80} />
          </label>
          <label className="cx-field">
            <span>Subject</span>
            <input name="subject" placeholder="What is the customer asking about?" required maxLength={140} />
          </label>
          <div className="cx-field-row">
            <label className="cx-field">
              <span>Priority</span>
              <select name="priority" defaultValue="P3">
                <option value="P1">P1 · Critical</option>
                <option value="P2">P2 · High</option>
                <option value="P3">P3 · Normal</option>
                <option value="P4">P4 · Low</option>
              </select>
            </label>
            <label className="cx-field">
              <span>Channel</span>
              <select name="channel" defaultValue="Email">
                <option>Email</option>
                <option>Chat</option>
                <option>Portal</option>
                <option>API</option>
              </select>
            </label>
          </div>
          <p className="cx-modal__note">
            New tickets start unassigned to a responder and join the queue with no SLA clock until triage.
          </p>
          <div className="cx-modal__actions">
            <button type="button" className="cx-secondary-button" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="cx-primary-button">
              Create ticket
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
