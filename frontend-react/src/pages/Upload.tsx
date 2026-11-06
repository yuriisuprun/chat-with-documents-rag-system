import { useState, useRef } from 'react'
import { apiClient, UploadProgress } from '../services/api'
import './Upload.css'

interface UploadItem {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

export default function Upload() {
  const [uploads, setUploads] = useState<UploadItem[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (files: FileList | null) => {
    if (!files) return

    const newUploads: UploadItem[] = Array.from(files).map((file) => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      progress: 0,
      status: 'pending',
    }))

    setUploads((prev) => [...prev, ...newUploads])

    // Upload each file
    for (const upload of newUploads) {
      await uploadFile(upload.id, upload.file)
    }
  }

  const uploadFile = async (uploadId: string, file: File) => {
    // Check file size (limit to 50MB)
    const MAX_SIZE = 50 * 1024 * 1024
    if (file.size > MAX_SIZE) {
      setUploads((prev) =>
        prev.map((u) =>
          u.id === uploadId
            ? {
                ...u,
                status: 'error',
                error: 'File too large (max 50MB)',
              }
            : u
        )
      )
      return
    }

    // Check file type
    if (file.type !== 'application/pdf') {
      setUploads((prev) =>
        prev.map((u) =>
          u.id === uploadId
            ? {
                ...u,
                status: 'error',
                error: 'Only PDF files are supported',
              }
            : u
        )
      )
      return
    }

    setUploads((prev) =>
      prev.map((u) => (u.id === uploadId ? { ...u, status: 'uploading' } : u))
    )

    try {
      await apiClient.uploadDocument(file, (progress: UploadProgress) => {
        setUploads((prev) =>
          prev.map((u) => (u.id === uploadId ? { ...u, progress: progress.percentage } : u))
        )
      })

      setUploads((prev) =>
        prev.map((u) => (u.id === uploadId ? { ...u, status: 'success', progress: 100 } : u))
      )
    } catch (error) {
      setUploads((prev) =>
        prev.map((u) =>
          u.id === uploadId
            ? {
                ...u,
                status: 'error',
                error: error instanceof Error ? error.message : 'Upload failed',
              }
            : u
        )
      )
    }
  }

  const handleRemoveUpload = (uploadId: string) => {
    setUploads((prev) => prev.filter((u) => u.id !== uploadId))
  }

  const successCount = uploads.filter((u) => u.status === 'success').length
  const errorCount = uploads.filter((u) => u.status === 'error').length
  const uploadingCount = uploads.filter((u) => u.status === 'uploading').length

  return (
    <div className="upload-page">
      <div className="upload-container">
        <div className="upload-content">
          {/* Drag & Drop Zone */}
          <div
            className="drop-zone"
            onDragOver={(e) => {
              e.preventDefault()
              e.currentTarget.classList.add('drag-over')
            }}
            onDragLeave={(e) => {
              e.currentTarget.classList.remove('drag-over')
            }}
            onDrop={(e) => {
              e.preventDefault()
              e.currentTarget.classList.remove('drag-over')
              handleFileSelect(e.dataTransfer.files)
            }}
          >
            <div className="drop-icon">📄</div>
            <h2>Drag and drop your PDF files here</h2>
            <p>or</p>
            <button
              className="btn btn-primary"
              onClick={() => fileInputRef.current?.click()}
            >
              Browse Files
            </button>
            <p className="file-hint">Max file size: 50MB | Supported: PDF</p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf"
              onChange={(e) => handleFileSelect(e.currentTarget.files)}
              style={{ display: 'none' }}
            />
          </div>

          {/* Upload Statistics */}
          {uploads.length > 0 && (
            <div className="upload-stats">
              <div className="stat-item success">
                <span className="stat-number">{successCount}</span>
                <span className="stat-label">Uploaded</span>
              </div>
              <div className="stat-item pending">
                <span className="stat-number">{uploadingCount}</span>
                <span className="stat-label">Uploading</span>
              </div>
              <div className="stat-item error">
                <span className="stat-number">{errorCount}</span>
                <span className="stat-label">Failed</span>
              </div>
            </div>
          )}

          {/* Upload List */}
          {uploads.length > 0 && (
            <div className="uploads-list">
              <h3>Upload Queue</h3>
              {uploads.map((upload) => (
                <div key={upload.id} className={`upload-item upload-${upload.status}`}>
                  <div className="upload-info">
                    <div className="upload-name">{upload.file.name}</div>
                    <div className="upload-size">
                      {(upload.file.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                  </div>

                  {upload.status === 'uploading' && (
                    <div className="upload-progress">
                      <div className="progress-bar">
                        <div
                          className="progress-fill"
                          style={{ width: `${upload.progress}%` }}
                        ></div>
                      </div>
                      <span className="progress-text">{upload.progress}%</span>
                    </div>
                  )}

                  {upload.status === 'success' && <div className="upload-status">✓ Done</div>}

                  {upload.status === 'error' && (
                    <div className="upload-error">
                      <div className="error-message">{upload.error}</div>
                    </div>
                  )}

                  <button
                    className="remove-btn"
                    onClick={() => handleRemoveUpload(upload.id)}
                    title="Remove from list"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Help Section */}
          {uploads.length === 0 && (
            <div className="help-section">
              <h3>Tips</h3>
              <ul>
                <li>Upload PDF documents to build your knowledge base</li>
                <li>Multiple files can be uploaded at once</li>
                <li>Documents are indexed for semantic search</li>
                <li>Ask questions in the Chat tab to query your documents</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
