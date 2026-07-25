import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Chat from './components/Chat'
import type { Session } from './types'
import './App.css'

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

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([createSession()])
  const [activeSessionId, setActiveSessionId] = useState(sessions[0].id)
  const [connected] = useState(true)

  const handleSelectSession = (id: string) => setActiveSessionId(id)

  const handleNewSession = () => {
    const newSession = createSession()
    setSessions((prev) => [...prev, newSession])
    setActiveSessionId(newSession.id)
  }

  const handleDeleteSession = (id: string) => {
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== id)
      if (filtered.length === 0) {
        const ns = createSession()
        setActiveSessionId(ns.id)
        return [ns]
      }
      if (id === activeSessionId) {
        setActiveSessionId(filtered[0].id)
      }
      return filtered
    })
  }

  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        connected={connected}
      />
      <main className="main-content">
        <Chat key={activeSessionId} />
      </main>
    </div>
  )
}
