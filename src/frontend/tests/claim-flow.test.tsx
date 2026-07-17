import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { IdentityClaimForm } from '@/features/claims/IdentityClaimForm'
import { OtherClaimForm } from '@/features/claims/OtherClaimForm'
import { ClaimProgressPage } from '@/features/claims/ClaimProgressPage'
import { candidatesApi } from '@/api/candidates'
import { claimsApi } from '@/api/claims'
import type { CandidatePublic } from '@/api/types'

vi.mock('@/api/candidates', () => ({ candidatesApi: { get: vi.fn() } }))
vi.mock('@/api/claims', () => ({
  claimsApi: { get: vi.fn(), questions: vi.fn(), verifyIdentity: vi.fn(), verifyAnswers: vi.fn(), contact: vi.fn(), createReview: vi.fn() },
}))
vi.mock('@/hooks/useAssetObjectUrl', () => ({
  useAssetObjectUrl: vi.fn(() => ({ url: null, isLoading: false, error: null })),
}))

const candidate: CandidatePublic = {
  id: 'candidate-real', lost_record_id: 'lost-1', found_record_id: 'found-1',
  total_score: 90, level: 'HIGH', reason_codes: [], conflict_codes: [],
  created_at: '2026-07-17T09:00:00Z',
  found_record: {
    id: 'found-1', owner_user_id: 'finder-1', kind: 'FOUND', item_type: 'OTHER',
    public_category: 'OTHER_CATEGORY', location_area: 'LIBRARY', status: 'PUBLISHED',
    name_public: '黑色折叠伞', description_public: '外观完整',
    event_time_public: '2026-07-17 09:00', location_public: '图书馆',
    public_image_asset_id: null, number_masked: null, claim_id: null, version: 1,
    published_at: '2026-07-17T09:00:00Z', created_at: '2026-07-17T09:00:00Z',
    updated_at: '2026-07-17T09:00:00Z',
  },
}

function renderRoute(path: string, routePath: string, element: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path={routePath} element={element} />
          <Route path="/claims/:id/progress" element={<div>真实进度页</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('real claim flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(candidatesApi.get).mockResolvedValue(candidate)
    vi.mocked(claimsApi.questions).mockResolvedValue([
      { id: 'q-real-1', question_text: '问题一', dimension: 'one' },
      { id: 'q-real-2', question_text: '问题二', dimension: 'two' },
    ])
  })

  it('navigates identity success with the API claim ID', async () => {
    vi.mocked(candidatesApi.get).mockResolvedValue({
      ...candidate,
      found_record: { ...candidate.found_record, item_type: 'IDENTITY_DOCUMENT', public_category: 'IDENTITY_CARD', number_masked: '310***********5678' },
    })
    vi.mocked(claimsApi.verifyIdentity).mockResolvedValue({
      claim_id: 'claim-from-api', status: 'PENDING_HANDOFF', result_code: 'IDENTITY_VERIFIED',
      attempt_no: 1, attempts_remaining: 1,
    })
    renderRoute('/claims/identity/candidate-real', '/claims/identity/:candidateId', <IdentityClaimForm />)

    fireEvent.change(await screen.findByPlaceholderText('请输入 18 位身份证号码'), { target: { value: '110101199901011234' } })
    fireEvent.click(screen.getByRole('button', { name: /提交验证/ }))

    expect(await screen.findByText('真实进度页')).toBeInTheDocument()
    expect(claimsApi.verifyIdentity).toHaveBeenCalledWith('candidate-real', '110101199901011234')
  })

  it('submits every backend OTHER question by ID and navigates with claim ID', async () => {
    vi.mocked(claimsApi.verifyAnswers).mockResolvedValue({
      claim_id: 'other-claim-api', status: 'PENDING_ADMIN_REVIEW', result_code: 'MODEL_UNAVAILABLE',
      attempt_no: 1, attempts_remaining: 0,
    })
    renderRoute('/claims/other/candidate-real', '/claims/other/:candidateId', <OtherClaimForm />)

    const answers = await screen.findAllByPlaceholderText('请详细描述您记忆中的情况...')
    fireEvent.change(answers[0], { target: { value: '回答一' } })
    fireEvent.change(answers[1], { target: { value: '回答二' } })
    fireEvent.click(screen.getByRole('button', { name: /提交核验/ }))

    await waitFor(() => expect(claimsApi.verifyAnswers).toHaveBeenCalledWith('candidate-real', [
      { question_id: 'q-real-1', answer: '回答一' },
      { question_id: 'q-real-2', answer: '回答二' },
    ]))
    expect(await screen.findByText('真实进度页')).toBeInTheDocument()
  })

  it('loads progress by route claim ID and reveals contact only after handoff approval', async () => {
    vi.mocked(claimsApi.get).mockResolvedValue({
      id: 'claim-real', candidate_id: 'candidate-real', requester_user_id: 'owner-1',
      item_type: 'OTHER', status: 'PENDING_HANDOFF', route_source: 'OTHER_MODEL',
      result_code: 'ANSWERS_VERIFIED', attempt_count: 1, attempts_remaining: 0,
      created_at: '2026-07-17T10:00:00Z', updated_at: '2026-07-17T10:00:00Z', timeline: [],
    })
    vi.mocked(claimsApi.contact).mockResolvedValue({ email: 'finder@example.test' })
    renderRoute('/claims/claim-real/progress', '/claims/:id/progress', <ClaimProgressPage />)

    expect(await screen.findByText('待交接')).toBeInTheDocument()
    expect(await screen.findByText('finder@example.test')).toBeInTheDocument()
    expect(claimsApi.get).toHaveBeenCalledWith('claim-real')
    expect(claimsApi.contact).toHaveBeenCalledWith('claim-real')
    expect(candidatesApi.get).toHaveBeenCalledWith('candidate-real')
    expect(screen.getByText('黑色折叠伞')).toBeInTheDocument()
  })

  it('submits a real review request after the identity attempt is locked', async () => {
    vi.mocked(candidatesApi.get).mockResolvedValue({
      ...candidate,
      found_record: { ...candidate.found_record, item_type: 'IDENTITY_DOCUMENT', public_category: 'IDENTITY_CARD', number_masked: '310***********5678' },
    })
    vi.mocked(claimsApi.verifyIdentity).mockResolvedValue({
      claim_id: 'locked-claim', status: 'LOCKED', result_code: 'ATTEMPT_LOCKED',
      attempt_no: 2, attempts_remaining: 0,
    })
    vi.mocked(claimsApi.createReview).mockResolvedValue({ id: 'review-real', status: 'OPEN' })
    renderRoute('/claims/identity/candidate-real', '/claims/identity/:candidateId', <IdentityClaimForm />)

    fireEvent.change(await screen.findByPlaceholderText('请输入 18 位身份证号码'), { target: { value: '110101199901011234' } })
    fireEvent.click(screen.getByRole('button', { name: /提交验证/ }))
    fireEvent.change(await screen.findByPlaceholderText('请说明需要人工复核的原因'), { target: { value: '证件信息需要人工确认' } })
    fireEvent.click(screen.getByRole('button', { name: '申请人工复核' }))

    await waitFor(() => expect(claimsApi.createReview).toHaveBeenCalledWith('locked-claim', '证件信息需要人工确认'))
    expect(await screen.findByText('真实进度页')).toBeInTheDocument()
  })
})
