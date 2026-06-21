let instance: EventSource | null = null

export type SSECallback = (data: unknown) => void

export interface SSEConnection {
  close: () => void
}

export function connectSSE(url: string, onMessage: SSECallback): SSEConnection {
  if (instance) {
    instance.close()
    instance = null
  }

  const es = new EventSource(url)
  instance = es

  es.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data)
      onMessage(parsed)
    } catch {
      console.warn('[sse] failed to parse event data', event.data)
    }
  }

  es.onerror = (event) => {
    console.warn('[sse] connection error — reconnecting', (event as MessageEvent)?.data ?? '')
  }

  return {
    close: () => {
      if (instance === es) {
        instance = null
      }
      es.close()
    },
  }
}
