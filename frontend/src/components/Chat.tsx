import { useState, useCallback } from 'react'
import type { ChatMessage, Session } from '../types'
import { sendMessage } from '../api/client'
import MessageList from './MessageList'
import ChatInput from './ChatInput'

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function createSession(): Session {
  return {
    id: generateId(),
    name: '新对话',
    messages: [],
    createdAt: Date.now(),
  }
}

export default function Chat() {
  const [sessions, setSessions] = useState<Session[]>([createSession()])
  const [activeSessionId, setActiveSessionId] = useState(sessions[0].id)
  const [loading, setLoading] = useState(false)
  const [connected, setConnected] = useState(true)

  const activeSession = sessions.find((s) => s.id === activeSessionId) || sessions[0]

  const updateSession = useCallback(
    (sessionId: string, updater: (s: Session) => Session) => {
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? updater(s) : s))
      )
    },
    []
  )

  const handleSend = useCallback(
    async (prompt: string) => {
      const sessionId = activeSessionId

      // 添加用户消息
      const userMsg: ChatMessage = {
        id: generateId(),
        role: 'user',
        content: prompt,
        timestamp: Date.now(),
      }

      updateSession(sessionId, (s) => ({
        ...s,
        messages: [...s.messages, userMsg],
        name: s.messages.length === 0 ? prompt.slice(0, 30) + (prompt.length > 30 ? '...' : '') : s.name,
      }))

      setLoading(true)

      try {
        const reply = await sendMessage(prompt, sessionId)

        const aiMsg: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: reply,
          timestamp: Date.now(),
        }

        updateSession(sessionId, (s) => ({
          ...s,
          messages: [...s.messages, aiMsg],
        }))

        setConnected(true)
      } catch (err) {
        setConnected(false)
        const errorMsg: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: `⚠️ 请求失败: ${err instanceof Error ? err.message : '未知错误'}`,
          timestamp: Date.now(),
        }
        updateSession(sessionId, (s) => ({
          ...s,
          messages: [...s.messages, errorMsg],
        }))
      } finally {
        setLoading(false)
      }
    },
    [activeSessionId, updateSession]
  )

  const handleNewSession = useCallback(() => {
    const newSession = createSession()
    setSessions((prev) => [...prev, newSession])
    setActiveSessionId(newSession.id)
  }, [])

  const handleDeleteSession = useCallback(
    (id: string) => {
      setSessions((prev) => {
        const filtered = prev.filter((s) => s.id !== id)
        if (filtered.length === 0) {
          const newSession = createSession()
          setActiveSessionId(newSession.id)
          return [newSession]
        }
        if (id === activeSessionId) {
          setActiveSessionId(filtered[0].id)
        }
        return filtered
      })
    },
    [activeSessionId]
  )

  return (
    <div className="chat-container">
      <MessageList messages={activeSession.messages} loading={loading} />
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  )
}
