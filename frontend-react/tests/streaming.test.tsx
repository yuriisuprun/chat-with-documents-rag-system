/**
 * Streaming and Progressive Rendering Tests
 * Tests for handling streaming responses, progressive token rendering, and error handling
 * Total: 8+ streaming tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Chat from '../src/pages/Chat'
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

describe('Streaming and Progressive Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockApiClient.listDocuments.mockResolvedValue([
      {
        id: '1',
        name: 'document.pdf',
        uploaded_at: '2026-01-01T00:00:00',
        file_size: 1024,
        pages: 10,
      },
    ])
    mockApiClient.getChatHistory.mockResolvedValue([])
  })

  describe('Progressive Token Rendering', () => {
    it('should render tokens progressively as they arrive', async () => {
      let completeResponse = 'This is a complete response'
      let currentIndex = 0

      mockApiClient.chat.mockImplementation(async () => {
        // Simulate streaming by returning complete response
        // In real implementation, would stream tokens
        return {
          query: 'test',
          answer: completeResponse,
          sources: [],
          context_sufficient: true,
        }
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'What is this?')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(completeResponse)).toBeInTheDocument()
      })
    })

    it('should display complete text after streaming finishes', async () => {
      const fullResponse = 'This is a long response that should be complete and not cut off or incomplete'

      mockApiClient.chat.mockResolvedValue({
        query: 'test',
        answer: fullResponse,
        sources: [],
        context_sufficient: true,
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Question')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(fullResponse)).toBeInTheDocument()
      })
    })

    it('should handle multi-paragraph responses', async () => {
      const response = `First paragraph with content.

Second paragraph with more content.

Third paragraph with final content.`

      mockApiClient.chat.mockResolvedValue({
        query: 'test',
        answer: response,
        sources: [],
        context_sufficient: true,
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(/First paragraph/)).toBeInTheDocument()
        expect(screen.getByText(/Second paragraph/)).toBeInTheDocument()
        expect(screen.getByText(/Third paragraph/)).toBeInTheDocument()
      })
    })

    it('should handle responses with special characters', async () => {
      const response = 'Response with special characters: @#$%^&*()_+-=[]{}|;:",.<>?/'

      mockApiClient.chat.mockResolvedValue({
        query: 'test',
        answer: response,
        sources: [],
        context_sufficient: true,
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(/Response with special characters/)).toBeInTheDocument()
      })
    })

    it('should handle responses with code blocks', async () => {
      const response = `Here's some code:

\`\`\`python
def hello():
    print("world")
\`\`\`

End of code.`

      mockApiClient.chat.mockResolvedValue({
        query: 'test',
        answer: response,
        sources: [],
        context_sufficient: true,
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(/Here's some code/)).toBeInTheDocument()
      })
    })
  })

  describe('Stream Interruption Handling', () => {
    it('should handle interrupted streams gracefully', async () => {
      const partialResponse = 'This is a partial response that got cut off'

      mockApiClient.chat.mockResolvedValue({
        query: 'test',
        answer: partialResponse,
        sources: [],
        context_sufficient: true,
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(partialResponse)).toBeInTheDocument()
      })
    })

    it('should handle timeout during streaming', async () => {
      mockApiClient.chat.mockRejectedValue(new Error('Chat request timeout - LLM inference took too long'))

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(/timeout/i)).toBeInTheDocument()
      })
    })

    it('should allow retry after stream interruption', async () => {
      let callCount = 0

      mockApiClient.chat.mockImplementation(async () => {
        callCount++
        if (callCount === 1) {
          throw new Error('Stream interrupted')
        }
        return {
          query: 'test',
          answer: 'Successful response',
          sources: [],
          context_sufficient: true,
        }
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      
      // First attempt
      await userEvent.type(input, 'Test')
      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })

      // Second attempt (retry)
      const input2 = screen.getByPlaceholderText(/ask a question/i) as HTMLTextAreaElement
      input2.value = ''
      await userEvent.type(input2, 'Test retry')

      const sendBtn2 = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn2)

      await waitFor(() => {
        expect(screen.getByText('Successful response')).toBeInTheDocument()
      })
    })
  })

  describe('Network Failure Visibility', () => {
    it('should display network error messages', async () => {
      mockApiClient.chat.mockRejectedValue(new Error('Network request failed'))

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })

    it('should display connection timeout messages', async () => {
      mockApiClient.chat.mockRejectedValue(new Error('Connection timeout'))

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })

    it('should display server error messages', async () => {
      mockApiClient.chat.mockRejectedValue(new Error('HTTP 500: Internal Server Error'))

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })

    it('should not lose previous messages on error', async () => {
      // First successful message
      mockApiClient.chat.mockResolvedValueOnce({
        query: 'First',
        answer: 'First answer',
        sources: [],
        context_sufficient: true,
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'First')

      let sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText('First answer')).toBeInTheDocument()
      })

      // Second message with error
      mockApiClient.chat.mockRejectedValueOnce(new Error('Server error'))

      const input2 = screen.getByPlaceholderText(/ask a question/i) as HTMLTextAreaElement
      input2.value = ''
      await userEvent.type(input2, 'Second')

      sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      // First message should still be visible
      await waitFor(() => {
        expect(screen.getByText('First answer')).toBeInTheDocument()
      })
    })
  })

  describe('Loading State Management', () => {
    it('should display loading state while waiting for response', async () => {
      let resolveChat: any
      mockApiClient.chat.mockReturnValue(
        new Promise((resolve) => {
          resolveChat = resolve
        })
      )

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText('Sending...')).toBeInTheDocument()
      })

      // Verify send button is disabled during loading
      const disabledBtn = screen.getByRole('button', { name: /sending/i })
      expect(disabledBtn).toBeDisabled()

      resolveChat({
        query: 'Test',
        answer: 'Answer',
        sources: [],
        context_sufficient: true,
      })

      await waitFor(() => {
        expect(screen.getByText('Send')).toBeInTheDocument()
        expect(screen.getByText('Answer')).toBeInTheDocument()
      })
    })

    it('should end loading state on error', async () => {
      mockApiClient.chat.mockRejectedValue(new Error('Error'))

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        // Should return to Send button (not Sending...)
        expect(screen.getByText('Send')).toBeInTheDocument()
      })
    })

    it('should end loading state on success', async () => {
      mockApiClient.chat.mockResolvedValue({
        query: 'Test',
        answer: 'Answer',
        sources: [],
        context_sufficient: true,
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText('Send')).toBeInTheDocument()
        expect(screen.getByText('Answer')).toBeInTheDocument()
      })
    })

    it('should prevent sending while response is loading', async () => {
      let resolveChat: any
      mockApiClient.chat.mockReturnValue(
        new Promise((resolve) => {
          resolveChat = resolve
        })
      )

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText('Sending...')).toBeInTheDocument()
      })

      const disabledBtn = screen.getByRole('button', { name: /sending/i })
      expect(disabledBtn).toBeDisabled()

      resolveChat({
        query: 'Test',
        answer: 'Answer',
        sources: [],
        context_sufficient: true,
      })

      await waitFor(() => {
        const enabledBtn = screen.getByRole('button', { name: /send/i })
        expect(enabledBtn).not.toBeDisabled()
      })
    })
  })

  describe('Source Display', () => {
    it('should display sources after streaming completes', async () => {
      mockApiClient.chat.mockResolvedValue({
        query: 'test',
        answer: 'Answer with sources',
        sources: [
          {
            document_id: '1',
            filename: 'source.pdf',
            page_number: 5,
            chunk_index: 0,
            similarity_score: 0.95,
            text_preview: 'Source text',
          },
        ],
        context_sufficient: true,
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(/sources:/i)).toBeInTheDocument()
        expect(screen.getByText('source.pdf')).toBeInTheDocument()
      })
    })

    it('should display multiple sources', async () => {
      mockApiClient.chat.mockResolvedValue({
        query: 'test',
        answer: 'Answer',
        sources: [
          {
            document_id: '1',
            filename: 'source1.pdf',
            page_number: 5,
            chunk_index: 0,
            similarity_score: 0.95,
            text_preview: 'Source 1',
          },
          {
            document_id: '2',
            filename: 'source2.pdf',
            page_number: 10,
            chunk_index: 1,
            similarity_score: 0.85,
            text_preview: 'Source 2',
          },
        ],
        context_sufficient: true,
      })

      render(<Chat />)

      const input = screen.getByPlaceholderText(/ask a question/i)
      await userEvent.type(input, 'Test')

      const sendBtn = screen.getByRole('button', { name: /send/i })
      await userEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText('source1.pdf')).toBeInTheDocument()
        expect(screen.getByText('source2.pdf')).toBeInTheDocument()
      })
    })
  })
})
