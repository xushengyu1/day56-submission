import { expect, type Page } from '@playwright/test'

export interface TestUser {
  username: string
  email: string
  password: string
}

export function registrationUser(): TestUser {
  return {
    username: 'e2e-browser-user',
    email: 'e2e-browser-user@example.test',
    password: 'e2e-password-123',
  }
}

export function captureApiRequests(page: Page): string[] {
  const requests: string[] = []
  page.on('request', (request) => {
    if (!['fetch', 'xhr'].includes(request.resourceType())) return
    const url = new URL(request.url())
    requests.push(url.pathname)
  })
  return requests
}

export async function expectNoStoredTokens(page: Page) {
  const storage = await page.evaluate(() => ({
    local: Object.keys(localStorage),
    session: Object.keys(sessionStorage),
  }))
  const tokenKey = /token/i
  expect(storage.local.filter((key) => tokenKey.test(key))).toEqual([])
  expect(storage.session.filter((key) => tokenKey.test(key))).toEqual([])
}
