
// While for this project, the websocket is really only has to handle UpdateMessages, 
// this Websocket Service uses generic string types for messages that are sent over the websocket
// Code that would like to use the websocket must implement the onmessage callback and handle type validation separately
// For example, the use-search hook handles type validation for its messages using utils in message-parser.ts
// The intention here is to decouple specific message types from the websocket service itself

export interface WebSocketCallbacks {
  onMessage?: (message: string) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private callbacks: WebSocketCallbacks = {}

  constructor(private baseUrl: string = 'ws://localhost:8000') {}

  connect(promptId: string, callbacks: WebSocketCallbacks = {}) {
    this.callbacks = callbacks
    const wsUrl = `${this.baseUrl}/ws/${promptId}`
    
    try {
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.callbacks.onOpen?.()
      }

      this.ws.onmessage = (event) => {
        // Simply pass the raw message string to the callback
        // Let the consuming code handle parsing
        this.callbacks.onMessage?.(event.data)
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.callbacks.onClose?.()
        this.attemptReconnect(promptId)
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.callbacks.onError?.(error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.callbacks.onError?.(error as Event)
    }
  }

  private attemptReconnect(promptId: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      setTimeout(() => {
        this.connect(promptId, this.callbacks)
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
} 