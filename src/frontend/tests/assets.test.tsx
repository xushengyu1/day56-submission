import { renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { assetsApi } from '@/api/assets'
import { clearTokens, setTokens } from '@/api/client'
import { ApiError } from '@/api/errors'
import { useAssetObjectUrl } from '@/hooks/useAssetObjectUrl'

describe('authenticated assets', () => {
  afterEach(() => {
    clearTokens()
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('fetches asset blobs with the current bearer token', async () => {
    setTokens({ access_token: 'access-token', refresh_token: 'refresh-token', token_type: 'bearer' })
    const fetchMock = vi.fn().mockResolvedValue(new Response(new Blob(['image'])))
    vi.stubGlobal('fetch', fetchMock)

    await expect(assetsApi.getBlob('asset id')).resolves.toBeInstanceOf(Blob)
    expect(fetchMock).toHaveBeenCalledWith('/api/assets/asset%20id', expect.objectContaining({
      headers: { Authorization: 'Bearer access-token' },
    }))
  })

  it('creates and releases an object URL on unmount', async () => {
    const createObjectURL = vi.fn(() => 'blob:asset-1')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(new Blob(['image']))))

    const { result, unmount } = renderHook(() => useAssetObjectUrl('asset-1'))

    await waitFor(() => expect(result.current).toEqual({ url: 'blob:asset-1', loading: false, error: null }))
    expect(createObjectURL).toHaveBeenCalledOnce()

    unmount()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:asset-1')
  })

  it('aborts the prior request and releases its URL when the asset changes', async () => {
    const createObjectURL = vi.fn()
      .mockReturnValueOnce('blob:old')
      .mockReturnValueOnce('blob:next')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(new Blob(['old'])))
      .mockResolvedValueOnce(new Response(new Blob(['next'])))
    vi.stubGlobal('fetch', fetchMock)

    const { result, rerender, unmount } = renderHook(({ assetId }) => useAssetObjectUrl(assetId), {
      initialProps: { assetId: 'asset-1' },
    })
    const firstSignal = fetchMock.mock.calls[0][1].signal as AbortSignal

    await waitFor(() => expect(result.current.url).toBe('blob:old'))

    rerender({ assetId: 'asset-2' })
    expect(firstSignal.aborted).toBe(true)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:old')

    await waitFor(() => expect(result.current.url).toBe('blob:next'))
    unmount()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:next')
  })

  it('does not request an asset without an ID', () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useAssetObjectUrl())

    expect(fetchMock).not.toHaveBeenCalled()
    expect(result.current).toEqual({ url: null, loading: false, error: null })
  })

  it('reports a safe API error for failed asset requests', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('private response', { status: 404 })))

    const { result } = renderHook(() => useAssetObjectUrl('missing'))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.url).toBeNull()
    expect(result.current.error).toMatchObject({ status: 404, code: 'HTTP_404', message: '资源加载失败' })
    expect(result.current.error).toBeInstanceOf(ApiError)
  })
})
