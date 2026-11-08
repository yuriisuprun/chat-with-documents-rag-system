import axios, { AxiosInstance, AxiosError } from 'axios'

interface ApiResponse<T> {
  data: T
  status: number
  message?: string
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: string[]
}

interface ChatRequest {
  query: string
  document_ids?: string[]
}

interface ChatResponse {
  answer: string
  sources: string[]
  confidence?: number
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
  private client: AxiosInstance

  constructor(baseURL: string = 'http://localhost:8000/api/v1') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    })

    // Add response interceptor for debugging
    this.client.interceptors.response.use(
      (response) => {
        console.log('[Axios] Success response interceptor:', { status: response.status, data: response.data })
        return response
      },
      (error: AxiosError) => {
        console.error('[Axios] Error interceptor:', { 
          status: error.response?.status,
          message: error.message,
          code: error.code,
        })
        throw this.handleError(error)
      }
    )
  }

  private handleError(error: AxiosError) {
    if (error.response) {
      return new Error(
        `Server Error: ${error.response.status} - ${
          (error.response.data as any)?.detail || error.response.statusText || 'Unknown error'
        }`
      )
    } else if (error.request) {
      return new Error('No response from server. Check your connection.')
    } else {
      return new Error(`Request Error: ${error.message}`)
    }
  }

  /**
   * Health check endpoint
   */
  async health(): Promise<any> {
    try {
      console.log('[health()] Starting health check with axios...')
      const url = `/health?t=${Date.now()}`
      console.log('[health()] Requesting:', url)
      
      const response = await this.client.get(url)
      console.log('[health()] Success:', response)
      return response.data
    } catch (error) {
      console.error('[health()] Axios failed:', error)
      
      // Fallback to fetch
      console.log('[health()] Trying fetch fallback...')
      try {
        const fullUrl = `http://localhost:8000/api/v1/health?t=${Date.now()}`
        console.log('[health()] Fetch URL:', fullUrl)
        const response = await fetch(fullUrl)
        console.log('[health()] Fetch success:', response)
        const data = await response.json()
        console.log('[health()] Fetch data:', data)
        return data
      } catch (fetchError) {
        console.error('[health()] Fetch also failed:', fetchError)
        throw error
      }
    }
  }

  /**
   * Upload a PDF document
   */
  async uploadDocument(
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.client.post('/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            percentage: Math.round((progressEvent.loaded / progressEvent.total) * 100),
          })
        }
      },
    })

    return response.data
  }

  /**
   * List all uploaded documents
   */
  async listDocuments(): Promise<Document[]> {
    const response = await this.client.get('/documents')
    return response.data
  }

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<void> {
    await this.client.delete(`/documents/${documentId}`)
  }

  /**
   * Chat with documents (RAG query)
   */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post('/chat', request)
    return response.data
  }

  /**
   * Get chat history
   */
  async getChatHistory(): Promise<ChatMessage[]> {
    const response = await this.client.get('/chat/history')
    return response.data
  }

  /**
   * Clear chat history
   */
  async clearChatHistory(): Promise<void> {
    await this.client.delete('/chat/history')
  }
}

export const apiClient = new ApiClient()

export type { ChatMessage, ChatRequest, ChatResponse, Document, UploadProgress, ApiResponse }
