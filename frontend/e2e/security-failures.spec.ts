import { expect, test, type APIRequestContext, type Page, type Request } from '@playwright/test'
import { fileURLToPath } from 'node:url'

const BASE = 'http://127.0.0.1:5173'
const FINDER_EMAIL = 'synthetic.user@example.test'
const FINDER_PASSWORD = 'SyntheticUser123!'
const FULL_ID = '110101200001010010'
const ID_IMAGE = fileURLToPath(new URL('./assets/synthetic-id.png', import.meta.url))

async function body<T>(response: Awaited<ReturnType<APIRequestContext['post']>>, status: number): Promise<T> {
  const value = await response.json()
  expect(response.status(), JSON.stringify(value)).toBe(status)
  return value as T
}

async function loginApi(request: APIRequestContext, email: string, password: string): Promise<string> {
  const result = await body<{ tokens: { access_token: string } }>(
    await request.post(`${BASE}/api/auth/login`, { data: { email, password } }),
    200,
  )
  return result.tokens.access_token
}

async function registerOther(request: APIRequestContext): Promise<string> {
  const result = await body<{ tokens: { access_token: string } }>(
    await request.post(`${BASE}/api/auth/register`, {
      data: {
        username: 'security-other',
        email: 'security-other@example.test',
        password: 'SecurityOther123!',
      },
    }),
    201,
  )
  return result.tokens.access_token
}

async function loginUi(page: Page) {
  await page.goto('/login')
  await page.getByPlaceholder('请输入邮箱地址').fill(FINDER_EMAIL)
  await page.getByPlaceholder('请输入密码').fill(FINDER_PASSWORD)
  const loginResponse = page.waitForResponse((response) =>
    response.url().endsWith('/api/auth/login') && response.request().method() === 'POST')
  await page.getByRole('button', { name: '登录' }).click()
  expect((await loginResponse).status()).toBe(200)
  await expect(page).toHaveURL(`${BASE}/`)
}

test('enforces role/private-asset guards and keeps tokens and full identity number out of browser surfaces', async ({ page, request }) => {
  test.setTimeout(90_000)
  const finderToken = await loginApi(request, FINDER_EMAIL, FINDER_PASSWORD)
  const otherToken = await registerOther(request)
  const observed: Request[] = []
  page.on('request', (next) => {
    if (['fetch', 'xhr'].includes(next.resourceType())) observed.push(next)
  })

  await loginUi(page)
  await page.getByRole('navigation').getByRole('link', { name: '我要招领' }).click()
  await expect(page).toHaveURL(/\/found\/new$/)
  await page.getByPlaceholder('物品名称').fill('SYNTHETIC ID 安全边界')
  await page.getByLabel('物品类别').selectOption('IDENTITY_CARD')
  await page.getByLabel('拾取地点').selectOption('LIBRARY')
  await page.getByLabel('拾取时间').fill('2026-07-17T12:00')
  await page.getByPlaceholder(/公开描述/).fill('图书馆一楼服务台拾得 SYNTHETIC ID')
  await page.getByLabel('选择物品图片').setInputFiles(ID_IMAGE)

  let originalAssetId = ''
  page.on('response', async (response) => {
    if (response.url().endsWith('/api/uploads') && response.status() === 201) {
      originalAssetId = (await response.json() as { image_asset_id: string }).image_asset_id
    }
  })
  await page.getByRole('button', { name: '创建草稿并继续' }).click()
  await expect(page.getByLabel('完整证件号')).toBeVisible()
  await page.getByLabel('完整证件号').fill(FULL_ID)
  await page.getByRole('checkbox').check()
  const picker = page.getByTestId('redaction-picker')
  await picker.scrollIntoViewIfNeeded()
  const box = await picker.boundingBox()
  expect(box).not.toBeNull()
  await page.mouse.move(box!.x + box!.width * 0.45, box!.y + box!.height * 0.3)
  await page.mouse.down()
  await page.mouse.move(box!.x + box!.width * 0.82, box!.y + box!.height * 0.65, { steps: 5 })
  await page.mouse.up()
  await page.getByRole('button', { name: '确认信息并发布' }).click()
  await expect(page).toHaveURL(/\/found\/[0-9a-f-]+$/)
  expect(originalAssetId).not.toBe('')

  const unauthenticatedAdmin = await request.get(`${BASE}/api/admin/reviews`)
  expect(unauthenticatedAdmin.status()).toBe(401)
  const normalUserAdmin = await request.get(`${BASE}/api/admin/reviews`, {
    headers: { Authorization: `Bearer ${otherToken}` },
  })
  expect(normalUserAdmin.status()).toBe(403)
  const privateAsset = await request.get(`${BASE}/api/assets/${originalAssetId}`, {
    headers: { Authorization: `Bearer ${otherToken}` },
  })
  expect(privateAsset.status()).toBe(404)

  const authorization = observed
    .map((item) => item.headers().authorization)
    .find((value): value is string => Boolean(value?.startsWith('Bearer ')))
  expect(authorization).toBeTruthy()
  const accessToken = authorization!.slice('Bearer '.length)
  for (const item of observed) {
    expect(item.url()).not.toContain(accessToken)
    if (!item.url().includes('/identity-confirmation')) {
      expect(item.postData() ?? '').not.toContain(FULL_ID)
    }
  }
  const storage = await page.evaluate(() => ({
    local: { ...localStorage },
    session: { ...sessionStorage },
  }))
  const serializedStorage = JSON.stringify(storage)
  expect(serializedStorage).not.toContain(accessToken)
  expect(serializedStorage).not.toContain(FULL_ID)
  await expect(page.locator('body')).not.toContainText(FULL_ID)

  const ownerPrivateAsset = await request.get(`${BASE}/api/assets/${originalAssetId}`, {
    headers: { Authorization: `Bearer ${finderToken}` },
  })
  expect(ownerPrivateAsset.status()).toBe(200)
})
