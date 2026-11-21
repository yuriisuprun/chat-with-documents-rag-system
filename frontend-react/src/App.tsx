import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Chat from './pages/Chat'
import Upload from './pages/Upload'
import Library from './pages/Library'
import { apiClient } from './services/api'
import './App.css'

type PageType = 'chat' | 'upload' | 'library'

const STORAGE_KEY = 'currentPage'

// Get saved page from localStorage or default to 'chat'
const getSavedPage = (): PageType => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'chat' || saved === 'upload' || saved === 'library') {
      return saved
    }
  } catch (e) {
    console.warn('Failed to read from localStorage:', e)
  }
  return 'chat'
}

export default function App() {
  const [currentPage, setCurrentPage] = useState<PageType>(getSavedPage)
  const [isOnline, setIsOnline] = useState(true)
  const [loading, setLoading] = useState(true)

  // Check backend connectivity on mount and periodically
  useEffect(() => {
    const checkHealth = async () => {
      try {
        console.log('[App] Health check initiated...')
        const response = await apiClient.health()
        console.log('[App] ✓ Backend is online:', response)
        setIsOnline(true)
      } catch (error) {
        console.error('[App] ✗ Backend is offline:', error)
        setIsOnline(false)
      } finally {
        setLoading(false)
      }
    }

    // Initial health check
    checkHealth()

    // Periodic health checks every 10 seconds
    const intervalId = setInterval(checkHealth, 10000)

    return () => clearInterval(intervalId)
  }, [])

  // Save current page to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, currentPage)
      console.log(`[App] Saved page preference: ${currentPage}`)
    } catch (e) {
      console.warn('Failed to save page preference to localStorage:', e)
    }
  }, [currentPage])

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
