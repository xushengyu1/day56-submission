import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HomePage } from '@/features/home/HomePage'
import { recordsApi } from '@/api/records'
import type { ItemRecordPublic } from '@/api/types'

vi.mock('@/api/records', () => ({
  recordsApi: {
    recent: vi.fn(),
    summary: vi.fn(),
  },
}))

const recentItem: ItemRecordPublic = {
  id: 'lost-1',
  owner_user_id: 'user-1',
  kind: 'LOST',
  item_type: 'OTHER',
  public_category: 'ELECTRONICS',
  location_area: 'LIBRARY',
  status: 'PUBLISHED',
  name_public: '黑色耳机',
  description_public: '在图书馆二楼遗失',
  event_time_public: '2026-07-17 09:00',
  location_public: '图书馆',
  public_image_asset_id: null,
  number_masked: null,
  claim_id: null,
  version: 1,
  published_at: '2026-07-17T09:00:00Z',
  created_at: '2026-07-17T09:00:00Z',
  updated_at: '2026-07-17T09:00:00Z',
}

function renderHomePage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><HomePage /></MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('HomePage', () => {
  beforeEach(() => {
    vi.mocked(recordsApi.recent).mockResolvedValue([recentItem])
    vi.mocked(recordsApi.summary).mockResolvedValue({
      lost_count: 2,
      found_count: 3,
      matched_count: 1,
      total_count: 5,
    })
  })

  it('loads recent records and the owner summary from domain APIs', async () => {
    renderHomePage()

    expect(await screen.findByText('黑色耳机')).toBeInTheDocument()
    await waitFor(() => {
      expect(recordsApi.recent).toHaveBeenCalledWith(5)
      expect(recordsApi.summary).toHaveBeenCalledOnce()
    })
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('links the two main actions to the real creation routes', () => {
    renderHomePage()

    expect(screen.getAllByText('我要寻物')[0].closest('a')).toHaveAttribute('href', '/lost/new')
    expect(screen.getAllByText('我要招领')[0].closest('a')).toHaveAttribute('href', '/found/new')
  })

  it('does not present zeroes when the summary request fails', async () => {
    vi.mocked(recordsApi.summary).mockRejectedValue(new Error('offline'))
    renderHomePage()

    expect(await screen.findByText('统计加载失败')).toBeInTheDocument()
    expect(screen.queryByText('寻物记录')).not.toBeInTheDocument()
  })

  it('shows a loading state until summary values are available', () => {
    vi.mocked(recordsApi.summary).mockReturnValue(new Promise(() => {}))
    renderHomePage()

    expect(screen.getByText('统计加载中')).toBeInTheDocument()
    expect(screen.queryByText('寻物记录')).not.toBeInTheDocument()
  })
})
