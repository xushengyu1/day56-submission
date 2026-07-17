import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AdminQueuePage } from '@/features/admin/AdminQueuePage'
import { AdminReviewPage } from '@/features/admin/AdminReviewPage'
import { AdminAuditPage } from '@/features/admin/AdminAuditPage'
import { adminApi } from '@/api/admin'
import type { ReviewDetail } from '@/api/types'

vi.mock('@/api/admin', () => ({
  adminApi: { reviews: vi.fn(), review: vi.fn(), decide: vi.fn(), audit: vi.fn() },
}))

const foundRecord = {
  id: 'found-1', owner_user_id: 'finder-1', kind: 'FOUND' as const,
  item_type: 'OTHER' as const, public_category: 'OTHER_CATEGORY' as const,
  location_area: 'LIBRARY' as const, status: 'PUBLISHED' as const,
  name_public: '黑色折叠伞', description_public: '外观完整',
  event_time_public: '2026-07-17 09:00', location_public: '图书馆',
  public_image_asset_id: null, number_masked: null, claim_id: null, version: 1,
  published_at: '2026-07-17T09:00:00Z', created_at: '2026-07-17T09:00:00Z',
  updated_at: '2026-07-17T09:00:00Z',
}

const unmatchedDetail: ReviewDetail = {
  id: 'review-2', source: 'UNMATCHED', item_type: null, status: 'OPEN',
  route_source: null, result_code: null, created_at: '2026-07-17T10:00:00Z',
  requester_user_id: 'owner-1', reason: '没有合适候选', lost_record: null,
  candidate: null, evidence: [],
  candidates: [{
    id: 'candidate-7', lost_record_id: 'lost-1', found_record_id: 'found-1',
    total_score: 91, reason_codes: ['TYPE_MATCH'], conflict_codes: [],
    found_record: foundRecord, created_at: '2026-07-17T09:00:00Z',
  }],
}

function renderRoute(path: string, routePath: string, element: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes><Route path={routePath} element={element} /><Route path="/admin" element={<div>队列首页</div>} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('admin real API console', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('crypto', { randomUUID: vi.fn(() => 'decision-key') })
    vi.mocked(adminApi.reviews).mockResolvedValue([
      { id: 'claim-1', source: 'CLAIM', item_type: 'OTHER', status: 'PENDING_ADMIN_REVIEW', route_source: 'OTHER_MODEL', result_code: 'MODEL_UNAVAILABLE', created_at: '2026-07-17T10:00:00Z' },
      { id: 'review-2', source: 'UNMATCHED', item_type: null, status: 'OPEN', route_source: null, result_code: null, created_at: '2026-07-17T11:00:00Z' },
    ])
    vi.mocked(adminApi.review).mockResolvedValue(unmatchedDetail)
    vi.mocked(adminApi.decide).mockResolvedValue({
      review_id: 'review-2', claim_id: null, candidate_id: 'candidate-7',
      status: 'RESOLVED', decision: 'RECOMMEND_CANDIDATE',
    })
    vi.mocked(adminApi.audit).mockResolvedValue([
      { event_id: 'event-1', event_type: 'ADMIN_REVIEW_DECIDED', aggregate_type: 'review_request', aggregate_id: 'review-2', result_code: 'RECOMMEND_CANDIDATE', metadata_redacted: { reason_present: true }, created_at: '2026-07-17T12:00:00Z' },
    ])
  })

  it('renders queue DTO source and status from adminApi', async () => {
    renderRoute('/admin', '/admin', <AdminQueuePage />)

    expect(await screen.findByText('未匹配复核')).toBeInTheDocument()
    expect(screen.getByText('待管理员复核')).toBeInTheDocument()
    expect(adminApi.reviews).toHaveBeenCalledTimes(1)
  })

  it('uses H candidates for an UNMATCHED recommendation decision', async () => {
    renderRoute('/admin/reviews/review-2', '/admin/reviews/:id', <AdminReviewPage />)

    expect(await screen.findByText('黑色折叠伞')).toBeInTheDocument()
    expect(screen.getByText('推荐候选')).toBeInTheDocument()
    expect(screen.getByText('驳回复核')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText(/黑色折叠伞/))
    fireEvent.change(screen.getByLabelText(/处理理由/), { target: { value: '建议核对该候选' } })
    fireEvent.click(screen.getByRole('button', { name: /提交决定/ }))

    await waitFor(() => expect(adminApi.decide).toHaveBeenCalledWith(
      'review-2',
      { decision: 'RECOMMEND_CANDIDATE', reason: '建议核对该候选', candidate_id: 'candidate-7' },
      'decision-key',
    ))
  })

  it('shows only handoff/reject actions and safe evidence for a claim review', async () => {
    vi.mocked(adminApi.review).mockResolvedValue({
      ...unmatchedDetail, id: 'claim-1', source: 'CLAIM', item_type: 'OTHER',
      candidate: unmatchedDetail.candidates[0], candidates: [],
      evidence: [{ attempt_no: 1, result_code: 'MODEL_UNAVAILABLE', answer_summary: { result: 'UNDETERMINED' }, risk_flag: null, created_at: '2026-07-17T10:00:00Z' }],
    })
    renderRoute('/admin/reviews/claim-1', '/admin/reviews/:id', <AdminReviewPage />)

    expect(await screen.findByText('进入交接')).toBeInTheDocument()
    expect(screen.getByText('驳回认领')).toBeInTheDocument()
    expect(screen.getByText(/第 1 次 · MODEL_UNAVAILABLE/)).toBeInTheDocument()
    expect(screen.queryByText(/标准答案|answer_key/i)).not.toBeInTheDocument()
  })

  it('renders the real audit DTO list', async () => {
    renderRoute('/admin/audit', '/admin/audit', <AdminAuditPage />)

    expect(await screen.findByText('ADMIN_REVIEW_DECIDED')).toBeInTheDocument()
    expect(screen.getByText('RECOMMEND_CANDIDATE')).toBeInTheDocument()
    expect(screen.getByText('review_request · review-2')).toBeInTheDocument()
    expect(adminApi.audit).toHaveBeenCalledTimes(1)
  })
})
