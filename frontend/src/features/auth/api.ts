import { apiClient, setTokens, clearTokens } from '@/api/client'
import { mockApi } from '@/api/mock'
import type { LoginRequest, RegisterRequest, User, AuthTokens } from '@/api/types'

const USE_MOCK = true

export async function login(req: LoginRequest): Promise<{ user: User; tokens: AuthTokens }> {
  if (USE_MOCK) {
    const result = await mockApi.login(req.email, req.password)
    setTokens(result.tokens)
    return result
  }
  const { data } = await apiClient.post('/api/auth/login', req)
  setTokens(data)
  return data
}

export async function register(req: RegisterRequest): Promise<{ user: User; tokens: AuthTokens }> {
  if (USE_MOCK) {
    const result = await mockApi.register({ username: req.username, email: req.email })
    setTokens(result.tokens)
    return result
  }
  const { data } = await apiClient.post('/api/auth/register', req)
  setTokens(data)
  return data
}

export async function getMe(): Promise<User> {
  if (USE_MOCK) {
    return mockApi.getMe()
  }
  const { data } = await apiClient.get('/api/auth/me')
  return data
}

export async function logout(): Promise<void> {
  clearTokens()
}
