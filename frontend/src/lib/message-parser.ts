
import { WarmupMessage, ScrapedImageMessage, ValidationMessage, TaskUpdateMessage } from '../types/messages'

// Type guards for runtime type checking
export function isWarmupMessage(message: any): message is WarmupMessage {
  return message && typeof message === 'object' && message.type === 'warmup' && typeof message.message === 'string'
}

export function isScrapedImageMessage(message: any): message is ScrapedImageMessage {
  return (
    message && 
    typeof message === 'object' && 
    message.type === 'scraped_image' && 
    typeof message.pin_id === 'string' && 
    typeof message.url === 'string' &&
    typeof message.image_title === 'string' &&
    typeof message.pin_url === 'string'
  )
}

export function isValidationMessage(message: any): message is ValidationMessage {
  return (
    message && 
    typeof message === 'object' && 
    message.type === 'validation' && 
    typeof message.pin_id === 'string' && 
    typeof message.score === 'number' && 
    message.score >= 0 && 
    message.score <= 100 && 
    typeof message.label === 'string' && 
    typeof message.valid === 'boolean'
  )
}

// Messages will not be parsed by the websocket service, so we use this to parse them
export function parseWebSocketStringToTaskUpdateMessage(rawMessage: string): TaskUpdateMessage | null {
  try {
    // Parse the raw string message from websocket
    const parsed = JSON.parse(rawMessage)

    // Check message type and validate structure
    if (isWarmupMessage(parsed)) {
      return parsed as WarmupMessage
    }
    
    if (isScrapedImageMessage(parsed)) {
      return parsed as ScrapedImageMessage  
    }
    
    if (isValidationMessage(parsed)) {
      return parsed as ValidationMessage
    }

    console.warn('Unknown message format:', rawMessage)
    return null
    
  } catch (error) {
    console.error('Failed to parse WebSocket message:', error, rawMessage)
    return null
  }
}

// Utility functions for working with parsed messages
export function getMessageType(message: TaskUpdateMessage): string {
  return message.type
}

export function isWarmupCompleteFromTaskUpdateMessages(messages: TaskUpdateMessage[]): boolean {
  //If we've received any scraped images, the warmup is complete
  return messages.some(msg => msg.type === 'scraped_image')
}

export function getScrapedImagesFromTaskUpdateMessages(messages: TaskUpdateMessage[]): ScrapedImageMessage[] {
  return messages.filter(isScrapedImageMessage)
}

export function getValidationResultsFromTaskUpdateMessages(messages: TaskUpdateMessage[]): ValidationMessage[] {
  return messages.filter(isValidationMessage)
}

export function getValidatedImagesFromTaskUpdateMessages(messages: TaskUpdateMessage[]): ValidationMessage[] {
  return messages.filter((msg): msg is ValidationMessage => isValidationMessage(msg) && msg.valid)
}

export function getRejectedImagesFromTaskUpdateMessages(messages: TaskUpdateMessage[]): ValidationMessage[] {
  return messages.filter((msg): msg is ValidationMessage => isValidationMessage(msg) && !msg.valid)
}   