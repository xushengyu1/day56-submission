import { beforeEach, describe, it, expect, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LostCreatePage } from '@/features/lost-items/LostCreatePage'
import { CandidateListPage } from '@/features/candidates/CandidateListPage'
import { CandidateDetailPage } from '@/features/candidates/CandidateDetailPage'
import { MyRecordsPage } from '@/features/records/MyRecordsPage'
import { recordsApi } from '@/api/records'
import { claimsApi } from '@/api/claims'
import type { ItemRecordPublic } from '@/api/types'

vi.mock('@/features/auth/hooks', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'u1', username: 'test', email: 'test@test.com', role: 'USER', created_at: '' },
    isLoading: false, isAuthenticated: true, isAdmin: false,
  })),
  useLogout: vi.fn(() => ({ logout: vi.fn() })),
}))

vi.mock('@/api/mock', () => ({
  mockApi: {
    getCandidates: vi.fn().mockResolvedValue([
      {
        id: 'c-001', lost_record_id: 'lr-001', found_record_id: 'fr-001', match_score: 82,
        matched_points: ['物品类别一致'], conflict_points: ['楼层不一致'],
        retention_reason: '地点相邻', created_at: '',
        item_record: { id: 'fr-001', record_type: 'FOUND', publisher_id: 'u2', item_type: 'OTHER', public_item_name: '黑色折叠伞', public_time_range: '7月16日上午', public_location: '教学楼B区2楼', public_description: '黑色折叠伞', status: 'PENDING_MATCH', created_at: '', updated_at: '' },
      },
    ]),
    getCandidateDetail: vi.fn().mockResolvedValue({
      id: 'c-001', lost_record_id: 'lr-001', found_record_id: 'fr-001', match_score: 82,
      matched_points: ['物品类别一致——都是折叠伞', '时间相差约20分钟'], conflict_points: ['楼层不一致——失主填写3楼'],
      retention_reason: '地点相邻且时间接近', created_at: '',
      item_record: { id: 'fr-001', record_type: 'FOUND', publisher_id: 'u2', item_type: 'OTHER', public_item_name: '黑色折叠伞', public_time_range: '7月16日上午', public_location: '教学楼B区2楼', public_description: '黑色折叠伞', status: 'PENDING_MATCH', created_at: '', updated_at: '' },
    }),
  },
}))

vi.mock('@/api/records', () => ({
  recordsApi: { mine: vi.fn(), summary: vi.fn() },
}))

vi.mock('@/api/claims', () => ({
  claimsApi: { completeHandoff: vi.fn() },
}))

function renderWithProviders(ui: React.ReactNode, route = '/') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('LostCreatePage', () => {
  it('renders page title', () => {
    renderWithProviders(<LostCreatePage />)
    expect(screen.getByText('我要寻物')).toBeInTheDocument()
  })

  it('renders form fields', () => {
    renderWithProviders(<LostCreatePage />)
    expect(screen.getByPlaceholderText('物品名称')).toBeInTheDocument()
    expect(screen.getByText('物品类别（下拉选择）')).toBeInTheDocument()
  })

  it('renders submit button', () => {
    renderWithProviders(<LostCreatePage />)
    expect(screen.getByText('提交')).toBeInTheDocument()
  })

  it('renders upload area', () => {
    renderWithProviders(<LostCreatePage />)
    expect(screen.getByText('上传图片')).toBeInTheDocument()
  })

  it('renders page slogan', () => {
    renderWithProviders(<LostCreatePage />)
    expect(screen.getByText('丢失物品，期待温暖回归')).toBeInTheDocument()
  })

  it('renders category dropdown with options', () => {
    renderWithProviders(<LostCreatePage />)
    expect(screen.getByText('电子产品')).toBeInTheDocument()
    expect(screen.getByText('证件卡片')).toBeInTheDocument()
    expect(screen.getByText('学习用品')).toBeInTheDocument()
  })
})

describe('CandidateListPage', () => {
  it('renders candidate count', async () => {
    renderWithProviders(<CandidateListPage />, '/lost/lr-001')
    expect(await screen.findByText(/个候选/)).toBeInTheDocument()
  })

  it('renders privacy disclaimer', async () => {
    renderWithProviders(<CandidateListPage />, '/lost/lr-001')
    expect(await screen.findByText(/匹配分仅表示信息相似程度/)).toBeInTheDocument()
  })

  it('renders unmatched review entry', () => {
    renderWithProviders(<CandidateListPage />, '/lost/lr-001')
    expect(screen.getByText('提交未匹配复核')).toBeInTheDocument()
  })
})

describe('CandidateDetailPage', () => {
  it('renders match points', async () => {
    renderWithProviders(<CandidateDetailPage />, '/candidates/c-001')
    expect(await screen.findByText('匹配点')).toBeInTheDocument()
  })

  it('renders conflict points', async () => {
    renderWithProviders(<CandidateDetailPage />, '/candidates/c-001')
    expect(await screen.findByText('冲突点')).toBeInTheDocument()
  })

  it('renders claim button', async () => {
    renderWithProviders(<CandidateDetailPage />, '/candidates/c-001')
    expect(await screen.findByText('发起认领')).toBeInTheDocument()
  })

  it('renders score breakdown', async () => {
    renderWithProviders(<CandidateDetailPage />, '/candidates/c-001')
    expect(await screen.findByText('评分明细')).toBeInTheDocument()
    expect(screen.getByText('语义相似度')).toBeInTheDocument()
  })
})

const handoffRecord: ItemRecordPublic = {
  id: 'found-1',
  owner_user_id: 'u1',
  kind: 'FOUND',
  item_type: 'OTHER',
  public_category: 'OTHER_CATEGORY',
  location_area: 'DORMITORY',
  status: 'PENDING_HANDOFF',
  name_public: '黑色雨伞',
  description_public: '宿舍一楼拾得',
  event_time_public: '2026-07-17 10:00',
  location_public: '宿舍区',
  public_image_asset_id: null,
  number_masked: null,
  claim_id: 'claim-77',
  version: 1,
  published_at: '2026-07-17T10:00:00Z',
  created_at: '2026-07-17T10:00:00Z',
  updated_at: '2026-07-17T10:00:00Z',
}

describe('MyRecordsPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.clearAllMocks()
    vi.mocked(recordsApi.mine).mockResolvedValue({ items: [handoffRecord], total: 1, page: 1, page_size: 5 })
    vi.mocked(recordsApi.summary).mockResolvedValue({ lost_count: 0, found_count: 1, matched_count: 1, total_count: 1 })
    vi.mocked(claimsApi.completeHandoff).mockResolvedValue({ claim_id: 'claim-77', status: 'CLAIMED' })
  })

  it('uses server-side kind and pagination parameters', async () => {
    renderWithProviders(<MyRecordsPage />)
    expect(await screen.findByText('黑色雨伞')).toBeInTheDocument()
    expect(recordsApi.mine).toHaveBeenCalledWith(undefined, 1, 5)

    fireEvent.click(screen.getByRole('button', { name: '招领 (1)' }))
    await waitFor(() => expect(recordsApi.mine).toHaveBeenCalledWith('FOUND', 1, 5))
  })

  it('completes handoff with the backend claim ID and an idempotency key', async () => {
    vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('00000000-0000-4000-8000-000000000001')
    renderWithProviders(<MyRecordsPage />)

    fireEvent.click(await screen.findByRole('button', { name: /确认交接/ }))
    fireEvent.click(screen.getByRole('button', { name: '确认已取走' }))

    await waitFor(() => expect(claimsApi.completeHandoff).toHaveBeenCalledWith(
      'claim-77',
      '00000000-0000-4000-8000-000000000001',
    ))
  })

  it('keeps the handoff idempotency key locked while the request is pending', async () => {
    vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('00000000-0000-4000-8000-000000000002')
    vi.mocked(claimsApi.completeHandoff).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<MyRecordsPage />)

    fireEvent.click(await screen.findByRole('button', { name: /确认交接/ }))
    fireEvent.click(screen.getByRole('button', { name: '确认已取走' }))

    expect(await screen.findByRole('button', { name: '取消' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: '确认中...' }))
    expect(claimsApi.completeHandoff).toHaveBeenCalledOnce()
    expect(globalThis.crypto.randomUUID).toHaveBeenCalledOnce()
  })

  it('reuses the handoff idempotency key after an uncertain failure', async () => {
    vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('00000000-0000-4000-8000-000000000003')
    vi.mocked(claimsApi.completeHandoff).mockRejectedValueOnce(new Error('connection reset'))
    renderWithProviders(<MyRecordsPage />)

    fireEvent.click(await screen.findByRole('button', { name: /确认交接/ }))
    fireEvent.click(screen.getByRole('button', { name: '确认已取走' }))
    expect(await screen.findByText('确认交接失败，请重试')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '取消' }))
    fireEvent.click(screen.getByRole('button', { name: /确认交接/ }))
    fireEvent.click(screen.getByRole('button', { name: '确认已取走' }))

    await waitFor(() => expect(claimsApi.completeHandoff).toHaveBeenCalledTimes(2))
    expect(claimsApi.completeHandoff).toHaveBeenNthCalledWith(1, 'claim-77', '00000000-0000-4000-8000-000000000003')
    expect(claimsApi.completeHandoff).toHaveBeenNthCalledWith(2, 'claim-77', '00000000-0000-4000-8000-000000000003')
    expect(globalThis.crypto.randomUUID).toHaveBeenCalledOnce()
  })
})
