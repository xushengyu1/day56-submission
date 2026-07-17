import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { RequireAuth, RequireAdmin } from '@/features/auth/guards'

const authMutations = vi.hoisted(() => ({ register: vi.fn() }))

// Mock the auth hooks
vi.mock('@/features/auth/hooks', () => ({
  useAuth: vi.fn(),
  useLogin: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false })),
  useRegister: vi.fn(() => ({ mutate: authMutations.register, isPending: false, isError: false })),
  useLogout: vi.fn(() => ({ logout: vi.fn() })),
}))

import { useAuth } from '@/features/auth/hooks'
const mockUseAuth = vi.mocked(useAuth)

function renderWithRouter(ui: React.ReactNode, route = '/') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<RequireAuth>{ui}</RequireAuth>} />
          <Route path="/admin" element={<RequireAdmin><div>Admin Page</div></RequireAdmin>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Auth Routing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login page', () => {
    mockUseAuth.mockReturnValue({ user: undefined, isLoading: false, isAuthenticated: false, isAdmin: false })
    renderWithRouter(<div>Login</div>, '/login')
    expect(screen.getByText('登录账号')).toBeInTheDocument()
  })

  it('renders register page', () => {
    mockUseAuth.mockReturnValue({ user: undefined, isLoading: false, isAuthenticated: false, isAdmin: false })
    renderWithRouter(<div>Register</div>, '/register')
    expect(screen.getByText('创建账号')).toBeInTheDocument()
  })

  it('submits only the backend registration contract and requires eight password characters', () => {
    mockUseAuth.mockReturnValue({ user: undefined, isLoading: false, isAuthenticated: false, isAdmin: false })
    renderWithRouter(<div>Register</div>, '/register')

    expect(screen.queryByLabelText('手机号')).not.toBeInTheDocument()
    fireEvent.change(screen.getByPlaceholderText('请输入用户名'), { target: { value: 'zhangsan' } })
    fireEvent.change(screen.getByPlaceholderText('请输入邮箱'), { target: { value: 'user@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('请设置密码（至少8位）'), { target: { value: 'password-123' } })
    fireEvent.change(screen.getByPlaceholderText('请再次输入密码'), { target: { value: 'password-123' } })
    fireEvent.click(screen.getByRole('button', { name: '注册' }))

    expect(authMutations.register).toHaveBeenCalledWith({
      username: 'zhangsan',
      email: 'user@example.com',
      password: 'password-123',
    })
  })

  it('shows loading state while checking auth', () => {
    mockUseAuth.mockReturnValue({ user: undefined, isLoading: true, isAuthenticated: false, isAdmin: false })
    renderWithRouter(<div>Protected</div>, '/')
    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('redirects to login when not authenticated', async () => {
    mockUseAuth.mockReturnValue({ user: undefined, isLoading: false, isAuthenticated: false, isAdmin: false })
    renderWithRouter(<div>Protected Content</div>, '/')
    await waitFor(() => {
      expect(screen.getByText('登录账号')).toBeInTheDocument()
    })
  })

  it('shows 403 for non-admin accessing admin route', async () => {
    mockUseAuth.mockReturnValue({
      user: { id: 'u1', username: 'test', email: 'test@test.com', role: 'USER', created_at: '' },
      isLoading: false,
      isAuthenticated: true,
      isAdmin: false,
    })
    renderWithRouter(<div>Admin Page</div>, '/admin')
    await waitFor(() => {
      expect(screen.getByText('无权访问')).toBeInTheDocument()
    })
  })
})
