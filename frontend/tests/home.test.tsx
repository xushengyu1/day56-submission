import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HomePage } from '@/features/home/HomePage'

vi.mock('@/features/auth/hooks', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'u1', username: 'zhangsan', email: 'test@test.com', role: 'USER', created_at: '' },
    isLoading: false, isAuthenticated: true, isAdmin: false,
  })),
  useLogout: vi.fn(() => ({ logout: vi.fn() })),
}))

vi.mock('@/api/mock', () => ({
  mockApi: {
    getMyLostItems: vi.fn().mockResolvedValue([
      { id: 'lr-001', record_type: 'LOST', publisher_id: 'u1', item_type: 'OTHER', public_item_name: '黑色折叠伞', public_time_range: '7月16日上午', public_location: '教学楼B区3楼', status: 'HAS_CANDIDATES', created_at: '', updated_at: '' },
    ]),
    getMyFoundItems: vi.fn().mockResolvedValue([
      { id: 'fr-001', record_type: 'FOUND', publisher_id: 'u1', item_type: 'OTHER', public_item_name: '黑色折叠伞', public_time_range: '7月16日上午', public_location: '教学楼B区2楼', status: 'PENDING_MATCH', created_at: '', updated_at: '' },
    ]),
  },
}))

function renderHomePage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><HomePage /></MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('HomePage', () => {
  it('renders hero section', async () => {
    renderHomePage()
    expect(await screen.findByText(/让丢失的物品/)).toBeInTheDocument()
  })

  it('renders two main action buttons', async () => {
    renderHomePage()
    expect(await screen.findByText('发布招领')).toBeInTheDocument()
    expect(screen.getByText('发布寻物')).toBeInTheDocument()
  })

  it('found entry links to /found/new', async () => {
    renderHomePage()
    const foundLink = (await screen.findByText('发布招领')).closest('a')
    expect(foundLink).toHaveAttribute('href', '/found/new')
  })

  it('lost entry links to /lost/new', async () => {
    renderHomePage()
    const lostLink = (await screen.findByText('发布寻物')).closest('a')
    expect(lostLink).toHaveAttribute('href', '/lost/new')
  })

  it('renders function cards section', async () => {
    renderHomePage()
    expect(await screen.findByText('核心功能')).toBeInTheDocument()
    expect(screen.getAllByText('我要招领').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('我要寻物').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('智能匹配').length).toBeGreaterThanOrEqual(1)
  })

  it('renders latest items section', async () => {
    renderHomePage()
    expect(await screen.findByText('最新动态')).toBeInTheDocument()
  })

  it('renders core capabilities panel', async () => {
    renderHomePage()
    expect(await screen.findByText('核心能力')).toBeInTheDocument()
    expect(screen.getByText('AI 智能识别')).toBeInTheDocument()
    expect(screen.getByText('语义匹配')).toBeInTheDocument()
    expect(screen.getByText('人工复核')).toBeInTheDocument()
  })
})
