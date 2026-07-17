import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LocationItemsPage } from '@/features/home/LocationItemsPage'
import { LostItemDetailPage } from '@/features/lost-items/LostItemDetailPage'
import { FoundItemDetailPage } from '@/features/found-items/FoundItemDetailPage'
import { recordsApi } from '@/api/records'
import { lostRecordsApi } from '@/api/lostRecords'
import { foundRecordsApi } from '@/api/foundRecords'
import type { ItemRecordPublic } from '@/api/types'

vi.mock('@/features/auth/hooks', () => ({
  useAuth: () => ({ user: { id: 'owner-1' }, isLoading: false, isAuthenticated: true, isAdmin: false }),
}))

vi.mock('@/api/records', () => ({ recordsApi: { list: vi.fn() } }))
vi.mock('@/api/lostRecords', () => ({ lostRecordsApi: { get: vi.fn() } }))
vi.mock('@/api/foundRecords', () => ({ foundRecordsApi: { get: vi.fn() } }))
vi.mock('@/hooks/useAssetObjectUrl', () => ({
  useAssetObjectUrl: (assetId?: string | null) => ({
    url: assetId ? `blob:${assetId}` : null,
    loading: false,
    error: null,
  }),
}))

const baseRecord: ItemRecordPublic = {
  id: 'record-1',
  owner_user_id: 'owner-1',
  kind: 'LOST',
  item_type: 'OTHER',
  public_category: 'ELECTRONICS',
  location_area: 'TEACHING_BUILDING',
  status: 'PUBLISHED',
  name_public: '黑色耳机',
  description_public: '教学楼 B 区 302 教室遗失',
  event_time_public: '2026-07-17 09:00',
  location_public: '教学楼',
  public_image_asset_id: 'asset-1',
  number_masked: null,
  claim_id: null,
  version: 1,
  published_at: '2026-07-17T09:00:00Z',
  created_at: '2026-07-17T09:00:00Z',
  updated_at: '2026-07-17T09:00:00Z',
}

function renderRoute(path: string, routePath: string, element: React.ReactNode) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <Routes><Route path={routePath} element={element} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('record browsing pages', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(recordsApi.list).mockResolvedValue({ items: [baseRecord], total: 1, page: 1, page_size: 5 })
    vi.mocked(lostRecordsApi.get).mockResolvedValue(baseRecord)
    vi.mocked(foundRecordsApi.get).mockResolvedValue({
      ...baseRecord,
      id: 'found-7',
      kind: 'FOUND',
      item_type: 'IDENTITY_DOCUMENT',
      public_category: 'IDENTITY_CARD',
      name_public: '校园卡',
      number_masked: '3101********1234',
    })
  })

  it('maps a Chinese location route to the backend enum and API pagination', async () => {
    renderRoute('/location/教学楼', '/location/:location', <LocationItemsPage />)

    expect(await screen.findByText('黑色耳机')).toBeInTheDocument()
    expect(recordsApi.list).toHaveBeenCalledWith('TEACHING_BUILDING', 1, 5)
  })

  it('renders not-found for an invalid location without issuing an unfiltered request', () => {
    renderRoute('/location/未知区域', '/location/:location', <LocationItemsPage />)

    expect(screen.getByText('地点不存在')).toBeInTheDocument()
    expect(recordsApi.list).not.toHaveBeenCalled()
  })

  it('loads a lost record by route ID and renders its authenticated object URL', async () => {
    renderRoute('/lost/lost-42', '/lost/:id', <LostItemDetailPage />)

    expect(await screen.findByText('教学楼 B 区 302 教室遗失')).toBeInTheDocument()
    expect(lostRecordsApi.get).toHaveBeenCalledWith('lost-42')
    expect(screen.getByRole('img', { name: '黑色耳机' })).toHaveAttribute('src', 'blob:asset-1')
    expect(screen.getByText('电子产品')).toBeInTheDocument()
  })

  it('loads a found record by route ID and renders the backend masked number', async () => {
    renderRoute('/found/found-7', '/found/:id', <FoundItemDetailPage />)

    expect(await screen.findByText('3101********1234')).toBeInTheDocument()
    await waitFor(() => expect(foundRecordsApi.get).toHaveBeenCalledWith('found-7'))
    expect(screen.getByText('证件卡片')).toBeInTheDocument()
  })
})
