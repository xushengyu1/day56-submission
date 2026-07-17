import { expect, type APIRequestContext, type APIResponse, type Page } from '@playwright/test'

export interface TestUser {
  username: string
  email: string
  password: string
}

export interface AuthenticatedTestUser extends TestUser {
  accessToken: string
}

export interface RecordInput {
  category: 'ELECTRONICS' | 'IDENTITY_CARD' | 'CLOTHING' | 'STATIONERY' | 'OTHER_CATEGORY'
  location: 'DORMITORY' | 'CANTEEN' | 'TEACHING_BUILDING' | 'SCIENCE_BUILDING' | 'LIBRARY'
  eventTime: string
  name: string
  description: string
}

export function registrationUser(): TestUser {
  return {
    username: 'e2e-browser-user',
    email: 'e2e-browser-user@example.test',
    password: 'e2e-password-123',
  }
}

export function uniqueUser(prefix: string): TestUser {
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  return {
    username: `${prefix}-${suffix}`,
    email: `${prefix}-${suffix}@example.test`,
    password: 'e2e-password-123',
  }
}

async function json<T>(response: APIResponse, expectedStatus: number): Promise<T> {
  const body = await response.text()
  expect(response.status(), body).toBe(expectedStatus)
  return JSON.parse(body) as T
}

function authorization(user: AuthenticatedTestUser) {
  return { Authorization: `Bearer ${user.accessToken}` }
}

export async function registerApi(
  request: APIRequestContext,
  user: TestUser,
): Promise<AuthenticatedTestUser> {
  const response = await request.post('/api/auth/register', { data: user })
  const body = await json<{ tokens: { access_token: string } }>(response, 201)
  return { ...user, accessToken: body.tokens.access_token }
}

export async function publishFoundRecord(
  request: APIRequestContext,
  user: AuthenticatedTestUser,
  input: RecordInput,
): Promise<string> {
  const headers = authorization(user)
  const draft = await json<{ id: string; version: number }>(
    await request.post('/api/found-records', {
      headers,
      data: { event_time: input.eventTime, location_area: input.location },
    }),
    201,
  )
  const confirmation = await json<{ version: number }>(
    await request.put(`/api/found-records/${draft.id}/confirmation`, {
      headers,
      data: {
        expected_version: draft.version,
        public_category: input.category,
        name_public: input.name,
        description_public: input.description,
        event_time: input.eventTime,
        location_area: input.location,
      },
    }),
    200,
  )
  await json(
    await request.post(`/api/found-records/${draft.id}/questions`, {
      headers,
      data: { hidden_description: '伞柄底部有一道细小裂纹，伞套内侧写有字母A。' },
    }),
    200,
  )
  const published = await json<{ id: string; status: string }>(
    await request.post(`/api/found-records/${draft.id}/publish`, {
      headers,
      data: { expected_version: confirmation.version },
    }),
    200,
  )
  expect(published.status).toBe('PUBLISHED')
  return published.id
}

export async function createLostRecord(
  request: APIRequestContext,
  user: AuthenticatedTestUser,
  input: RecordInput,
): Promise<string> {
  const created = await json<{ id: string; status: string }>(
    await request.post('/api/lost-records', {
      headers: authorization(user),
      data: {
        public_category: input.category,
        location_area: input.location,
        event_time: input.eventTime,
        name_public: input.name,
        description_public: input.description,
      },
    }),
    201,
  )
  expect(created.status).toBe('PUBLISHED')
  return created.id
}

export async function loginViaUi(page: Page, user: TestUser) {
  await page.goto('/login')
  await page.getByPlaceholder('请输入邮箱地址').fill(user.email)
  await page.getByPlaceholder('请输入密码').fill(user.password)
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL('http://127.0.0.1:5173/')
}

export async function logoutViaUi(page: Page, user: TestUser) {
  await page.getByRole('button', { name: new RegExp(user.username) }).click()
  await page.getByRole('button', { name: '退出登录' }).click()
  await expect(page).toHaveURL(/\/login$/)
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
