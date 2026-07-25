export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

export interface ChatRequest {
  prompt: string
  system_prompt?: string
  temperature?: number
  max_tokens?: number
}

export interface ChatResponse {
  reply: string
  model: string
}

export interface ConversationRequest {
  prompt: string
  session_id?: string
  temperature?: number
  max_tokens?: number
}

export interface ConversationResponse {
  reply: string
  model: string
  session_id: string
}

export interface Session {
  id: string
  name: string
  messages: ChatMessage[]
  createdAt: number
}
