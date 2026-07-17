import { expect, test } from '@playwright/test'
import { captureApiRequests, expectNoStoredTokens, registrationUser } from './helpers'

test('registers, logs out and in through the real API without persisting tokens', async ({ page }) => {
  const user = registrationUser()
  const apiRequests = captureApiRequests(page)

  await page.goto('/records')
  await expect(page).toHaveURL(/\/login$/)
  await page.getByRole('link', { name: '注册新账号' }).click()

  await page.getByPlaceholder('请输入用户名').fill(user.username)
  await page.getByPlaceholder('请输入邮箱').fill(user.email)
  await page.getByPlaceholder('请设置密码（至少8位）').fill(user.password)
  await page.getByPlaceholder('请再次输入密码').fill(user.password)
  const registerResponse = page.waitForResponse((response) =>
    response.url().endsWith('/api/auth/register') && response.request().method() === 'POST')
  await page.getByRole('button', { name: '注册' }).click()
  expect((await registerResponse).status()).toBe(201)

  await expect(page).toHaveURL('http://127.0.0.1:5173/')
  await expect(page.getByRole('navigation').getByRole('link', { name: '我的记录' })).toBeVisible()
  await expectNoStoredTokens(page)

  await page.getByRole('button', { name: new RegExp(user.username) }).click()
  await page.getByRole('button', { name: '退出登录' }).click()
  await expect(page).toHaveURL(/\/login$/)

  await page.goto('/records')
  await expect(page).toHaveURL(/\/login$/)
  await page.getByPlaceholder('请输入邮箱地址').fill(user.email)
  await page.getByPlaceholder('请输入密码').fill(user.password)
  const loginResponse = page.waitForResponse((response) =>
    response.url().endsWith('/api/auth/login') && response.request().method() === 'POST')
  await page.getByRole('button', { name: '登录' }).click()
  expect((await loginResponse).status()).toBe(200)

  await expect(page).toHaveURL('http://127.0.0.1:5173/')
  await expectNoStoredTokens(page)
  expect(apiRequests).toContain('/api/auth/register')
  expect(apiRequests).toContain('/api/auth/login')
  expect(apiRequests.some((path) => path === '/api/auth/me')).toBe(true)
  expect(apiRequests.every((path) => path.startsWith('/api/'))).toBe(true)
})
