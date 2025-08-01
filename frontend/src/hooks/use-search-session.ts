/**
 * Custom hook for managing search session state and WebSocket communication.
 * 
 * This hook manages the entire search lifecycle:
 * - Starting/stopping search sessions
 * - WebSocket connection management
 * - Real-time message handling and state updates
 * - Error handling and cleanup
 * 
 * The WebSocket connection is tied to the search session lifecycle,
 * so they're managed together to avoid prop drilling and complex state management.
 */

import { useState, useCallback, useRef } from 'react'
import { createPrompt, PromptRequest} from '@/lib/api'
import { WebSocketService } from '@/lib/websocket'
import { parseWebSocketStringToTaskUpdateMessage } from '../lib/message-parser'
import { ScrapedImageMessage, TaskUpdateMessage, ValidationMessage, WarmupMessage } from '../types/messages'

export interface SearchSessionState {
  isSearching: boolean
  promptId: string | null
  allTaskUpdateMessages: TaskUpdateMessage[]
  warmupMessages: WarmupMessage[]
  scrapedImagesMessages: ScrapedImageMessage[]
  validationMessages: ValidationMessage[]
  error: string | null
  isConnected: boolean
}

export function useSearchSession() {
  // Main session state
  const [state, setState] = useState<SearchSessionState>({
    isSearching: false,
    promptId: null,
    allTaskUpdateMessages: [],
    warmupMessages: [],
    scrapedImagesMessages: [],
    validationMessages: [],
    error: null,
    isConnected: false,
  })

  // WebSocket service reference for cleanup
  const wsServiceRef = useRef<WebSocketService | null>(null)

  /**
   * Initiates a new search session with backend communication
   */
  const startSearchSession = useCallback(async (query: string) => {
    try {
      setState(prev => ({
        ...prev,
        isSearching: true,
        error: null,
        allTaskUpdateMessages: [],
        warmupMessages: [],
        scrapedImagesMessages: [],
        validationMessages: [],
      }))

      // Create prompt via API
      // Gets the prompt id for websocket connection
      const response = await createPrompt({ text: query })
      
      setState(prev => ({
        ...prev,
        promptId: response.id,
      }))

      const wsService = new WebSocketService()
      wsServiceRef.current = wsService

      // Connect to WebSocket
      // Handle all websocket callbacks here
      wsService.connect(response.id, {
        onOpen: () => {
          setState(prev => ({
            ...prev,
            isConnected: true,
          }))
        },
        // Websocket service will pass raw string messages to this callback
        // Therefore we need to parse the message with type safety
        onMessage: (message: string) => {
          const parsedMessage = parseWebSocketStringToTaskUpdateMessage(message)

          //All messages are added to the allTaskUpdateMessages array
          if (parsedMessage) {
            setState(prev => ({
              ...prev,
              allTaskUpdateMessages: [...prev.allTaskUpdateMessages, parsedMessage],
            }))

            //conditionally add to the appropriate message arrays
            //simplifies consuming specific message types in the frontend
            if (parsedMessage.type === 'warmup') {
              setState(prev => ({
                ...prev,
                warmupMessages: [...prev.warmupMessages, parsedMessage],
              }))
            } else if (parsedMessage.type === 'scraped_image') {
              setState(prev => ({
                ...prev,
                scrapedImagesMessages: [...prev.scrapedImagesMessages, parsedMessage],
              }))
            } else if (parsedMessage.type === 'validation') { 
              setState(prev => ({
                ...prev,
                validationMessages: [...prev.validationMessages, parsedMessage],
              }))
            }
          }
        },
        onClose: () => {
          setState(prev => ({
            ...prev,
            isConnected: false,
          }))
        },
        onError: (error) => {
          console.error('WebSocket error:', error)
          setState(prev => ({
            ...prev,
            error: 'Connection error',
            isConnected: false,
          }))
        },
      })

    } catch (error) {
      console.error('Search error:', error)
      setState(prev => ({
        ...prev,
        isSearching: false,
        error: error instanceof Error ? error.message : 'Failed to start search',
      }))
    }
  }, [])

  const stopSearchSession = useCallback(() => {
    if (wsServiceRef.current) {
      wsServiceRef.current.disconnect()
      wsServiceRef.current = null
    }

    setState({
      isSearching: false,
      promptId: null,
      allTaskUpdateMessages: [],
      warmupMessages: [],
      scrapedImagesMessages: [],
      validationMessages: [],
      error: null,
      isConnected: false,
    })
  }, [])

  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null,
    }))
  }, [])

  return {
    ...state,
    startSearchSession,
    stopSearchSession,
    clearError,
  }
} 