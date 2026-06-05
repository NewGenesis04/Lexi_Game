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

  es.onerror = () => {
    // The browser EventSource API handles reconnection automatically.
    // Do NOT close+recreate here — that would trigger a false disconnect
    // on the server, causing the game to pause mid-reconnect.
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
