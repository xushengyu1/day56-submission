import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { RequireAuth, RequireAdmin } from '@/features/auth/guards'

// Mock the auth hooks
vi.mock('@/features/auth/hooks', () => ({
  useAuth: vi.fn(),
  useLogin: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false })),
  useRegister: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false })),
  useLogout: vi.fn(() => ({ logout: vi.fn() })),
}))

import { useAuth } from '@/features/auth/hooks'
const mockUseAuth = vi.mocked(useAuth)

function renderWithRouter(ui: React.ReactNode, route = '/') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  const router = createMemoryRouter(
    [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      {
        path: '/',
        element: <RequireAuth>{ui}</RequireAuth>,
      },
      {
        path: '/admin',
        element: <RequireAdmin><div>Admin Page</div></RequireAdmin>,
      },
    ],
    { initialEntries: [route] },
  )
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
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
