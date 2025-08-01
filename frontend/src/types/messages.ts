// Type definitions for update messages from the backend

export interface WarmupMessage {
  type: 'warmup'
  message: string
}

export interface ScrapedImageMessage {
  type: 'scraped_image'
  pin_id: string
  image_title: string
  url: string
  pin_url: string
}

export interface ValidationMessage {
  type: 'validation'
  pin_id: string
  score: number
  label: string
  valid: boolean
}

// Union type for all possible message types
export type TaskUpdateMessage = WarmupMessage | ScrapedImageMessage | ValidationMessage 