import { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import type { ChatMessage } from '../types'

interface MessageListProps {
  messages: ChatMessage[]
  loading: boolean
}

export default function MessageList({ messages, loading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🤖</div>
        <h2>LangChain AI Chat</h2>
        <p>基于 DeepSeek 的智能对话助手</p>
        <p className="empty-hint">开始输入消息与 AI 对话</p>
      </div>
    )
  }

  return (
    <div className="message-list">
      {messages.map((msg) => (
        <div key={msg.id} className={`message ${msg.role}`}>
          <div className="message-avatar">
            {msg.role === 'user' ? '👤' : '🤖'}
          </div>
          <div className="message-content">
            <div className="message-header">
              <span className="message-role">
                {msg.role === 'user' ? '你' : 'AI 助手'}
              </span>
              <span className="message-time">
                {new Date(msg.timestamp).toLocaleTimeString('zh-CN', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
            <div className="message-bubble">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          </div>
        </div>
      ))}

      {loading && (
        <div className="message assistant">
          <div className="message-avatar">🤖</div>
          <div className="message-content">
            <div className="message-header">
              <span className="message-role">AI 助手</span>
            </div>
            <div className="message-bubble">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
