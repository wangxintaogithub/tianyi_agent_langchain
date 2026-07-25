import type { ChatRequest, ChatResponse, ConversationResponse } from '../types'

const API_BASE = '/api'

export async function sendMessage(prompt: string, sessionId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/conversation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt,
      session_id: sessionId,
    } as ChatRequest & { session_id: string }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || '请求失败')
  }

  const data: ConversationResponse = await res.json()
  return data.reply
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`)
    return res.ok
  } catch {
    return false
  }
}
