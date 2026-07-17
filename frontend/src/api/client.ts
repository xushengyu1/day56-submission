import axios from 'axios'
import type { AuthTokens } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

let accessToken: string | null = null
let refreshToken: string | null = null

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
        const { data } = await axios.post(`${API_BASE}/api/auth/refresh`, {
          refresh_token: refreshToken,
        })
        setTokens(data)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(originalRequest)
      } catch {
        clearTokens()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
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

export function getAccessToken() {
  return accessToken
}
