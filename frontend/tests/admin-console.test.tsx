import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AdminQueuePage } from '@/features/admin/AdminQueuePage'
import { AdminReviewPage } from '@/features/admin/AdminReviewPage'

vi.mock('@/features/auth/hooks', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'u-admin', username: 'admin', email: 'admin@test.com', role: 'ADMIN', created_at: '' },
    isLoading: false,
    isAuthenticated: true,
    isAdmin: true,
  })),
  useLogout: vi.fn(() => ({ logout: vi.fn() })),
}))

vi.mock('@/api/mock', () => ({
  mockApi: {
    getReviewQueue: vi.fn().mockResolvedValue([
      { id: 'rv-001', review_type: 'MULTI_CLAIM', target_id: 'fr-001', target_type: 'CLAIM', applicant_id: 'u-001', reason: '同一物品有2人认领', status: 'PENDING', created_at: '2026-07-16T15:00:00Z' },
      { id: 'rv-002', review_type: 'UNMATCHED', target_id: 'lr-003', target_type: 'LOST', applicant_id: 'u-007', reason: 'Top5无合适候选', status: 'PENDING', created_at: '2026-07-16T12:30:00Z' },
    ]),
    getReviewDetail: vi.fn().mockResolvedValue({
      id: 'rv-001', review_type: 'MULTI_CLAIM', target_id: 'fr-001', target_type: 'CLAIM', applicant_id: 'u-001', reason: '同一物品有2人认领', status: 'PENDING', created_at: '2026-07-16T15:00:00Z',
    }),
  },
}))

function renderWithProviders(ui: React.ReactNode, route = '/admin') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('AdminQueuePage', () => {
  it('renders stats cards', async () => {
    renderWithProviders(<AdminQueuePage />)
    expect(screen.getByText('待处理')).toBeInTheDocument()
    expect(screen.getByText('多人认领')).toBeInTheDocument()
    expect(screen.getByText('核验未通过')).toBeInTheDocument()
    expect(screen.getByText('未匹配复核')).toBeInTheDocument()
  })

  it('renders filter tabs', async () => {
    renderWithProviders(<AdminQueuePage />)
    expect(await screen.findByText(/全部/)).toBeInTheDocument()
  })

  it('renders review list table headers', () => {
    renderWithProviders(<AdminQueuePage />)
    expect(screen.getByText('物品信息')).toBeInTheDocument()
    expect(screen.getByText('类型')).toBeInTheDocument()
    expect(screen.getByText('申请人')).toBeInTheDocument()
    expect(screen.getByText('复核原因')).toBeInTheDocument()
  })

  it('renders review type badges', async () => {
    renderWithProviders(<AdminQueuePage />)
    expect(await screen.findByText('多人认领')).toBeInTheDocument()
    expect(screen.getByText('未匹配复核')).toBeInTheDocument()
  })
})

describe('AdminReviewPage', () => {
  it('renders review detail with applicant comparison', async () => {
    renderWithProviders(<AdminReviewPage />, '/admin/reviews/rv-001')
    expect(await screen.findByText('认领申请人')).toBeInTheDocument()
  })

  it('renders decision form', async () => {
    renderWithProviders(<AdminReviewPage />, '/admin/reviews/rv-001')
    expect(await screen.findByText('确认张同学认领')).toBeInTheDocument()
    expect(screen.getByText('驳回全部认领')).toBeInTheDocument()
    expect(screen.getByText('处理理由')).toBeInTheDocument()
  })

  it('shows standard answer section (admin only)', async () => {
    renderWithProviders(<AdminReviewPage />, '/admin/reviews/rv-001')
    expect(await screen.findByText(/拾得者隐藏特征/)).toBeInTheDocument()
  })

  it('shows AI analysis results', async () => {
    renderWithProviders(<AdminReviewPage />, '/admin/reviews/rv-001')
    expect(await screen.findByText('AI 分析结果')).toBeInTheDocument()
  })
})
