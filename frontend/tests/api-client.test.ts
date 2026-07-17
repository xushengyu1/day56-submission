import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  apiClient,
  clearTokens,
  getAccessToken,
  isMockMode,
  setTokens,
  setUnauthorizedHandler,
} from '@/api/client'
import { ApiError } from '@/api/errors'
import { authApi } from '@/api/auth'
import { recordsApi } from '@/api/records'
import { lostRecordsApi } from '@/api/lostRecords'
import { foundRecordsApi } from '@/api/foundRecords'
import { claimsApi } from '@/api/claims'
import { adminApi } from '@/api/admin'

function responseError(
  config: InternalAxiosRequestConfig,
  status: number,
  data = { error_code: 'REQUEST_FAILED', message: 'request failed' },
) {
  return new AxiosError('request failed', undefined, config, undefined, {
    config,
    data,
    headers: {},
    status,
    statusText: 'Error',
  })
}

describe('api client', () => {
  afterEach(() => {
    clearTokens()
    setUnauthorizedHandler(() => {})
    vi.restoreAllMocks()
  })

  it('uses real API mode by default', () => {
    expect(isMockMode).toBe(false)
  })

  it('keeps tokens in memory without browser storage writes', () => {
    const localSetItem = vi.spyOn(Storage.prototype, 'setItem')
    setTokens({ access_token: 'access', refresh_token: 'refresh', token_type: 'bearer' })

    expect(getAccessToken()).toBe('access')
    expect(localSetItem).not.toHaveBeenCalled()
  })

  it('refreshes once and retries a 401 request', async () => {
    setTokens({ access_token: 'expired', refresh_token: 'refresh', token_type: 'bearer' })
    const refresh = vi.spyOn(axios, 'post').mockResolvedValue({
      data: {
        user: { id: 'u-1', username: 'user', email: 'user@example.com', role: 'USER', created_at: '2026-07-17T00:00:00Z' },
        tokens: { access_token: 'renewed', refresh_token: 'next-refresh', token_type: 'bearer' },
      },
    })
    let attempts = 0
    apiClient.defaults.adapter = async (config) => {
      attempts += 1
      if (attempts === 1) throw responseError(config, 401)
      return { config, data: { ok: true }, headers: {}, status: 200, statusText: 'OK' }
    }

    await expect(apiClient.get('/api/protected')).resolves.toMatchObject({ data: { ok: true } })
    expect(refresh).toHaveBeenCalledOnce()
    expect(attempts).toBe(2)
    expect(getAccessToken()).toBe('renewed')
  })

  it('clears memory and redirects when refresh fails', async () => {
    setTokens({ access_token: 'expired', refresh_token: 'refresh', token_type: 'bearer' })
    const redirect = vi.fn()
    setUnauthorizedHandler(redirect)
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('refresh failed'))
    apiClient.defaults.adapter = async (config) => { throw responseError(config, 401) }

    await expect(apiClient.get('/api/protected')).rejects.toBeInstanceOf(ApiError)
    expect(getAccessToken()).toBeNull()
    expect(redirect).toHaveBeenCalledOnce()
  })

  it.each([403, 409, 422, 423])('normalizes %i responses to ApiError', async (status) => {
    apiClient.defaults.adapter = async (config) => {
      throw responseError(config, status, { error_code: `ERROR_${status}`, message: `message ${status}` })
    }

    await expect(apiClient.get('/api/failing')).rejects.toMatchObject({
      name: 'ApiError',
      status,
      code: `ERROR_${status}`,
      message: `message ${status}`,
    })
  })

  it('exposes typed real domain endpoints through the single client', async () => {
    const paths: string[] = []
    apiClient.defaults.adapter = async (config) => {
      paths.push(String(config.url))
      return { config, data: [], headers: {}, status: 200, statusText: 'OK' }
    }

    await authApi.getMe()
    await recordsApi.recent()
    await lostRecordsApi.get('lost-1')
    await foundRecordsApi.get('found-1')
    await claimsApi.get('claim-1')
    await adminApi.reviews()

    expect(paths).toEqual([
      '/api/auth/me',
      '/api/records/recent',
      '/api/lost-records/lost-1',
      '/api/found-records/found-1',
      '/api/claims/claim-1',
      '/api/admin/reviews',
    ])
  })
})
