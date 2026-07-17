import { expect, test } from '@playwright/test'
import {
  createLostRecord,
  loginViaUi,
  logoutViaUi,
  publishFoundRecord,
  registerApi,
  uniqueUser,
} from './helpers'

const categories = [
  ['', '物品类别（下拉选择）'],
  ['ELECTRONICS', '电子产品'],
  ['IDENTITY_CARD', '证件卡片'],
  ['CLOTHING', '服饰配饰'],
  ['STATIONERY', '学习用品'],
  ['OTHER_CATEGORY', '其他'],
]

const locations = [
  ['', '拾取地点（下拉选择）'],
  ['DORMITORY', '宿舍区'],
  ['CANTEEN', '食堂'],
  ['TEACHING_BUILDING', '教学楼'],
  ['SCIENCE_BUILDING', '科教楼'],
  ['LIBRARY', '图书馆'],
]

test('matches OTHER by taxonomy and detailed location, then claims and completes handoff', async ({ page, request }) => {
  const finder = await registerApi(request, uniqueUser('e2e-finder'))
  const owner = await registerApi(request, uniqueUser('e2e-owner'))
  const eventTime = '2026-07-17T02:30:00.000Z'
  const sameRoom = {
    category: 'OTHER_CATEGORY' as const,
    location: 'TEACHING_BUILDING' as const,
    eventTime,
    name: '蓝色折叠伞（A101）',
    description: '蓝色折叠伞，遗落在教学楼 A101 教室第三排。',
  }
  const otherRoom = {
    ...sameRoom,
    name: '蓝色折叠伞（A201）',
    description: '蓝色折叠伞，遗落在教学楼 A201 教室最后一排。',
  }

  await loginViaUi(page, finder)
  await page.getByRole('navigation').getByRole('link', { name: '我要招领' }).click()
  await expect(page.getByLabel('物品类别').locator('option')).toHaveCount(categories.length)
  await expect(page.getByLabel('拾取地点').locator('option')).toHaveCount(locations.length)
  expect(await page.getByLabel('物品类别').locator('option').evaluateAll((options) =>
    options.map((option) => [(option as HTMLOptionElement).value, option.textContent]))).toEqual(categories)
  expect(await page.getByLabel('拾取地点').locator('option').evaluateAll((options) =>
    options.map((option) => [(option as HTMLOptionElement).value, option.textContent]))).toEqual(locations)

  const sameRoomFoundId = await publishFoundRecord(request, finder, sameRoom)
  const otherRoomFoundId = await publishFoundRecord(request, finder, otherRoom)
  const wrongCategoryFoundId = await publishFoundRecord(request, finder, {
    ...sameRoom,
    category: 'ELECTRONICS',
    name: '蓝色电子伞（类别干扰项）',
  })
  const wrongAreaFoundId = await publishFoundRecord(request, finder, {
    ...sameRoom,
    location: 'LIBRARY',
    name: '蓝色折叠伞（区域干扰项）',
  })
  const lostId = await createLostRecord(request, owner, sameRoom)

  const matchResponse = await request.get(`/api/lost-records/${lostId}/match`, {
    headers: { Authorization: `Bearer ${owner.accessToken}` },
  })
  const matchBody = await matchResponse.text()
  expect(matchResponse.status(), matchBody).toBe(200)
  expect(matchBody).toContain('event: done')
  const candidatesResponse = await request.get(`/api/lost-records/${lostId}/candidates`, {
    headers: { Authorization: `Bearer ${owner.accessToken}` },
  })
  expect(candidatesResponse.status(), await candidatesResponse.text()).toBe(200)
  const candidates = await candidatesResponse.json() as Array<{
    id: string
    found_record_id: string
    total_score: number
  }>
  expect(candidates.map((candidate) => candidate.found_record_id)).toEqual([
    sameRoomFoundId,
    otherRoomFoundId,
  ])
  expect(candidates[0].total_score).toBeGreaterThan(candidates[1].total_score)
  expect(candidates.map((candidate) => candidate.found_record_id)).not.toContain(wrongCategoryFoundId)
  expect(candidates.map((candidate) => candidate.found_record_id)).not.toContain(wrongAreaFoundId)

  await logoutViaUi(page, finder)
  await loginViaUi(page, owner)
  await page.getByRole('navigation').getByRole('link', { name: '我的记录' }).click()
  await page.locator('.list-item').filter({ hasText: sameRoom.name }).click()
  await page.getByRole('link', { name: '查看匹配结果' }).click()
  await expect(page.getByText('2 个候选')).toBeVisible()
  const candidateLinks = page.locator(`a[href^="/candidates/"]`)
  await expect(candidateLinks).toHaveCount(2)
  await expect(candidateLinks.nth(0)).toContainText(sameRoom.name)
  await expect(candidateLinks.nth(1)).toContainText(otherRoom.name)

  const questionsResponsePromise = page.waitForResponse((response) =>
    response.url().includes(`/api/candidates/${candidates[0].id}/questions`)
    && response.request().method() === 'GET')
  await candidateLinks.nth(0).click()
  await page.getByRole('button', { name: '发起认领' }).click()
  const questionsResponse = await questionsResponsePromise
  expect(questionsResponse.status()).toBe(200)
  const questions = await questionsResponse.json() as Array<{
    id: string
    question_text: string
  }>
  expect(questions).toHaveLength(2)
  expect(questions.every((question) => /^[0-9a-f-]{36}$/.test(question.id))).toBe(true)
  await page.getByText('请描述伞柄底部可识别的细节。').locator('..')
    .getByPlaceholder('请详细描述您记忆中的情况...').fill('一道细小裂纹')
  await page.getByText('请描述伞套内侧的标记。').locator('..')
    .getByPlaceholder('请详细描述您记忆中的情况...').fill('字母A')

  const claimResponsePromise = page.waitForResponse((response) =>
    response.url().includes(`/api/candidates/${candidates[0].id}/claims/answers`)
    && response.request().method() === 'POST')
  await page.getByRole('button', { name: '提交核验' }).click()
  const claimResponse = await claimResponsePromise
  expect(claimResponse.status()).toBe(200)
  const claim = await claimResponse.json() as { claim_id: string; status: string }
  expect(claim.claim_id).toMatch(/^[0-9a-f-]{36}$/)
  expect(claim.claim_id).not.toBe(candidates[0].id)
  expect(claim.status).toBe('PENDING_HANDOFF')
  await expect(page).toHaveURL(new RegExp(`/claims/${claim.claim_id}/progress$`))
  await expect(page.getByText(`认领编号：${claim.claim_id}`)).toBeVisible()
  await expect(page.getByRole('heading', { name: '待交接' })).toBeVisible()
  await expect(page.getByText(finder.email)).toBeVisible()

  await logoutViaUi(page, owner)
  await loginViaUi(page, finder)
  await page.getByRole('navigation').getByRole('link', { name: '我的记录' }).click()
  const foundCard = page.locator('.list-item').filter({ hasText: sameRoom.name })
  await expect(foundCard).toHaveCount(1)
  await foundCard.getByRole('button', { name: '确认交接' }).click()
  const handoffResponsePromise = page.waitForResponse((response) =>
    response.url().endsWith(`/api/claims/${claim.claim_id}/handoff-complete`)
    && response.request().method() === 'POST')
  await foundCard.getByRole('button', { name: '确认已取走' }).click()
  const handoffResponse = await handoffResponsePromise
  expect(handoffResponse.status()).toBe(200)
  expect(await handoffResponse.json()).toEqual({ claim_id: claim.claim_id, status: 'CLAIMED' })
  await expect(foundCard).toContainText('物品已完成交接')
})
