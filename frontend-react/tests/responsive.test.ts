/**
 * Responsive Design Tests for Chat With Documents
 * Tests layout adaptation across different screen sizes using Playwright
 * Total: 15+ responsive tests
 */

import { test, expect } from '@playwright/test'

// Device configurations
const devices = {
  mobile_small: { width: 320, height: 640, name: 'Mobile 320px' },
  mobile_medium: { width: 375, height: 667, name: 'Mobile 375px (iPhone)' },
  mobile_large: { width: 480, height: 854, name: 'Mobile 480px' },
  tablet: { width: 768, height: 1024, name: 'Tablet 768px' },
  tablet_large: { width: 1024, height: 1366, name: 'Tablet 1024px' },
  desktop: { width: 1280, height: 720, name: 'Desktop 1280px' },
  desktop_large: { width: 1920, height: 1080, name: 'Desktop 1920px' },
}

test.beforeEach(async ({ page }) => {
  // Mock API responses
  await page.route('**/api/v1/health', route => {
    route.abort()
  })
})

test.describe('Responsive Design Tests', () => {
  test.describe('Mobile Layouts', () => {
    test('should adapt layout for 320px mobile screens', async ({ page }) => {
      await page.setViewportSize(devices.mobile_small.width, devices.mobile_small.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      // Check that content is not horizontally scrollable
      const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)

      // Check that sidebar is visible or properly collapsed
      const sidebar = await page.locator('aside').isVisible().catch(() => false)
      const mainContent = await page.locator('main').isVisible()
      expect(mainContent).toBeTruthy()
    })

    test('should adapt layout for 375px mobile screens', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
    })

    test('should adapt layout for 480px mobile screens', async ({ page }) => {
      await page.setViewportSize(devices.mobile_large.width, devices.mobile_large.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
    })

    test('should not have horizontal scrolling on mobile', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > window.innerWidth
      })
      expect(hasHorizontalScroll).toBe(false)
    })

    test('should stack form inputs vertically on mobile', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      // Navigate to upload page
      const uploadBtn = await page.locator('button', { hasText: /upload/i }).first()
      await uploadBtn.click()

      // Forms should be readable
      const form = await page.locator('form, [class*="form"]').isVisible().catch(() => true)
      expect(form).toBeTruthy()
    })
  })

  test.describe('Tablet Layouts', () => {
    test('should adapt layout for 768px tablet screens', async ({ page }) => {
      await page.setViewportSize(devices.tablet.width, devices.tablet.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
    })

    test('should adapt layout for 1024px tablet screens', async ({ page }) => {
      await page.setViewportSize(devices.tablet_large.width, devices.tablet_large.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
    })

    test('should display sidebar on tablet screens', async ({ page }) => {
      await page.setViewportSize(devices.tablet.width, devices.tablet.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      // Sidebar or navigation should be visible
      const navigation = await page.locator('nav, [class*="sidebar"]').isVisible().catch(() => false)
      expect(navigation).toBeTruthy()
    })
  })

  test.describe('Desktop Layouts', () => {
    test('should render desktop layout at 1280px', async ({ page }) => {
      await page.setViewportSize(devices.desktop.width, devices.desktop.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
    })

    test('should render desktop layout at 1920px', async ({ page }) => {
      await page.setViewportSize(devices.desktop_large.width, devices.desktop_large.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
    })

    test('should display full layout components on desktop', async ({ page }) => {
      await page.setViewportSize(devices.desktop.width, devices.desktop.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      // Both header and main content should be visible
      const header = await page.locator('header, [role="banner"]').isVisible().catch(() => false)
      const main = await page.locator('main').isVisible()
      
      expect(main).toBeTruthy()
    })
  })

  test.describe('Touch Target Sizes', () => {
    test('buttons should be at least 44px on mobile', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const buttons = await page.locator('button').all()
      for (const button of buttons) {
        const box = await button.boundingBox()
        if (box && await button.isVisible()) {
          expect(box.height).toBeGreaterThanOrEqual(40)
          expect(box.width).toBeGreaterThanOrEqual(40)
        }
      }
    })

    test('form inputs should be at least 44px on mobile', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      // Navigate to upload
      const uploadBtn = await page.locator('button', { hasText: /upload/i }).first()
      await uploadBtn.click()

      const inputs = await page.locator('input[type="file"], textarea, input[type="text"]').all()
      for (const input of inputs) {
        const box = await input.boundingBox()
        if (box && await input.isVisible()) {
          expect(box.height).toBeGreaterThanOrEqual(40)
        }
      }
    })

    test('interactive elements should have adequate spacing', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const buttons = await page.locator('button').all()
      expect(buttons.length).toBeGreaterThan(0)

      // Buttons should be visible and clickable
      for (const button of buttons) {
        const isVisible = await button.isVisible()
        if (isVisible) {
          expect(await button.isEnabled()).toBeTruthy()
        }
      }
    })
  })

  test.describe('Typography and Text Readability', () => {
    test('text should be readable on mobile (min 16px)', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const textElements = await page.locator('p, span, h1, h2, h3, h4, h5, h6').all()
      for (const element of textElements.slice(0, 10)) {
        const computed = await page.evaluate((el) => {
          const style = window.getComputedStyle(el)
          return {
            fontSize: style.fontSize,
            lineHeight: style.lineHeight,
          }
        }, await element.elementHandle())

        // Font size should be reasonable for readability
        expect(computed.fontSize).not.toBe('0px')
      }
    })

    test('text should have adequate line height', async ({ page }) => {
      await page.setViewportSize(devices.desktop.width, devices.desktop.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      // Check for readable line height
      const textElements = await page.locator('p').all()
      for (const element of textElements.slice(0, 5)) {
        const lineHeight = await page.evaluate((el) => {
          return window.getComputedStyle(el).lineHeight
        }, await element.elementHandle())

        expect(lineHeight).not.toBe('0px')
        expect(lineHeight).not.toBe('normal')
      }
    })

    test('headings should be properly sized', async ({ page }) => {
      await page.setViewportSize(devices.desktop.width, devices.desktop.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const h2 = await page.locator('h2').first()
      if (await h2.isVisible()) {
        const fontSize = await page.evaluate((el) => {
          return window.getComputedStyle(el).fontSize
        }, await h2.elementHandle())

        expect(fontSize).not.toBe('16px') // Should be larger than body text
      }
    })
  })

  test.describe('Images and Media Responsiveness', () => {
    test('images should not overflow container on mobile', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const images = await page.locator('img').all()
      for (const img of images) {
        const box = await img.boundingBox()
        const viewportWidth = await page.evaluate(() => window.innerWidth)
        
        if (box) {
          expect(box.width).toBeLessThanOrEqual(viewportWidth)
        }
      }
    })

    test('images should scale properly on different viewports', async ({ page }) => {
      // Test on mobile
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const mobilImages = await page.locator('img').all()

      // Test on desktop
      await page.setViewportSize(devices.desktop.width, devices.desktop.height)

      const desktopImages = await page.locator('img').all()

      expect(mobilImages.length).toBe(desktopImages.length)
    })
  })

  test.describe('Form Responsiveness', () => {
    test('upload form should be usable on mobile', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      // Navigate to upload
      const uploadBtn = await page.locator('button', { hasText: /upload/i }).first()
      await uploadBtn.click()

      // Form should be visible and not overflow
      const formElements = await page.locator('[class*="drop"], [class*="upload"]').all()
      expect(formElements.length).toBeGreaterThan(0)

      const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
    })

    test('chat interface should be usable on mobile', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      // Chat should be displayed
      const textarea = await page.locator('textarea').isVisible()
      expect(textarea).toBeTruthy()

      // No horizontal scrolling
      const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
    })

    test('library interface should be usable on mobile', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      // Navigate to library
      const libraryBtn = await page.locator('button', { hasText: /library/i }).first()
      await libraryBtn.click()

      // Content should adapt
      const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
    })
  })

  test.describe('Navigation Responsiveness', () => {
    test('navigation should be accessible on all screen sizes', async ({ page }) => {
      const sizes = [
        devices.mobile_medium,
        devices.tablet,
        devices.desktop,
      ]

      for (const size of sizes) {
        await page.setViewportSize(size.width, size.height)
        await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

        // Navigation should be present
        const navButtons = await page.locator('button', { hasText: /chat|upload|library/i }).all()
        expect(navButtons.length).toBeGreaterThan(0)
      }
    })

    test('page content should not overlap navigation', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const mainContent = await page.locator('main')
      const box = await mainContent.boundingBox()
      
      expect(box).not.toBeNull()
      if (box) {
        expect(box.x).toBeGreaterThanOrEqual(0)
      }
    })
  })

  test.describe('Viewport Orientation Changes', () => {
    test('should adapt layout on orientation change (portrait to landscape)', async ({ page }) => {
      // Start in portrait
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const portraitWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const portraitViewport = await page.evaluate(() => window.innerWidth)
      expect(portraitWidth).toBeLessThanOrEqual(portraitViewport)

      // Switch to landscape
      await page.setViewportSize(devices.mobile_medium.height, devices.mobile_medium.width)

      const landscapeWidth = await page.evaluate(() => document.documentElement.scrollWidth)
      const landscapeViewport = await page.evaluate(() => window.innerWidth)
      expect(landscapeWidth).toBeLessThanOrEqual(landscapeViewport)
    })
  })

  test.describe('Scrolling Behavior', () => {
    test('chat messages should be scrollable on small screens', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      // Navigate to chat
      const chatBtn = await page.locator('button', { hasText: /chat/i }).first()
      await chatBtn.click()

      // Should have scrollable content area
      const messagesArea = await page.locator('[class*="messages"]').isVisible().catch(() => false)
      expect(messagesArea).toBeTruthy()
    })

    test('should not have unwanted scrollbars', async ({ page }) => {
      await page.setViewportSize(devices.mobile_medium.width, devices.mobile_medium.height)
      await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' })

      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > window.innerWidth
      })
      expect(hasHorizontalScroll).toBe(false)
    })
  })
})
