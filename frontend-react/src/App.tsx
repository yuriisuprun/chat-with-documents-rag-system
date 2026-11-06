import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Chat from './pages/Chat'
import Upload from './pages/Upload'
import Library from './pages/Library'
import { apiClient } from './services/api'
import './App.css'

type PageType = 'chat' | 'upload' | 'library'

export default function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('chat')
  const [isOnline, setIsOnline] = useState(true)
  const [loading, setLoading] = useState(true)

  // Check backend connectivity on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await apiClient.health()
        setIsOnline(true)
      } catch (error) {
        console.error('Backend unavailable:', error)
        setIsOnline(false)
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
  }, [])

  if (loading) {
    return (
      <div className="app-container">
        <div className="loading-screen">
          <div className="spinner"></div>
          <p>Connecting to backend...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app-container">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
      <main className="main-content">
        <Header isOnline={isOnline} />
        {!isOnline && (
          <div className="offline-banner">
            ⚠️ Backend server is not available. Some features may not work. Make sure the FastAPI
            server is running on http://localhost:8000
          </div>
        )}
        <div className="page-content">
          {currentPage === 'chat' && <Chat />}
          {currentPage === 'upload' && <Upload />}
          {currentPage === 'library' && <Library />}
        </div>
      </main>
    </div>
  )
}
