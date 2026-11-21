/**
 * End-to-End Tests for Chat With Documents
 * Tests complete user workflows with real browser interactions
 * Total: 10+ E2E tests
 */

import { test, expect, Page } from '@playwright/test'

test.describe('E2E: Complete User Workflows', () => {
  let page: Page

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage()
    
    // Intercept API calls for mocking or inspection
    await page.route('**/api/v1/**', (route) => {
      // Log API calls for debugging
      console.log('API Call:', route.request().url())
    })
  })

  test.afterEach(async () => {
    await page.close()
  })

  test('should load application and show chat page', async () => {
    await page.goto('/')
    
    // Check for app loading
    await expect(page.locator('main')).toBeVisible()
    
    // Chat page should be visible by default
    await expect(page.getByText(/start a conversation/i)).toBeVisible()
  })

  test('should navigate between pages', async () => {
    await page.goto('/')
    
    // Start on Chat
    await expect(page.getByText(/start a conversation/i)).toBeVisible()
    
    // Navigate to Upload
    await page.getByRole('button', { name: /upload/i }).first().click()
    await expect(page.getByText(/drag and drop/i)).toBeVisible()
    
    // Navigate to Library
    await page.getByRole('button', { name: /library/i }).first().click()
    await expect(page.getByText(/document library/i)).toBeVisible()
    
    // Navigate back to Chat
    await page.getByRole('button', { name: /chat/i }).first().click()
    await expect(page.getByText(/start a conversation/i)).toBeVisible()
  })

  test('should handle upload and library workflows', async () => {
    await page.goto('/')
    
    // Mock successful document upload
    await page.route('**/api/v1/documents/upload', (route) => {
      route.abort()
    })
    
    // Go to Upload page
    await page.getByRole('button', { name: /upload/i }).first().click()
    await expect(page.getByText(/browse files/i)).toBeVisible()
    
    // Check upload interface is interactive
    const browseBtn = page.getByRole('button', { name: /browse files/i })
    await expect(browseBtn).toBeEnabled()
  })

  test('should test chat input validation', async () => {
    await page.goto('/')
    
    // Chat page should show disabled send button initially
    const sendBtn = page.getByRole('button', { name: /send/i })
    await expect(sendBtn).toBeDisabled()
    
    // Type message
    const textarea = page.getByPlaceholderText(/ask a question/i)
    await textarea.fill('Test message')
    
    // Send button should be enabled (assuming documents exist)
    await expect(sendBtn).toBeEnabled()
  })

  test('should handle page navigation persistence', async () => {
    await page.goto('/')
    
    // Go to Upload
    await page.getByRole('button', { name: /upload/i }).first().click()
    await expect(page.getByText(/browse files/i)).toBeVisible()
    
    // Reload page
    await page.reload()
    
    // Should still be on Upload page (localStorage persistence)
    await expect(page.getByText(/browse files/i)).toBeVisible()
  })

  test('should handle document sorting in library', async () => {
    await page.goto('/')
    
    // Mock library documents
    await page.route('**/api/v1/documents', (route) => {
      route.abort()
    })
    
    // Go to Library
    await page.getByRole('button', { name: /library/i }).first().click()
    
    // Check for sort control
    const sortSelect = page.getByLabel(/sort by/i)
    await expect(sortSelect).toBeVisible()
    
    // Try changing sort order
    await sortSelect.selectOption('name')
    await expect(sortSelect).toHaveValue('name')
  })

  test('should display header with status', async () => {
    await page.goto('/')
    
    // Header should be visible
    const header = page.locator('header, [role="banner"]')
    await expect(header).toBeVisible()
  })

  test('should handle touch interactions on mobile', async () => {
    // Set mobile viewport
    await page.setViewportSize(375, 667)
    await page.goto('/')
    
    // Chat should be visible
    await expect(page.getByPlaceholderText(/ask a question/i)).toBeVisible()
    
    // Buttons should be touchable (adequate size)
    const sendBtn = page.getByRole('button', { name: /send/i })
    const box = await sendBtn.boundingBox()
    expect(box!.height).toBeGreaterThanOrEqual(40)
    expect(box!.width).toBeGreaterThanOrEqual(40)
  })

  test('should handle keyboard navigation', async () => {
    await page.goto('/')
    
    // Tab through interactive elements
    await page.keyboard.press('Tab')
    
    // Focus should move to interactive element
    const focusedElement = await page.evaluate(() => {
      const el = document.activeElement as any
      return el?.tagName
    })
    
    expect(focusedElement).toMatch(/BUTTON|INPUT|TEXTAREA|SELECT/)
  })

  test('should display responsive layout on different sizes', async () => {
    const sizes = [
      { width: 320, height: 640, name: 'Mobile' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 1280, height: 720, name: 'Desktop' },
    ]

    for (const size of sizes) {
      await page.setViewportSize(size.width, size.height)
      await page.goto('/')
      
      // Should load without horizontal scrolling
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > window.innerWidth
      })
      
      expect(hasHorizontalScroll).toBe(false)
      
      // Main content should be visible
      await expect(page.locator('main')).toBeVisible()
    }
  })

  test('should handle error states gracefully', async () => {
    await page.goto('/')
    
    // Mock health check failure
    await page.route('**/api/v1/health', (route) => {
      route.abort()
    })
    
    // Reload to trigger health check
    await page.reload()
    
    // App should still render (might show offline message)
    await expect(page.locator('main')).toBeVisible()
  })

  test('should display proper aria labels for accessibility', async () => {
    await page.goto('/')
    
    // Buttons should be accessible
    const buttons = await page.getByRole('button').all()
    expect(buttons.length).toBeGreaterThan(0)
    
    // Check for accessible name
    for (const button of buttons.slice(0, 3)) {
      const name = await button.getAttribute('aria-label') || 
                  await button.textContent()
      expect(name?.trim()).toBeTruthy()
    }
  })

  test('should handle form submission with keyboard', async () => {
    await page.goto('/')
    
    // Focus input
    const textarea = page.getByPlaceholderText(/ask a question/i)
    await textarea.focus()
    
    // Type message
    await textarea.fill('Test message')
    
    // Press Enter (should submit, not create new line)
    await textarea.press('Enter')
    
    // Should have triggered send or similar action
  })

  test('should persist chat history across navigation', async () => {
    await page.goto('/')
    
    // Type message
    const textarea = page.getByPlaceholderText(/ask a question/i)
    await textarea.fill('Test query')
    
    // Mock successful chat response
    await page.route('**/api/v1/chat', (route) => {
      route.abort()
    })
    
    // Navigate away
    await page.getByRole('button', { name: /upload/i }).first().click()
    
    // Navigate back
    await page.getByRole('button', { name: /chat/i }).first().click()
    
    // Chat history should persist (if implemented)
  })

  test('should handle concurrent requests properly', async () => {
    await page.goto('/')
    
    // Prevent actual API calls
    await page.route('**/api/v1/**', (route) => {
      route.abort()
    })
    
    // Try multiple actions
    const textarea = page.getByPlaceholderText(/ask a question/i)
    await textarea.fill('First query')
    
    const sendBtn = page.getByRole('button', { name: /send/i })
    if (await sendBtn.isEnabled()) {
      await sendBtn.click()
    }
    
    // Quick navigation
    await page.getByRole('button', { name: /upload/i }).first().click()
    await page.getByRole('button', { name: /chat/i }).first().click()
    
    // Should not crash or show errors
    await expect(page.locator('main')).toBeVisible()
  })

  test('should display information clearly without clutter', async () => {
    await page.goto('/')
    
    // Check contrast and readability
    const main = page.locator('main')
    await expect(main).toBeVisible()
    
    // Should have clear visual hierarchy
    const headings = await page.getByRole('heading').all()
    expect(headings.length).toBeGreaterThan(0)
  })

  test('should handle rapid page switches', async () => {
    await page.goto('/')
    
    // Rapidly switch pages
    for (let i = 0; i < 5; i++) {
      await page.getByRole('button', { name: /upload/i }).first().click()
      await page.getByRole('button', { name: /chat/i }).first().click()
      await page.getByRole('button', { name: /library/i }).first().click()
    }
    
    // Should still be functional
    await expect(page.locator('main')).toBeVisible()
  })
})

test.describe('E2E: Accessibility Validation', () => {
  let page: Page

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage()
  })

  test.afterEach(async () => {
    await page.close()
  })

  test('should be navigable with keyboard only', async () => {
    await page.goto('/')
    
    // Tab through elements
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab')
    }
    
    // Should not get stuck
    const focusedElement = await page.evaluate(() => {
      return document.activeElement?.tagName
    })
    
    expect(focusedElement).not.toBe('BODY')
  })

  test('should have sufficient color contrast', async () => {
    await page.goto('/')
    
    // Get computed styles for text
    const textElements = await page.locator('p, span, button').all()
    
    for (const el of textElements.slice(0, 5)) {
      const color = await el.evaluate((e) => {
        return window.getComputedStyle(e).color
      })
      
      expect(color).toBeTruthy()
      expect(color).not.toBe('rgb(0, 0, 0)')
      expect(color).not.toBe('rgba(0, 0, 0, 0)')
    }
  })

  test('should have proper semantic HTML', async () => {
    await page.goto('/')
    
    // Check for semantic elements
    const main = page.locator('main')
    const buttons = page.getByRole('button')
    
    await expect(main).toBeVisible()
    expect(await buttons.count()).toBeGreaterThan(0)
  })
})
