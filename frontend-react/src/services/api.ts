interface ApiResponse<T> {
  data: T
  status: number
  message?: string
}

interface SourceReference {
  document_id: string
  filename: string
  page_number: number
  chunk_index: number
  similarity_score: number
  text_preview: string
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: SourceReference[]
}

interface ChatRequest {
  query: string
  document_ids?: string[]
  include_sources?: boolean
}

interface ChatResponse {
  query: string
  answer: string
  sources: SourceReference[]
  context_sufficient: boolean
  error?: string | null
}

interface Document {
  id: string
  name: string
  uploaded_at: string
  file_size: number
  pages?: number
}

interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

class ApiClient {
  private baseURL: string

  constructor(baseURL: string = 'http://localhost:8000/api/v1') {
    this.baseURL = baseURL
  }

  private async fetchWithTimeout(
    url: string,
    options: RequestInit = {},
    timeout: number = 10000
  ): Promise<Response> {
    const controller = new AbortController()
    let timeoutId: ReturnType<typeof setTimeout> | null = null

    if (timeout > 0) {
      timeoutId = setTimeout(() => {
        console.warn(`[fetchWithTimeout] Request timeout after ${timeout}ms for ${url}`)
        controller.abort()
      }, timeout)
    }

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      })
      if (timeoutId) clearTimeout(timeoutId)
      return response
    } catch (error) {
      if (timeoutId) clearTimeout(timeoutId)
      throw error
    }
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const contentType = response.headers.get('content-type')
      let errorDetail = response.statusText

      if (contentType?.includes('application/json')) {
        try {
          const errorData = await response.json()
          errorDetail = errorData.detail || errorData.message || errorDetail
        } catch {
          // Continue with statusText if JSON parsing fails
        }
      }

      throw new Error(`HTTP ${response.status}: ${errorDetail}`)
    }

    const contentType = response.headers.get('content-type')
    if (contentType?.includes('application/json')) {
      return await response.json()
    }

    return (await response.text()) as unknown as T
  }

  private handleFetchError(error: Error, url: string): Error {
    if (error.name === 'AbortError') {
      return new Error(`Request timeout or was aborted while requesting ${url}`)
    }
    return error
  }

  /**
   * Health check endpoint
   */
  async health(): Promise<any> {
    try {
      console.log('[health()] Starting health check...')
      const url = `${this.baseURL}/health?t=${Date.now()}`
      console.log('[health()] Requesting:', url)

      const response = await this.fetchWithTimeout(
        url,
        {
          method: 'GET',
          // No headers - GET requests don't need Content-Type, avoids CORS preflight
        },
        15000 // 15 second timeout - increased to account for occasional delays
      )

      const data = await this.handleResponse(response)
      console.log('[health()] Success:', data)
      return data
    } catch (error) {
      const err = error as Error
      if (err.name === 'AbortError') {
        console.error('[health()] Request was aborted (likely timeout)')
      } else {
        console.error('[health()] Failed:', error)
      }
      throw error
    }
  }

  /**
   * Upload a PDF document using Fetch API with manual progress tracking
   */
  async uploadDocument(
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)

    const url = `${this.baseURL}/documents/upload`
    const uploadTimeoutMs = 300000 // 5 minutes for large file processing
    
    console.log('[uploadDocument()] Starting upload to:', url, 'File size:', file.size)
    console.log(`[uploadDocument()] Timeout set to ${uploadTimeoutMs / 1000}s`)

    const controller = new AbortController()
    let timeoutId: ReturnType<typeof setTimeout> | null = null

    try {
      // Set timeout
      timeoutId = setTimeout(() => {
        console.warn(`[uploadDocument()] Upload timeout after ${uploadTimeoutMs / 1000}s`)
        controller.abort()
      }, uploadTimeoutMs)

      // Report initial progress
      if (onProgress) {
        onProgress({
          loaded: 0,
          total: file.size,
          percentage: 1, // Show 1% to indicate it's starting
        })
      }

      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
        // Note: Don't set headers - browser will set them automatically for FormData
      })

      if (timeoutId) clearTimeout(timeoutId)

      console.log('[uploadDocument()] Response received, status:', response.status)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('[uploadDocument()] Upload failed:', response.status, errorText)
        try {
          const errorData = JSON.parse(errorText)
          throw new Error(`HTTP ${response.status}: ${errorData.detail || 'Upload failed'}`)
        } catch {
          throw new Error(`HTTP ${response.status}: Upload failed`)
        }
      }

      const data = await response.json()
      console.log('[uploadDocument()] Upload success:', data)
      
      // Call progress callback with 100% to signal completion
      if (onProgress) {
        onProgress({
          loaded: file.size,
          total: file.size,
          percentage: 100,
        })
      }

      return data
    } catch (error) {
      if (timeoutId) clearTimeout(timeoutId)
      
      const err = error as Error
      if (err.name === 'AbortError') {
        console.error('[uploadDocument()] Upload was aborted (timeout after 5 minutes)')
        throw new Error('Upload timeout - document processing took too long. Try uploading a smaller file.')
      }
      
      console.error('[uploadDocument()] Upload error:', error)
      throw error
    }
  }

  /**
   * List all uploaded documents
   */
  async listDocuments(): Promise<Document[]> {
    const url = `${this.baseURL}/documents`
    console.log('[listDocuments()] Requesting:', url)

    const response = await this.fetchWithTimeout(
      url,
      {
        method: 'GET',
        // No headers - GET requests don't need Content-Type, avoids CORS preflight
      },
      20000 // 20 second timeout - increased to handle initialization
    )

    return this.handleResponse(response)
  }

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<void> {
    const url = `${this.baseURL}/documents/${documentId}`
    console.log('[deleteDocument()] Requesting:', url)

    const response = await this.fetchWithTimeout(
      url,
      {
        method: 'DELETE',
        // No headers - DELETE without body doesn't need Content-Type, avoids CORS preflight
      },
      10000 // 10 second timeout
    )

    await this.handleResponse(response)
  }

  /**
   * Chat with documents (RAG query)
   */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const url = `${this.baseURL}/chat`
    console.log('[chat()] Requesting:', url, request)

    try {
      const response = await this.fetchWithTimeout(
        url,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        },
        180000 // 180s timeout for LLM processing (3 minutes)
      )

      const data = await this.handleResponse(response)
      console.log('[chat()] Response received:', data)
      return data
    } catch (error) {
      const err = error as Error
      console.error('[chat()] Request failed:', err.message)
      if (err.name === 'AbortError') {
        console.error('[chat()] Request was aborted - LLM inference took too long')
        throw new Error('Chat request timeout - LLM inference took too long (try a simpler question)')
      }
      throw error
    }
  }

  /**
   * Get chat history
   */
  async getChatHistory(): Promise<ChatMessage[]> {
    const url = `${this.baseURL}/chat/history`
    console.log('[getChatHistory()] Requesting:', url)

    const response = await this.fetchWithTimeout(
      url,
      {
        method: 'GET',
        // No headers - GET requests don't need Content-Type, avoids CORS preflight
      },
      20000 // 20 second timeout - increased to handle initialization
    )

    return this.handleResponse(response)
  }

  /**
   * Clear chat history
   */
  async clearChatHistory(): Promise<void> {
    const url = `${this.baseURL}/chat/history`
    console.log('[clearChatHistory()] Requesting:', url)

    const response = await this.fetchWithTimeout(
      url,
      {
        method: 'DELETE',
        // No headers - DELETE without body doesn't need Content-Type, avoids CORS preflight
      },
      10000 // 10 second timeout
    )

    await this.handleResponse(response)
  }
}

export const apiClient = new ApiClient()

export type { ChatMessage, ChatRequest, ChatResponse, Document, UploadProgress, ApiResponse, SourceReference }
