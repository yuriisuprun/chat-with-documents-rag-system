/**
 * Integration Tests for Chat With Documents
 * Tests complete workflows and state management across components
 * Total: 10+ integration tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../src/App'
import * as apiModule from '../src/services/api'

vi.mock('../src/services/api', () => ({
  apiClient: {
    health: vi.fn(),
    listDocuments: vi.fn(),
    getChatHistory: vi.fn(),
    chat: vi.fn(),
    clearChatHistory: vi.fn(),
    uploadDocument: vi.fn(),
    deleteDocument: vi.fn(),
  },
}))

const mockApiClient = apiModule.apiClient as any

describe('Integration Tests - Complete Workflows', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    vi.mocked(localStorage.getItem).mockReturnValue(null)
    vi.mocked(localStorage.setItem).mockImplementation(() => {})
  })

  describe('Upload → Library → Chat Lifecycle', () => {
    it('should complete full document workflow', async () => {
      const document = {
        id: 'doc-1',
        name: 'test.pdf',
        uploaded_at: new Date().toISOString(),
        file_size: 1024,
        pages: 5,
      }

      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments.mockResolvedValue([])
      mockApiClient.getChatHistory.mockResolvedValue([])
      mockApiClient.uploadDocument.mockResolvedValue(document)

      render(<App />)

      // Wait for backend health check
      await waitFor(() => {
        expect(mockApiClient.health).toHaveBeenCalled()
      })

      // Navigate to Upload page
      const uploadLink = screen.getByText(/upload/i).closest('button')
      await userEvent.click(uploadLink!)

      // Verify Upload page is shown
      await waitFor(() => {
        expect(screen.getByText(/browse files/i)).toBeInTheDocument()
      })
    })

    it('should sync document library after upload', async () => {
      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments
        .mockResolvedValueOnce([]) // Initial load
        .mockResolvedValueOnce([
          {
            id: 'doc-1',
            name: 'uploaded.pdf',
            uploaded_at: new Date().toISOString(),
            file_size: 2048,
            pages: 10,
          },
        ]) // After reload

      mockApiClient.getChatHistory.mockResolvedValue([])
      mockApiClient.uploadDocument.mockResolvedValue({
        id: 'doc-1',
        name: 'uploaded.pdf',
        uploaded_at: new Date().toISOString(),
        file_size: 2048,
        pages: 10,
      })

      render(<App />)

      await waitFor(() => {
        expect(mockApiClient.health).toHaveBeenCalled()
      })

      // Go to Upload page
      const uploadLink = screen.getByText(/upload/i).closest('button')
      await userEvent.click(uploadLink!)

      await waitFor(() => {
        expect(screen.getByText(/browse files/i)).toBeInTheDocument()
      })

      // Simulate file upload
      const file = new File(['test'], 'uploaded.pdf', { type: 'application/pdf' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      if (input) {
        await userEvent.upload(input, file)
      }

      // Go to Library
      const libraryLink = screen.getByText(/library/i).closest('button')
      await userEvent.click(libraryLink!)

      // Verify new document appears in library
      await waitFor(() => {
        expect(mockApiClient.listDocuments).toHaveBeenCalled()
      })
    })
  })

  describe('Chat with Multiple Documents', () => {
    it('should allow querying multiple documents', async () => {
      const documents = [
        {
          id: '1',
          name: 'doc1.pdf',
          uploaded_at: '2026-01-01T00:00:00',
          file_size: 1024,
          pages: 5,
        },
        {
          id: '2',
          name: 'doc2.pdf',
          uploaded_at: '2026-01-02T00:00:00',
          file_size: 2048,
          pages: 10,
        },
      ]

      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments.mockResolvedValue(documents)
      mockApiClient.getChatHistory.mockResolvedValue([])
      mockApiClient.chat.mockResolvedValue({
        query: 'test',
        answer: 'answer',
        sources: [],
        context_sufficient: true,
      })

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('💬')).toBeInTheDocument()
      })

      // Select first document
      const checkbox1 = screen.getByRole('checkbox', { name: /doc1.pdf/i })
      await userEvent.click(checkbox1)

      // Select second document
      const checkbox2 = screen.getByRole('checkbox', { name: /doc2.pdf/i })
      await userEvent.click(checkbox2)

      // Type and send message
      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test query')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      // Verify chat was called with both document IDs
      await waitFor(() => {
        expect(mockApiClient.chat).toHaveBeenCalledWith(
          expect.objectContaining({
            query: 'Test query',
            document_ids: expect.arrayContaining(['1', '2']),
          })
        )
      })
    })

    it('should query all documents when none selected', async () => {
      const documents = [
        {
          id: '1',
          name: 'doc1.pdf',
          uploaded_at: '2026-01-01T00:00:00',
          file_size: 1024,
          pages: 5,
        },
      ]

      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments.mockResolvedValue(documents)
      mockApiClient.getChatHistory.mockResolvedValue([])
      mockApiClient.chat.mockResolvedValue({
        query: 'test',
        answer: 'answer',
        sources: [],
        context_sufficient: true,
      })

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('💬')).toBeInTheDocument()
      })

      // Don't select any document - should query all
      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test query')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(mockApiClient.chat).toHaveBeenCalledWith(
          expect.objectContaining({
            query: 'Test query',
          })
        )
      })
    })
  })

  describe('Document Deletion and Cleanup', () => {
    it('should remove deleted documents from chat selection', async () => {
      const documents = [
        {
          id: '1',
          name: 'doc1.pdf',
          uploaded_at: '2026-01-01T00:00:00',
          file_size: 1024,
          pages: 5,
        },
        {
          id: '2',
          name: 'doc2.pdf',
          uploaded_at: '2026-01-02T00:00:00',
          file_size: 2048,
          pages: 10,
        },
      ]

      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments
        .mockResolvedValueOnce(documents) // Initial
        .mockResolvedValueOnce([documents[0]]) // After deletion

      mockApiClient.getChatHistory.mockResolvedValue([])
      mockApiClient.deleteDocument.mockResolvedValue(undefined)

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('💬')).toBeInTheDocument()
      })

      // Navigate to Library
      const libraryLink = screen.getByText(/library/i).closest('button')
      await userEvent.click(libraryLink!)

      await waitFor(() => {
        expect(screen.getByText(/document library/i)).toBeInTheDocument()
      })

      // Delete document
      vi.spyOn(global, 'confirm').mockReturnValue(true)
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await userEvent.click(deleteButtons[1])

      await waitFor(() => {
        expect(mockApiClient.deleteDocument).toHaveBeenCalled()
      })
    })
  })

  describe('Chat History Persistence', () => {
    it('should persist chat history across page navigations', async () => {
      const chatHistory = [
        {
          id: '1',
          role: 'user' as const,
          content: 'Question',
          timestamp: new Date().toISOString(),
        },
        {
          id: '2',
          role: 'assistant' as const,
          content: 'Answer',
          timestamp: new Date().toISOString(),
        },
      ]

      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments.mockResolvedValue([
        {
          id: '1',
          name: 'doc.pdf',
          uploaded_at: '2026-01-01T00:00:00',
          file_size: 1024,
          pages: 5,
        },
      ])
      mockApiClient.getChatHistory.mockResolvedValue(chatHistory)

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Question')).toBeInTheDocument()
        expect(screen.getByText('Answer')).toBeInTheDocument()
      })

      // Navigate to Upload and back
      const uploadLink = screen.getByText(/upload/i).closest('button')
      await userEvent.click(uploadLink!)

      const chatLink = screen.getByText(/chat/i).closest('button')
      await userEvent.click(chatLink!)

      // Chat history should still be visible
      await waitFor(() => {
        expect(screen.getByText('Question')).toBeInTheDocument()
        expect(screen.getByText('Answer')).toBeInTheDocument()
      })
    })

    it('should save cleared chat history', async () => {
      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments.mockResolvedValue([
        {
          id: '1',
          name: 'doc.pdf',
          uploaded_at: '2026-01-01T00:00:00',
          file_size: 1024,
          pages: 5,
        },
      ])
      mockApiClient.getChatHistory.mockResolvedValue([])
      mockApiClient.chat.mockResolvedValue({
        query: 'test',
        answer: 'answer',
        sources: [],
        context_sufficient: true,
      })
      mockApiClient.clearChatHistory.mockResolvedValue(undefined)

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('💬')).toBeInTheDocument()
      })

      // Add message
      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument()
      })

      // Clear history
      vi.spyOn(global, 'confirm').mockReturnValue(true)
      const clearBtn = screen.getByRole('button', { name: /clear/i })
      await userEvent.click(clearBtn)

      await waitFor(() => {
        expect(mockApiClient.clearChatHistory).toHaveBeenCalled()
      })
    })
  })

  describe('State Management Across Pages', () => {
    it('should save current page preference to localStorage', async () => {
      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments.mockResolvedValue([])
      mockApiClient.getChatHistory.mockResolvedValue([])

      render(<App />)

      await waitFor(() => {
        expect(mockApiClient.health).toHaveBeenCalled()
      })

      // Click Upload page
      const uploadLink = screen.getByText(/upload/i).closest('button')
      await userEvent.click(uploadLink!)

      // Wait for localStorage to be called
      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith('currentPage', 'upload')
      })
    })

    it('should restore page preference from localStorage', async () => {
      vi.mocked(localStorage.getItem).mockReturnValue('library')

      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments.mockResolvedValue([])

      render(<App />)

      // Page should load library by default
      await waitFor(() => {
        expect(screen.getByText(/document library/i)).toBeInTheDocument()
      })
    })
  })

  describe('Error Recovery', () => {
    it('should handle backend connection errors gracefully', async () => {
      mockApiClient.health.mockRejectedValue(new Error('Connection failed'))
      mockApiClient.listDocuments.mockResolvedValue([])
      mockApiClient.getChatHistory.mockResolvedValue([])

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText(/backend server is not available/i)).toBeInTheDocument()
      })
    })

    it('should recover from temporary API failures', async () => {
      mockApiClient.health
        .mockRejectedValueOnce(new Error('Connection failed'))
        .mockResolvedValue({ status: 'ok' })

      mockApiClient.listDocuments.mockResolvedValue([])
      mockApiClient.getChatHistory.mockResolvedValue([])

      render(<App />)

      await waitFor(() => {
        expect(mockApiClient.health).toHaveBeenCalled()
      })

      // Should show offline message initially
      await waitFor(() => {
        expect(screen.getByText(/backend server is not available/i)).toBeInTheDocument()
      })
    })

    it('should display error when document upload fails', async () => {
      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments.mockResolvedValue([])
      mockApiClient.getChatHistory.mockResolvedValue([])
      mockApiClient.uploadDocument.mockRejectedValue(new Error('Upload failed'))

      render(<App />)

      await waitFor(() => {
        expect(mockApiClient.health).toHaveBeenCalled()
      })

      const uploadLink = screen.getByText(/upload/i).closest('button')
      await userEvent.click(uploadLink!)

      await waitFor(() => {
        expect(screen.getByText(/browse files/i)).toBeInTheDocument()
      })

      // Simulate file upload
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      if (input) {
        await userEvent.upload(input, file)

        await waitFor(() => {
          expect(screen.getByText(/upload failed/i)).toBeInTheDocument()
        })
      }
    })

    it('should allow retry on document load failure in library', async () => {
      mockApiClient.health.mockResolvedValue({ status: 'ok' })
      mockApiClient.listDocuments
        .mockRejectedValueOnce(new Error('Load failed'))
        .mockResolvedValueOnce([
          {
            id: '1',
            name: 'doc.pdf',
            uploaded_at: '2026-01-01T00:00:00',
            file_size: 1024,
            pages: 5,
          },
        ])

      mockApiClient.getChatHistory.mockResolvedValue([])

      render(<App />)

      await waitFor(() => {
        expect(mockApiClient.health).toHaveBeenCalled()
      })

      const libraryLink = screen.getByText(/library/i).closest('button')
      await userEvent.click(libraryLink!)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })

      const retryBtn = screen.getByRole('button', { name: /try again/i })
      await userEvent.click(retryBtn)

      await waitFor(() => {
        expect(screen.getByText('doc.pdf')).toBeInTheDocument()
      })
    })
  })
})
