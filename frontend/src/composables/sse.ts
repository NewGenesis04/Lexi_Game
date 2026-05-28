const RECONNECT_DELAY_MS = 2000

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
    es.close()
    if (instance === es) {
      instance = null
    }
    setTimeout(() => {
      connectSSE(url, onMessage)
    }, RECONNECT_DELAY_MS)
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
