import { useState, useRef, useEffect } from 'react'
import { apiClient, ChatMessage, Document } from '../services/api'
import './Chat.css'

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Load documents and chat history on mount
  useEffect(() => {
    loadDocuments()
    loadChatHistory()
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadDocuments = async () => {
    try {
      const docs = await apiClient.listDocuments()
      setDocuments(docs)
    } catch (error) {
      console.error('Failed to load documents:', error)
    }
  }

  const loadChatHistory = async () => {
    try {
      const history = await apiClient.getChatHistory()
      setMessages(history)
    } catch (error) {
      console.error('Failed to load chat history:', error)
    }
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await apiClient.chat({
        query: input,
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
      })

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        sources: response.sources,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to get response'}`,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleClear = async () => {
    if (confirm('Clear all chat history?')) {
      try {
        await apiClient.clearChatHistory()
        setMessages([])
      } catch (error) {
        console.error('Failed to clear history:', error)
      }
    }
  }

  const toggleDocumentSelection = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    )
  }

  return (
    <div className="chat-page">
      <div className="chat-container">
        {/* Messages */}
        <div className="messages-area">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💬</div>
              <h2>Start a conversation</h2>
              <p>Upload documents and ask questions about their content.</p>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div key={msg.id} className={`message message-${msg.role}`}>
                  <div className="message-bubble">
                    <p className="message-content">{msg.content}</p>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="message-sources">
                        <strong>Sources:</strong>
                        <ul>
                          {msg.sources.map((source, idx) => (
                            <li key={idx}>{source}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <span className="message-time">
                      {new Date(msg.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="input-area">
          {/* Document Filter */}
          {documents.length > 0 && (
            <div className="document-filter">
              <label>Filter by documents (optional):</label>
              <div className="document-checkboxes">
                {documents.map((doc) => (
                  <label key={doc.id} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={selectedDocIds.includes(doc.id)}
                      onChange={() => toggleDocumentSelection(doc.id)}
                    />
                    <span>{doc.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Message Input */}
          <div className="input-group">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              placeholder="Ask a question about your documents... (Shift+Enter for new line)"
              className="message-input"
              disabled={loading || documents.length === 0}
            />
            <div className="input-actions">
              <button
                onClick={handleSend}
                disabled={loading || !input.trim() || documents.length === 0}
                className="btn btn-primary"
              >
                {loading ? 'Sending...' : 'Send'}
              </button>
              {messages.length > 0 && (
                <button onClick={handleClear} className="btn btn-secondary">
                  Clear
                </button>
              )}
            </div>
          </div>

          {documents.length === 0 && (
            <p className="help-text">No documents uploaded. Go to the Upload tab to add documents.</p>
          )}
        </div>
      </div>
    </div>
  )
}
