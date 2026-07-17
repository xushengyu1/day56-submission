import axios from 'axios'
import type { AuthTokens } from './types'
import { ApiError, toApiError } from './errors'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

let accessToken: string | null = null
let refreshToken: string | null = null
let unauthorizedHandler = () => window.location.assign('/login')

export const isMockMode = import.meta.env.VITE_USE_MOCK === 'true'

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && refreshToken && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const { data } = await axios.post<{ tokens: AuthTokens }>(`${API_BASE}/api/auth/refresh`, {
          refresh_token: refreshToken,
        })
        setTokens(data.tokens)
        originalRequest.headers.Authorization = `Bearer ${data.tokens.access_token}`
      } catch {
        invalidateSession()
        return Promise.reject(toApiError(error))
      }
      try {
        return await apiClient(originalRequest)
      } catch (retryError) {
        if (retryError instanceof ApiError && retryError.status === 401) invalidateSession()
        return Promise.reject(retryError)
      }
    }
    return Promise.reject(toApiError(error))
  },
)

export function setTokens(tokens: AuthTokens) {
  accessToken = tokens.access_token
  refreshToken = tokens.refresh_token
}

export function clearTokens() {
  accessToken = null
  refreshToken = null
}

function invalidateSession() {
  clearTokens()
  unauthorizedHandler()
}

export function getAccessToken() {
  return accessToken
}

export function setUnauthorizedHandler(handler: () => void) {
  unauthorizedHandler = handler
}

export function apiUrl(path: string) {
  return `${API_BASE}${path}`
}

export async function authorizedFetch(path: string, init: RequestInit = {}) {
  const request = () => fetch(apiUrl(path), {
    ...init,
    headers: {
      ...init.headers,
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
  })
  let response = await request()
  if (response.status !== 401 || !refreshToken) return response

  try {
    const { data } = await axios.post<{ tokens: AuthTokens }>(`${API_BASE}/api/auth/refresh`, { refresh_token: refreshToken })
    setTokens(data.tokens)
    response = await request()
    if (response.status === 401) invalidateSession()
    return response
  } catch {
    invalidateSession()
    throw new ApiError(401, 'UNAUTHORIZED', '登录已过期，请重新登录')
  }
}
