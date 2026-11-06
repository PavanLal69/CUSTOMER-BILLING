import { useCallback, useEffect, useRef, useState, type RefObject } from 'react'

interface VirtualRows {
  listRef: RefObject<HTMLDivElement>
  onScroll: () => void
  start: number
  end: number
  padTop: number
  padBottom: number
  virtualized: boolean
}

/**
 * A tiny fixed-row windowing hook. The queue is small today, so it renders
 * normally until the threshold is crossed; long queues then mount only the
 * visible rows plus an overscan buffer.
 */
export function useVirtualRows(count: number, rowHeight: number, enabled: boolean, overscan = 3): VirtualRows {
  const listRef = useRef<HTMLDivElement>(null)
  const [scrollTop, setScrollTop] = useState(0)
  const [viewport, setViewport] = useState(600)

  useEffect(() => {
    const element = listRef.current
    if (!element || typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(() => setViewport(element.clientHeight))
    observer.observe(element)
    setViewport(element.clientHeight)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    listRef.current?.scrollTo({ top: 0 })
    setScrollTop(0)
  }, [count])

  const onScroll = useCallback(() => {
    if (listRef.current) setScrollTop(listRef.current.scrollTop)
  }, [])

  if (!enabled) {
    return {
      listRef,
      onScroll,
      start: 0,
      end: count,
      padTop: 0,
      padBottom: 0,
      virtualized: false,
    }
  }

  const start = Math.min(count, Math.max(0, Math.floor(scrollTop / rowHeight) - overscan))
  const end = Math.max(start, Math.min(count, Math.ceil((scrollTop + viewport) / rowHeight) + overscan))

  return {
    listRef,
    onScroll,
    start,
    end,
    padTop: start * rowHeight,
    padBottom: Math.max(0, (count - end) * rowHeight),
    virtualized: true,
  }
}
