import { Dispatch, SetStateAction } from 'react'
import './Sidebar.css'

type PageType = 'chat' | 'upload' | 'library'

interface SidebarProps {
  currentPage: PageType
  setCurrentPage: Dispatch<SetStateAction<PageType>>
}

export default function Sidebar({ currentPage, setCurrentPage }: SidebarProps) {
  const navItems: { id: PageType; label: string }[] = [
    { id: 'chat', label: 'Chat' },
    { id: 'upload', label: 'Upload' },
    { id: 'library', label: 'Library' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">ChatDocs</h1>
        <p className="sidebar-subtitle">AI-Powered PDF Q&A</p>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-button ${currentPage === item.id ? 'active' : ''}`}
            onClick={() => setCurrentPage(item.id)}
            aria-current={currentPage === item.id ? 'page' : undefined}
          >
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <p className="footer-text">v1.0.0</p>
      </div>
    </aside>
  )
}
