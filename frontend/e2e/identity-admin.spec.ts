import { expect, test, type APIRequestContext, type Page } from '@playwright/test'
import { fileURLToPath } from 'node:url'
import { readFile } from 'node:fs/promises'

const BASE = 'http://127.0.0.1:5173'
const FINDER_EMAIL = 'synthetic.user@example.test'
const FINDER_PASSWORD = 'SyntheticUser123!'
const ADMIN_EMAIL = 'synthetic.admin@example.test'
const ADMIN_PASSWORD = 'SyntheticAdmin123!'
const CLAIMANT = {
  username: 'identity-owner',
  email: 'identity-owner@example.test',
  password: 'IdentityOwner123!',
}
const ID_IMAGE = fileURLToPath(new URL('./assets/synthetic-id.png', import.meta.url))

function cnId(prefix17: string): string {
  const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  const checks = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
  const sum = [...prefix17].reduce((total, digit, index) => total + Number(digit) * weights[index], 0)
  return prefix17 + checks[sum % 11]
}

const SUCCESS_ID = cnId('11010120000101001')
const LOCKED_SECRET_ID = cnId('11010519491231002')
const SECOND_WRONG_ID = cnId('32010119900101001')

async function json<T>(response: Awaited<ReturnType<APIRequestContext['get']>>, status = 200): Promise<T> {
  const body = await response.json()
  expect(response.status(), JSON.stringify(body)).toBe(status)
  return body as T
}

async function loginApi(request: APIRequestContext, email: string, password: string): Promise<string> {
  const body = await json<{ tokens: { access_token: string } }>(
    await request.post(`${BASE}/api/auth/login`, { data: { email, password } }),
  )
  return body.tokens.access_token
}

async function registerApi(request: APIRequestContext): Promise<string> {
  const body = await json<{ tokens: { access_token: string } }>(
    await request.post(`${BASE}/api/auth/register`, { data: CLAIMANT }),
    201,
  )
  return body.tokens.access_token
}

function headers(token: string) {
  return { Authorization: `Bearer ${token}` }
}

async function loginUi(page: Page, email: string, password: string) {
  await page.goto('/login')
  await page.getByPlaceholder('请输入邮箱地址').fill(email)
  await page.getByPlaceholder('请输入密码').fill(password)
  const loginResponse = page.waitForResponse((response) =>
    response.url().endsWith('/api/auth/login') && response.request().method() === 'POST')
  await page.getByRole('button', { name: '登录' }).click()
  expect((await loginResponse).status()).toBe(200)
  await expect(page).toHaveURL(email === ADMIN_EMAIL ? `${BASE}/admin` : `${BASE}/`)
}

async function navigateInApp(page: Page, path: string) {
  await page.evaluate((nextPath) => {
    window.history.pushState({}, '', nextPath)
    window.dispatchEvent(new PopStateEvent('popstate'))
  }, path)
  await expect(page).toHaveURL(new RegExp(`${path.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`))
}

async function publishIdentityInUi(page: Page): Promise<string> {
  let recordId = ''
  page.on('response', async (response) => {
    if (response.url().endsWith('/api/found-records') && response.request().method() === 'POST' && response.status() === 201) {
      recordId = (await response.json() as { id: string }).id
    }
  })
  await page.getByRole('navigation').getByRole('link', { name: '我要招领' }).click()
  await expect(page).toHaveURL(/\/found\/new$/)
  await page.getByPlaceholder('物品名称').fill('SYNTHETIC ID 成功路径')
  await page.getByLabel('物品类别').selectOption('IDENTITY_CARD')
  await page.getByLabel('拾取地点').selectOption('LIBRARY')
  await page.getByLabel('拾取时间').fill('2026-07-17T10:00')
  await page.getByPlaceholder(/公开描述/).fill('图书馆三楼 302 室拾得 SYNTHETIC ID')
  await page.getByLabel('选择物品图片').setInputFiles(ID_IMAGE)
  await page.getByRole('button', { name: '创建草稿并继续' }).click()
  await expect(page.getByLabel('完整证件号')).toBeVisible()

  await page.getByLabel('完整证件号').fill(SUCCESS_ID)
  await page.getByRole('checkbox').check()
  const picker = page.getByTestId('redaction-picker')
  await picker.scrollIntoViewIfNeeded()
  const box = await picker.boundingBox()
  expect(box).not.toBeNull()
  await page.mouse.move(box!.x + box!.width * 0.45, box!.y + box!.height * 0.3)
  await page.mouse.down()
  await page.mouse.move(box!.x + box!.width * 0.82, box!.y + box!.height * 0.65, { steps: 5 })
  await page.mouse.up()
  await expect(page.getByText(/已选择区域/)).not.toContainText('尚未选择')

  const identityResponse = page.waitForResponse((response) =>
    response.url().includes('/identity-confirmation') && response.request().method() === 'POST')
  const redactionResponse = page.waitForResponse((response) =>
    response.url().includes('/redaction') && response.request().method() === 'POST')
  const publishResponse = page.waitForResponse((response) =>
    response.url().endsWith('/publish') && response.request().method() === 'POST')
  await page.getByRole('button', { name: '确认信息并发布' }).click()
  expect((await identityResponse).status()).toBe(200)
  expect((await redactionResponse).status()).toBe(201)
  expect((await publishResponse).status()).toBe(200)
  await expect(page).toHaveURL(/\/found\/[0-9a-f-]+$/)
  expect(recordId).not.toBe('')
  return recordId
}

async function publishIdentityApi(
  request: APIRequestContext,
  token: string,
  fullNumber: string,
  name: string,
): Promise<string> {
  const auth = headers(token)
  const draft = await json<{ id: string; version: number }>(
    await request.post(`${BASE}/api/found-records`, {
      headers: auth,
      data: { event_time: '2026-07-17T10:05:00+08:00', location_area: 'LIBRARY' },
    }),
    201,
  )
  const uploaded = await json<{ image_asset_id: string }>(
    await request.post(`${BASE}/api/uploads`, {
      headers: auth,
      multipart: {
        record_id: draft.id,
        purpose: 'FINDER_ORIGINAL',
        file: { name: 'synthetic-id.png', mimeType: 'image/png', buffer: await readFile(ID_IMAGE) },
      },
    }),
    201,
  )
  const confirmed = await json<{ version: number }>(
    await request.put(`${BASE}/api/found-records/${draft.id}/confirmation`, {
      headers: auth,
      data: {
        expected_version: draft.version,
        public_category: 'IDENTITY_CARD',
        name_public: name,
        description_public: '图书馆三楼 302 室拾得 SYNTHETIC ID',
        event_time: '2026-07-17T10:05:00+08:00',
        location_area: 'LIBRARY',
      },
    }),
  )
  await json(await request.post(`${BASE}/api/found-records/${draft.id}/identity-confirmation`, {
    headers: auth,
    data: { full_number: fullNumber, digits_confirmed: true },
  }))
  await json(await request.post(`${BASE}/api/found-records/${draft.id}/redaction`, {
    headers: auth,
    data: {
      original_asset_id: uploaded.image_asset_id,
      region: { x: 420, y: 340, width: 370, height: 80 },
    },
  }), 201)
  await json(await request.post(`${BASE}/api/found-records/${draft.id}/publish`, {
    headers: auth,
    data: { expected_version: confirmed.version },
  }))
  return draft.id
}

async function createLostAndMatch(
  request: APIRequestContext,
  token: string,
  category: string,
  name: string,
): Promise<{ lostId: string; candidates: Array<{ id: string; found_record_id: string }> }> {
  const auth = headers(token)
  const lost = await json<{ id: string }>(
    await request.post(`${BASE}/api/lost-records`, {
      headers: auth,
      data: {
        public_category: category,
        location_area: 'LIBRARY',
        event_time: '2026-07-17T10:06:00+08:00',
        name_public: name,
        description_public: `图书馆三楼 302 室遗失 ${name}`,
      },
    }),
    201,
  )
  const match = await request.get(`${BASE}/api/lost-records/${lost.id}/match`, { headers: auth })
  expect(match.status(), await match.text()).toBe(200)
  const candidates = await json<Array<{ id: string; found_record_id: string }>>(
    await request.get(`${BASE}/api/lost-records/${lost.id}/candidates`, { headers: auth }),
  )
  return { lostId: lost.id, candidates }
}

async function publishOtherApi(request: APIRequestContext, token: string, name: string): Promise<string> {
  const auth = headers(token)
  const draft = await json<{ id: string; version: number }>(
    await request.post(`${BASE}/api/found-records`, {
      headers: auth,
      data: { event_time: '2026-07-17T11:00:00+08:00', location_area: 'LIBRARY' },
    }),
    201,
  )
  const confirmed = await json<{ version: number }>(
    await request.put(`${BASE}/api/found-records/${draft.id}/confirmation`, {
      headers: auth,
      data: {
        expected_version: draft.version,
        public_category: 'OTHER_CATEGORY',
        name_public: name,
        description_public: '图书馆二楼阅览区拾得 SYNTHETIC OTHER',
        event_time: '2026-07-17T11:00:00+08:00',
        location_area: 'LIBRARY',
      },
    }),
  )
  await json(await request.post(`${BASE}/api/found-records/${draft.id}/questions`, {
    headers: auth,
    data: { hidden_description: '伞柄底部一道细小裂纹，伞套内侧字母A' },
  }))
  await json(await request.post(`${BASE}/api/found-records/${draft.id}/publish`, {
    headers: auth,
    data: { expected_version: confirmed.version },
  }))
  return draft.id
}

test('proves identity publish, verification limits, admin decisions and audit', async ({ page, request }) => {
  test.setTimeout(120_000)
  const finderToken = await loginApi(request, FINDER_EMAIL, FINDER_PASSWORD)
  await loginUi(page, FINDER_EMAIL, FINDER_PASSWORD)
  const successFoundId = await publishIdentityInUi(page)
  const lockedFoundId = await publishIdentityApi(
    request,
    finderToken,
    LOCKED_SECRET_ID,
    'SYNTHETIC ID 锁定路径',
  )
  const claimantToken = await registerApi(request)

  const successMatch = await createLostAndMatch(request, claimantToken, 'IDENTITY_CARD', 'SYNTHETIC ID 成功寻物')
  const successCandidate = successMatch.candidates.find((candidate) => candidate.found_record_id === successFoundId)
  expect(successCandidate).toBeTruthy()

  await loginUi(page, CLAIMANT.email, CLAIMANT.password)
  await navigateInApp(page, `/claims/identity/${successCandidate!.id}`)
  await page.getByPlaceholder('请输入 18 位身份证号码').fill(SUCCESS_ID)
  await page.getByRole('button', { name: '提交验证' }).click()
  await expect(page).toHaveURL(/\/claims\/[0-9a-f-]+\/progress$/)
  await expect(page.getByRole('heading', { name: '待交接' })).toBeVisible()

  const lockedMatch = await createLostAndMatch(request, claimantToken, 'IDENTITY_CARD', 'SYNTHETIC ID 锁定寻物')
  const lockedCandidate = lockedMatch.candidates.find((candidate) => candidate.found_record_id === lockedFoundId)
  expect(lockedCandidate).toBeTruthy()
  await navigateInApp(page, `/claims/identity/${lockedCandidate!.id}`)
  await page.getByPlaceholder('请输入 18 位身份证号码').fill(SUCCESS_ID)
  await page.getByRole('button', { name: '提交验证' }).click()
  await expect(page.getByRole('alert')).toContainText('剩余 1 次尝试')
  await page.getByPlaceholder('请输入 18 位身份证号码').fill(SECOND_WRONG_ID)
  await page.getByRole('button', { name: '提交验证' }).click()
  await expect(page.getByRole('alert')).toContainText('安全核验已锁定')
  await expect(page.getByRole('button', { name: '申请人工复核' })).toBeVisible()

  const claimFoundId = await publishOtherApi(request, finderToken, 'SYNTHETIC OTHER 认领管理员路径')
  const claimMatch = await createLostAndMatch(request, claimantToken, 'OTHER_CATEGORY', 'SYNTHETIC OTHER 认领复核')
  const otherCandidate = claimMatch.candidates.find((candidate) => candidate.found_record_id === claimFoundId)
  expect(otherCandidate).toBeTruthy()
  const questions = await json<Array<{ id: string }>>(
    await request.get(`${BASE}/api/candidates/${otherCandidate!.id}/questions`, { headers: headers(claimantToken) }),
  )
  const pendingClaim = await json<{ claim_id: string; status: string }>(
    await request.post(`${BASE}/api/candidates/${otherCandidate!.id}/claims/answers`, {
      headers: headers(claimantToken),
      data: { answers: questions.map((question) => ({ question_id: question.id, answer: '完全错误' })) },
    }),
  )
  expect(pendingClaim.status).toBe('PENDING_ADMIN_REVIEW')

  const unmatchedFoundId = await publishOtherApi(request, finderToken, 'SYNTHETIC OTHER 未匹配管理员路径')
  const unmatchedMatch = await createLostAndMatch(request, claimantToken, 'OTHER_CATEGORY', 'SYNTHETIC OTHER 未匹配复核')
  const unmatchedCandidate = unmatchedMatch.candidates.find((candidate) => candidate.found_record_id === unmatchedFoundId)
  expect(unmatchedCandidate).toBeTruthy()
  const unmatched = await json<{ id: string }>(
    await request.post(`${BASE}/api/lost-records/${unmatchedMatch.lostId}/review-requests`, {
      headers: headers(claimantToken),
      data: { reason: '候选信息仍需管理员确认' },
    }),
    201,
  )

  await loginUi(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await navigateInApp(page, `/admin/reviews/${pendingClaim.claim_id}`)
  await page.getByLabel('处理理由').fill('E2E 管理员确认进入交接')
  await page.getByRole('button', { name: '提交决定' }).click()
  await expect(page).toHaveURL(/\/admin$/)

  await navigateInApp(page, `/admin/reviews/${unmatched.id}`)
  await page.getByRole('radio', { name: /SYNTHETIC OTHER 未匹配管理员路径/ }).check()
  await page.getByLabel('处理理由').fill('E2E 推荐安全候选')
  await page.getByRole('button', { name: '提交决定' }).click()
  await expect(page).toHaveURL(/\/admin$/)

  await navigateInApp(page, '/admin/audit')
  await expect(page.getByRole('heading', { name: '审计日志' })).toBeVisible()
  await expect(page.getByText('ADMIN_REVIEW_DECIDED').first()).toBeVisible()
  expect(await page.getByText('ADMIN_REVIEW_DECIDED').count()).toBeGreaterThanOrEqual(2)
})
