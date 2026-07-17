import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { IdentityClaimForm } from '@/features/claims/IdentityClaimForm'
import { OtherClaimForm } from '@/features/claims/OtherClaimForm'
import { candidatesApi } from '@/api/candidates'
import { claimsApi } from '@/api/claims'
import { ApiError } from '@/api/errors'
import type { CandidatePublic } from '@/api/types'

vi.mock('@/api/candidates', () => ({ candidatesApi: { get: vi.fn() } }))
vi.mock('@/api/claims', () => ({
  claimsApi: { questions: vi.fn(), verifyIdentity: vi.fn(), verifyAnswers: vi.fn() },
}))

const candidate: CandidatePublic = {
  id: 'candidate-7',
  lost_record_id: 'lost-1',
  found_record_id: 'found-1',
  total_score: 91,
  level: 'HIGH',
  reason_codes: [],
  conflict_codes: [],
  created_at: '2026-07-17T09:00:00Z',
  found_record: {
    id: 'found-1', owner_user_id: 'finder-1', kind: 'FOUND',
    item_type: 'IDENTITY_DOCUMENT', public_category: 'IDENTITY_CARD',
    location_area: 'CANTEEN', status: 'PUBLISHED', name_public: '居民身份证',
    description_public: '透明卡套', event_time_public: '2026-07-17 09:00',
    location_public: '食堂', public_image_asset_id: null,
    number_masked: '110***********1234', claim_id: null, version: 1,
    published_at: '2026-07-17T09:00:00Z', created_at: '2026-07-17T09:00:00Z',
    updated_at: '2026-07-17T09:00:00Z',
  },
}

function renderRoute(path: string, routePath: string, element: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes><Route path={routePath} element={element} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('claim error and privacy states', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(candidatesApi.get).mockResolvedValue(candidate)
    vi.mocked(claimsApi.questions).mockResolvedValue([
      { id: 'question-1', question_text: '伞套有什么标记？', dimension: 'cover' },
      { id: 'question-2', question_text: '伞柄有什么特征？', dimension: 'handle' },
    ])
  })

  it('loads the masked number from the candidate API without a full-number leak', async () => {
    renderRoute('/claims/identity/candidate-7', '/claims/identity/:candidateId', <IdentityClaimForm />)

    expect(await screen.findByText('110***********1234')).toBeInTheDocument()
    expect(candidatesApi.get).toHaveBeenCalledWith('candidate-7')
    expect(screen.queryByText(/110101\d{12}/)).not.toBeInTheDocument()
  })

  it('shows only the server remaining-attempt count after a failed identity check', async () => {
    vi.mocked(claimsApi.verifyIdentity).mockResolvedValue({
      claim_id: 'claim-9', status: 'VERIFYING', result_code: 'IDENTITY_NOT_VERIFIED',
      attempt_no: 1, attempts_remaining: 1,
    })
    renderRoute('/claims/identity/candidate-7', '/claims/identity/:candidateId', <IdentityClaimForm />)

    fireEvent.change(await screen.findByPlaceholderText('请输入 18 位身份证号码'), {
      target: { value: '110101199901011234' },
    })
    fireEvent.click(screen.getByRole('button', { name: /提交验证/ }))

    expect(await screen.findByRole('alert')).toHaveTextContent('剩余 1 次')
    expect(screen.getByRole('alert')).not.toHaveTextContent('号码')
  })

  it('renders a safe lock message for a 423 response', async () => {
    vi.mocked(claimsApi.verifyIdentity).mockRejectedValue(
      new ApiError(423, 'ATTEMPT_LOCKED', 'sensitive backend detail'),
    )
    renderRoute('/claims/identity/candidate-7', '/claims/identity/:candidateId', <IdentityClaimForm />)

    fireEvent.change(await screen.findByPlaceholderText('请输入 18 位身份证号码'), {
      target: { value: '110101199901011234' },
    })
    fireEvent.click(screen.getByRole('button', { name: /提交验证/ }))

    expect(await screen.findByRole('alert')).toHaveTextContent('安全核验已锁定')
    expect(screen.getByRole('alert')).not.toHaveTextContent('sensitive')
  })

  it('loads public OTHER questions and never renders an answer key', async () => {
    vi.mocked(candidatesApi.get).mockResolvedValue({
      ...candidate,
      found_record: { ...candidate.found_record, item_type: 'OTHER', public_category: 'OTHER_CATEGORY', number_masked: null },
    })
    renderRoute('/claims/other/candidate-7', '/claims/other/:candidateId', <OtherClaimForm />)

    expect(await screen.findByText('伞套有什么标记？')).toBeInTheDocument()
    expect(screen.getByText('伞柄有什么特征？')).toBeInTheDocument()
    await waitFor(() => expect(claimsApi.questions).toHaveBeenCalledWith('candidate-7'))
    expect(screen.queryByText(/标准答案|answer_key/i)).not.toBeInTheDocument()
  })
})
