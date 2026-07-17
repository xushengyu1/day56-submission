/**
 * SSE 客户端 — 用于 AI 匹配等需要实时进度的场景
 *
 * 真实后端接入时：
 *   const es = new EventSource(`/api/lost-records/${lostId}/match`, { withCredentials: true })
 *
 * Mock 模式下使用 simulateMatchSSE 模拟后端推送。
 */

export interface MatchProgressEvent {
  step: string
  label: string
  progress: number
}

export interface MatchDoneEvent {
  candidates: unknown[]
}

export interface MatchErrorEvent {
  error_code: string
  message: string
}

/** 连接真实后端 SSE（联调时使用） */
export function connectMatchSSE(
  lostId: string,
  handlers: {
    onProgress: (event: MatchProgressEvent) => void
    onDone: (event: MatchDoneEvent) => void
    onError: (event: MatchErrorEvent) => void
  },
): EventSource {
  const es = new EventSource(`/api/lost-records/${lostId}/match`)

  es.addEventListener('progress', (e) => {
    handlers.onProgress(JSON.parse(e.data))
  })

  es.addEventListener('done', (e) => {
    handlers.onDone(JSON.parse(e.data))
    es.close()
  })

  es.addEventListener('error', (e) => {
    // EventSource 的原生 error 事件没有 data
    // 服务端自定义 error 事件通过 message 传递
    if (e instanceof MessageEvent && e.data) {
      handlers.onError(JSON.parse(e.data))
    } else {
      handlers.onError({ error_code: 'CONNECTION_ERROR', message: '连接中断' })
    }
    es.close()
  })

  return es
}

/** Mock SSE 模拟 — 模拟后端逐阶段推送进度 */
const MOCK_STEPS: MatchProgressEvent[] = [
  { step: 'searching', label: '正在检索招领记录...', progress: 15 },
  { step: 'filtering', label: '筛选同类型已发布记录...', progress: 30 },
  { step: 'embedding', label: '生成文本向量...', progress: 50 },
  { step: 'matching', label: '语义匹配计算中...', progress: 70 },
  { step: 'scoring', label: '综合评分排序...', progress: 85 },
  { step: 'finalizing', label: '生成匹配结果...', progress: 100 },
]

export function simulateMatchSSE(
  handlers: {
    onProgress: (event: MatchProgressEvent) => void
    onDone: (event: MatchDoneEvent) => void
    onError: (event: MatchErrorEvent) => void
  },
): { cancel: () => void } {
  let cancelled = false
  let stepIndex = 0

  const nextStep = () => {
    if (cancelled) return
    if (stepIndex >= MOCK_STEPS.length) {
      // 所有步骤完成，推送 done 事件
      handlers.onDone({ candidates: [] })
      return
    }

    const step = MOCK_STEPS[stepIndex]
    handlers.onProgress(step)
    stepIndex++

    // 每步间隔 400-800ms，模拟真实延迟
    const delay = 400 + Math.random() * 400
    setTimeout(nextStep, delay)
  }

  // 首步延迟 300ms
  setTimeout(nextStep, 300)

  return {
    cancel: () => { cancelled = true },
  }
}
