import { useState, useEffect } from 'react'
import { apiClient, Document } from '../services/api'
import './Library.css'

export default function Library() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'name' | 'date' | 'size'>('date')

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    setLoading(true)
    setError(null)

    try {
      const docs = await apiClient.listDocuments()
      setDocuments(docs)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (docId: string, docName: string) => {
    if (confirm(`Delete "${docName}"? This cannot be undone.`)) {
      try {
        await apiClient.deleteDocument(docId)
        setDocuments((prev) => prev.filter((d) => d.id !== docId))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete document')
      }
    }
  }

  const getSortedDocuments = () => {
    const sorted = [...documents]

    switch (sortBy) {
      case 'name':
        return sorted.sort((a, b) => a.name.localeCompare(b.name))
      case 'size':
        return sorted.sort((a, b) => b.file_size - a.file_size)
      case 'date':
      default:
        return sorted.sort(
          (a, b) =>
            new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
        )
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleDateString([], {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading) {
    return (
      <div className="library-page">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading documents...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="library-page">
        <div className="error-state">
          <p className="error-message">Error: {error}</p>
          <button className="btn btn-primary" onClick={loadDocuments}>
            Try Again
          </button>
        </div>
      </div>
    )
  }

  const sortedDocs = getSortedDocuments()

  return (
    <div className="library-page">
      <div className="library-container">
        {/* Header with Stats */}
        <div className="library-header">
          <div className="header-info">
            <h2>Document Library</h2>
            <p className="header-subtitle">
              {documents.length} document{documents.length !== 1 ? 's' : ''} •{' '}
              {formatFileSize(documents.reduce((sum, d) => sum + d.file_size, 0))} total
            </p>
          </div>

          <div className="sort-control">
            <label htmlFor="sort-select">Sort by:</label>
            <select
              id="sort-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'date' | 'size')}
              className="sort-select"
            >
              <option value="date">Date Added</option>
              <option value="name">Name</option>
              <option value="size">File Size</option>
            </select>
          </div>
        </div>

        {documents.length === 0 ? (
          <div className="empty-library">
            <div className="empty-icon">📚</div>
            <h3>No documents yet</h3>
            <p>Upload PDF documents to get started. Go to the Upload tab to add files.</p>
          </div>
        ) : (
          <div className="documents-grid">
            {sortedDocs.map((doc) => (
              <div key={doc.id} className="document-card">
                <div className="card-header">
                  <div className="doc-icon">📄</div>
                  <div className="doc-meta">
                    <h3 className="doc-name" title={doc.name}>
                      {doc.name}
                    </h3>
                    <p className="doc-date">
                      {formatDate(doc.uploaded_at)}
                    </p>
                  </div>
                </div>

                <div className="card-info">
                  {doc.pages && (
                    <div className="info-item">
                      <span className="info-label">Pages:</span>
                      <span className="info-value">{doc.pages}</span>
                    </div>
                  )}
                  <div className="info-item">
                    <span className="info-label">Size:</span>
                    <span className="info-value">{formatFileSize(doc.file_size)}</span>
                  </div>
                </div>

                <button
                  className="delete-btn"
                  onClick={() => handleDelete(doc.id, doc.name)}
                  title="Delete document"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
