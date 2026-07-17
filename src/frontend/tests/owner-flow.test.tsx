import { beforeEach, describe, it, expect, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LostCreatePage } from '@/features/lost-items/LostCreatePage'
import { CandidateListPage } from '@/features/candidates/CandidateListPage'
import { CandidateDetailPage } from '@/features/candidates/CandidateDetailPage'
import { MyRecordsPage } from '@/features/records/MyRecordsPage'
import { recordsApi } from '@/api/records'
import { claimsApi } from '@/api/claims'
import { lostRecordsApi } from '@/api/lostRecords'
import { candidatesApi } from '@/api/candidates'
import { streamMatch } from '@/api/sse'
import type { CandidatePublic, ItemRecordPublic } from '@/api/types'

vi.mock('@/features/auth/hooks', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'u1', username: 'test', email: 'test@test.com', role: 'USER', created_at: '' },
    isLoading: false, isAuthenticated: true, isAdmin: false,
  })),
  useLogout: vi.fn(() => ({ logout: vi.fn() })),
}))

vi.mock('@/api/records', () => ({
  recordsApi: { mine: vi.fn(), summary: vi.fn() },
}))

vi.mock('@/api/claims', () => ({
  claimsApi: { completeHandoff: vi.fn() },
}))

vi.mock('@/api/lostRecords', () => ({
  lostRecordsApi: { create: vi.fn(), get: vi.fn(), candidates: vi.fn() },
}))

vi.mock('@/api/candidates', () => ({ candidatesApi: { get: vi.fn() } }))

vi.mock('@/api/sse', () => ({
  streamMatch: vi.fn(async (_lostId, handlers) => handlers.onDone({ stage: 'done', progress: 100 })),
}))

vi.mock('@/hooks/useAssetObjectUrl', () => ({
  useAssetObjectUrl: (assetId?: string | null) => ({ url: assetId ? `blob:${assetId}` : null, loading: false, error: null }),
}))

function renderWithProviders(ui: React.ReactNode, route = '/', routePath?: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        {routePath ? <Routes><Route path={routePath} element={ui} /></Routes> : ui}
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const lostRecord: ItemRecordPublic = {
  id: 'lr-001', owner_user_id: 'u1', kind: 'LOST', item_type: 'OTHER', public_category: 'OTHER_CATEGORY',
  location_area: 'TEACHING_BUILDING', status: 'PUBLISHED', name_public: '黑色折叠伞',
  description_public: '教学楼 B 区 302 教室丢失', event_time_public: '2026-07-16 09:00', location_public: '教学楼',
  public_image_asset_id: 'lost-asset', number_masked: null, claim_id: null, version: 1, published_at: '2026-07-16T09:00:00Z',
  created_at: '2026-07-16T09:00:00Z', updated_at: '2026-07-16T09:00:00Z',
}

const foundRecord: ItemRecordPublic = {
  ...lostRecord, id: 'fr-001', owner_user_id: 'u2', kind: 'FOUND', name_public: '黑色折叠伞招领',
  description_public: '在教学楼 B 区 2 楼拾得', public_image_asset_id: 'found-asset',
}

const candidate: CandidatePublic = {
  id: 'c-001', lost_record_id: 'lr-001', found_record_id: 'fr-001', total_score: 79.6, level: 'MEDIUM',
  reason_codes: ['SEMANTIC_MATCH', 'TYPE_MATCH'], conflict_codes: ['LOCATION_WEAK_CONFLICT'],
  found_record: foundRecord, created_at: '2026-07-16T10:00:00Z',
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
    expect(screen.getByText('物归原主，屿过天晴')).toBeInTheDocument()
  })

  it('renders category dropdown with options', () => {
    renderWithProviders(<LostCreatePage />)
    expect(screen.getByText('电子产品')).toBeInTheDocument()
    expect(screen.getByText('证件卡片')).toBeInTheDocument()
    expect(screen.getByText('学习用品')).toBeInTheDocument()
  })
})

describe('CandidateListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(lostRecordsApi.get).mockResolvedValue(lostRecord)
    vi.mocked(lostRecordsApi.candidates).mockResolvedValue([candidate])
    vi.mocked(streamMatch).mockImplementation(async (_lostId, handlers) => handlers.onDone({ stage: 'done', progress: 100 }))
  })

  it('renders candidate count', async () => {
    renderWithProviders(<CandidateListPage />, '/lost/lr-001/candidates', '/lost/:id/candidates')
    expect(await screen.findByText('1 个候选')).toBeInTheDocument()
    expect(lostRecordsApi.get).toHaveBeenCalledWith('lr-001')
    expect(streamMatch).toHaveBeenCalledWith('lr-001', expect.any(Object), expect.any(AbortSignal))
    expect(lostRecordsApi.candidates).toHaveBeenCalledWith('lr-001')
    expect(await screen.findByText('公开描述相似')).toBeInTheDocument()
  })

  it('renders privacy disclaimer', async () => {
    renderWithProviders(<CandidateListPage />, '/lost/lr-001/candidates', '/lost/:id/candidates')
    expect(await screen.findByText(/匹配分仅表示信息相似程度/)).toBeInTheDocument()
  })

  it('renders unmatched review entry', async () => {
    renderWithProviders(<CandidateListPage />, '/lost/lr-001/candidates', '/lost/:id/candidates')
    expect(await screen.findByText('提交未匹配复核')).toBeInTheDocument()
  })

  it('aborts the authenticated match stream when leaving the page', async () => {
    let signal: AbortSignal | undefined
    vi.mocked(streamMatch).mockImplementationOnce(async (_lostId, _handlers, nextSignal) => {
      signal = nextSignal
      await new Promise<void>(() => {})
    })
    const view = renderWithProviders(<CandidateListPage />, '/lost/lr-001/candidates', '/lost/:id/candidates')

    await waitFor(() => expect(streamMatch).toHaveBeenCalled())
    expect(signal?.aborted).toBe(false)
    view.unmount()
    expect(signal?.aborted).toBe(true)
  })

  it('renders progress from the real SSE stage event', async () => {
    vi.mocked(streamMatch).mockImplementationOnce(async (_lostId, handlers) => {
      handlers.onProgress({ stage: 'embedding', step: 'embedding', label: '正在生成公开信息向量...', progress: 50 })
      await new Promise<void>(() => {})
    })

    renderWithProviders(<CandidateListPage />, '/lost/lr-001/candidates', '/lost/:id/candidates')

    expect(await screen.findByText('正在生成公开信息向量...')).toBeInTheDocument()
  })

  it('aborts the failed stream and reconnects with a new signal on retry', async () => {
    const signals: AbortSignal[] = []
    vi.mocked(streamMatch).mockImplementation(async (_lostId, handlers, signal) => {
      if (signal) signals.push(signal)
      if (signals.length === 1) {
        handlers.onError({ stage: 'failed', progress: 100, error_code: 'MATCHING_FAILED', message: '匹配失败，请重试' })
        return
      }
      await new Promise<void>(() => {})
    })
    renderWithProviders(<CandidateListPage />, '/lost/lr-001/candidates', '/lost/:id/candidates')

    expect(await screen.findByRole('alert')).toHaveTextContent('匹配失败，请重试')
    fireEvent.click(screen.getByRole('button', { name: '重新匹配' }))

    await waitFor(() => expect(streamMatch).toHaveBeenCalledTimes(2))
    expect(signals[0].aborted).toBe(true)
    expect(signals[1]).not.toBe(signals[0])
    expect(signals[1].aborted).toBe(false)
  })
})

describe('CandidateDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(candidatesApi.get).mockResolvedValue(candidate)
  })

  it('renders match points', async () => {
    renderWithProviders(<CandidateDetailPage />, '/candidates/c-001', '/candidates/:id')
    expect(await screen.findByText('匹配点')).toBeInTheDocument()
    expect(screen.getByText('公开描述相似')).toBeInTheDocument()
    expect(candidatesApi.get).toHaveBeenCalledWith('c-001')
  })

  it('renders conflict points', async () => {
    renderWithProviders(<CandidateDetailPage />, '/candidates/c-001', '/candidates/:id')
    expect(await screen.findByText('冲突点')).toBeInTheDocument()
    expect(screen.getByText('地点信息有轻微差异')).toBeInTheDocument()
  })

  it('renders claim button', async () => {
    renderWithProviders(<CandidateDetailPage />, '/candidates/c-001', '/candidates/:id')
    expect(await screen.findByText('发起认领')).toBeInTheDocument()
  })

  it('renders only the strict DTO total score and authenticated image', async () => {
    renderWithProviders(<CandidateDetailPage />, '/candidates/c-001', '/candidates/:id')
    expect(await screen.findByText('匹配总分')).toBeInTheDocument()
    expect(screen.queryByText('评分明细')).not.toBeInTheDocument()
    expect(screen.getAllByText('79.6')).toHaveLength(2)
    expect(screen.getByText('中匹配')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: '黑色折叠伞招领' })).toHaveAttribute('src', 'blob:found-asset')
  })

  it.each([
    ['IDENTITY_DOCUMENT', '/claims/identity/c-001', '身份证件认领'],
    ['OTHER', '/claims/other/c-001', '普通物品认领'],
  ] as const)('routes %s candidates to the correct claim flow', async (itemType, destination, destinationText) => {
    vi.mocked(candidatesApi.get).mockResolvedValue({ ...candidate, found_record: { ...foundRecord, item_type: itemType } })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/candidates/c-001']}>
          <Routes>
            <Route path="/candidates/:id" element={<CandidateDetailPage />} />
            <Route path={destination} element={<div>{destinationText}</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    fireEvent.click(await screen.findByRole('button', { name: '发起认领' }))
    expect(await screen.findByText(destinationText)).toBeInTheDocument()
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
