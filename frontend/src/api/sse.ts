import { ApiError } from './errors'
import { authorizedFetch } from './client'

export interface MatchProgressEvent {
  stage: string
  progress: number
  step: string
  label: string
}

export interface MatchDoneEvent {
  stage: string
  progress: number
}

export interface MatchErrorEvent {
  error_code: string
  message: string
}

export async function streamMatch(
  lostId: string,
  handlers: {
    onProgress: (event: MatchProgressEvent) => void
    onDone: (event: MatchDoneEvent) => void
    onError: (event: MatchErrorEvent) => void
  },
  signal?: AbortSignal,
): Promise<void> {
  if (signal?.aborted) return
  const response = await authorizedFetch(`/api/lost-records/${lostId}/match`, { signal })
  if (!response.ok) {
    handlers.onError({ error_code: `HTTP_${response.status}`, message: '匹配进度连接失败' })
    throw new ApiError(response.status, `HTTP_${response.status}`, '匹配进度连接失败')
  }
  if (!response.body) {
    handlers.onError({ error_code: 'EMPTY_STREAM', message: '匹配进度连接失败' })
    return
  }

  const reader = response.body.getReader()
  const cancel = () => { void reader.cancel() }
  signal?.addEventListener('abort', cancel, { once: true })
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (!signal?.aborted) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const messages = buffer.split('\n\n')
      buffer = messages.pop() ?? ''
      for (const message of messages) {
        const event = message.match(/^event:\s*(.+)$/m)?.[1]
        const data = message.match(/^data:\s*(.+)$/m)?.[1]
        if (!event || !data) continue
        const payload = JSON.parse(data)
        if (event === 'progress') handlers.onProgress(payload)
        if (event === 'done') handlers.onDone(payload)
        if (event === 'error') handlers.onError(payload)
      }
    }
  } finally {
    signal?.removeEventListener('abort', cancel)
  }
}

const mockSteps: MatchProgressEvent[] = [
  { stage: 'searching', step: 'searching', label: '正在检索招领记录...', progress: 15 },
  { stage: 'filtering', step: 'filtering', label: '筛选同类型已发布记录...', progress: 30 },
  { stage: 'embedding', step: 'embedding', label: '生成文本向量...', progress: 50 },
  { stage: 'matching', step: 'matching', label: '语义匹配计算中...', progress: 70 },
  { stage: 'scoring', step: 'scoring', label: '综合评分排序...', progress: 85 },
  { stage: 'finalizing', step: 'finalizing', label: '生成匹配结果...', progress: 100 },
]

export function simulateMatchSSE(
  handlers: {
    onProgress: (event: MatchProgressEvent) => void
    onDone: (event: MatchDoneEvent) => void
    onError: (event: MatchErrorEvent) => void
  },
): { cancel: () => void } {
  let cancelled = false
  let index = 0
  const next = () => {
    if (cancelled) return
    const event = mockSteps[index++]
    if (!event) {
      handlers.onDone({ stage: 'done', progress: 100 })
      return
    }
    handlers.onProgress(event)
    setTimeout(next, 400)
  }
  setTimeout(next, 300)
  return { cancel: () => { cancelled = true } }
}
