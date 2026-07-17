import { apiClient, clearTokens, isMockMode, setTokens } from './client'
import { mockApi } from './mock'
import type { LoginRequest, LoginResponse, RegisterRequest, User } from './types'

export const authApi = {
  async login(request: LoginRequest): Promise<LoginResponse> {
    const response = isMockMode
      ? await mockApi.login(request.email, request.password)
      : (await apiClient.post<LoginResponse>('/api/auth/login', request)).data
    setTokens(response.tokens)
    return response
  },

  async register(request: RegisterRequest): Promise<LoginResponse> {
    const response = isMockMode
      ? await mockApi.register(request)
      : (await apiClient.post<LoginResponse>('/api/auth/register', request)).data
    setTokens(response.tokens)
    return response
  },

  async getMe(): Promise<User> {
    return isMockMode ? mockApi.getMe() : (await apiClient.get<User>('/api/auth/me')).data
  },

  logout() {
    clearTokens()
  },
}
