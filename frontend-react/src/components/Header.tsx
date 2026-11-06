interface HeaderProps {
  isOnline: boolean
}

export default function Header({ isOnline }: HeaderProps) {
  return (
    <header className="header">
      <div className="header-content">
        <h1>Chat with Documents</h1>
        <div className="header-status">
          <span className={`status-indicator ${isOnline ? 'online' : 'offline'}`}></span>
          <span className="status-text">{isOnline ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>
    </header>
  )
}
