const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface PromptRequest {
  text: string
}

export interface PromptResponse {
  id: string
}

export async function createPrompt(prompt: PromptRequest): Promise<PromptResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/prompts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(prompt),
    })

    if (!response.ok) {
      throw new APIError(`HTTP error! status: ${response.status}`, response.status)
    }

    const data = await response.json()
    return data
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    throw new APIError(`Failed to create prompt: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
} 

export class APIError extends Error {
  constructor(message: string, public status?: number) {
    super(message)
    this.name = 'APIError'
  }
}