import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { FoundWizardPage } from '@/features/found-items/FoundWizardPage'

vi.mock('@/features/auth/hooks', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'u1', username: 'test', email: 'test@test.com', role: 'USER', created_at: '' },
    isLoading: false, isAuthenticated: true, isAdmin: false,
  })),
  useLogout: vi.fn(() => ({ logout: vi.fn() })),
}))

function renderWizard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><FoundWizardPage /></MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('FoundWizardPage', () => {
  it('renders page title', () => {
    renderWizard()
    expect(screen.getByText('我要招领')).toBeInTheDocument()
  })

  it('renders form fields', () => {
    renderWizard()
    expect(screen.getByPlaceholderText('物品名称')).toBeInTheDocument()
    expect(screen.getByText('物品类别（下拉选择）')).toBeInTheDocument()
  })

  it('renders upload area', () => {
    renderWizard()
    expect(screen.getByText('上传图片')).toBeInTheDocument()
  })

  it('renders submit button', () => {
    renderWizard()
    expect(screen.getByText('提交')).toBeInTheDocument()
  })

  it('renders page slogan', () => {
    renderWizard()
    expect(screen.getByText('捡到物品，帮助他人寻回温暖')).toBeInTheDocument()
  })

  it('renders category dropdown with options', () => {
    renderWizard()
    expect(screen.getByText('电子产品')).toBeInTheDocument()
    expect(screen.getByText('证件卡片')).toBeInTheDocument()
    expect(screen.getByText('服饰配饰')).toBeInTheDocument()
    expect(screen.getByText('学习用品')).toBeInTheDocument()
  })
})
