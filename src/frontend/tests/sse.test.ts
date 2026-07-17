import { describe, expect, it, vi } from 'vitest'
import { setTokens } from '@/api/client'
import { streamMatch } from '@/api/sse'

describe('streamMatch', () => {
  it('uses bearer-authenticated fetch and dispatches progress, done, and error events', async () => {
    setTokens({ access_token: 'access-token', refresh_token: 'refresh-token', token_type: 'bearer' })
    const fetchMock = vi.fn().mockResolvedValue(new Response(
      'event: progress\ndata: {"stage":"searching","progress":15}\n\n' +
      'event: done\ndata: {"stage":"done","progress":100}\n\n' +
      'event: error\ndata: {"stage":"failed","progress":100,"error_code":"MATCHING_FAILED"}\n\n',
      { status: 200, headers: { 'Content-Type': 'text/event-stream' } },
    ))
    vi.stubGlobal('fetch', fetchMock)
    const onProgress = vi.fn()
    const onDone = vi.fn()
    const onError = vi.fn()

    await streamMatch('lost-1', { onProgress, onDone, onError })

    expect(fetchMock).toHaveBeenCalledWith('/api/lost-records/lost-1/match', expect.objectContaining({
      headers: expect.objectContaining({ Authorization: 'Bearer access-token' }),
    }))
    expect(String(fetchMock.mock.calls[0][0])).not.toContain('access-token')
    expect(onProgress).toHaveBeenCalledWith({
      stage: 'searching', progress: 15, step: 'searching', label: '正在检索招领记录...',
    })
    expect(onDone).toHaveBeenCalledWith({ stage: 'done', progress: 100 })
    expect(onError).toHaveBeenCalledWith({
      stage: 'failed', progress: 100, error_code: 'MATCHING_FAILED', message: '匹配失败，请重试',
    })
  })

  it('returns without fetching when the signal is already aborted', async () => {
    const controller = new AbortController()
    controller.abort()
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    await expect(streamMatch('lost-1', { onProgress: vi.fn(), onDone: vi.fn(), onError: vi.fn() }, controller.signal)).resolves.toBeUndefined()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
