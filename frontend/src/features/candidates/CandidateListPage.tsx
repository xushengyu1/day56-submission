import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { mockApi } from '@/api/mock'
import { simulateMatchSSE } from '@/api/sse'
import type { MatchProgressEvent } from '@/api/sse'
import { useState, useEffect, useCallback, useRef } from 'react'

function ScoreBadge({ score }: { score: number }) {
  const level = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low'
  const config = {
    high: { bg: 'rgba(107,158,122,0.1)', text: '#4a7a5a', border: 'rgba(107,158,122,0.2)', label: '高' },
    medium: { bg: 'rgba(107,139,164,0.1)', text: '#4a6b82', border: 'rgba(107,139,164,0.2)', label: '中' },
    low: { bg: 'rgba(148,163,184,0.1)', text: '#7a8e9e', border: 'rgba(148,163,184,0.2)', label: '低' },
  }
  const c = config[level]
  return (
    <div className="flex items-center gap-1.5 px-2 py-1 rounded-md"
      style={{ background: c.bg, border: `1px solid ${c.border}` }}
    >
      <span className="text-sm font-bold" style={{ color: c.text }}>{score}</span>
      <span className="text-[10px] font-medium" style={{ color: c.text }}>{c.label}</span>
    </div>
  )
}

// SSE 推送的步骤 → 图标映射
const STEP_ICONS: Record<string, string> = {
  searching: 'fa-search',
  filtering: 'fa-filter',
  embedding: 'fa-brain',
  matching: 'fa-robot',
  scoring: 'fa-sliders',
  finalizing: 'fa-check-circle',
}

// 全量步骤定义（用于步骤指示器）
const ALL_STEPS = [
  { step: 'searching', label: '检索招领记录' },
  { step: 'filtering', label: '筛选同类型记录' },
  { step: 'embedding', label: '生成文本向量' },
  { step: 'matching', label: '语义匹配计算' },
  { step: 'scoring', label: '综合评分排序' },
]

function AIMatchingProgress({ onComplete }: { onComplete: () => void }) {
  const [currentStep, setCurrentStep] = useState('')
  const [currentLabel, setCurrentLabel] = useState('准备中...')
  const [progress, setProgress] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<string[]>([])
  const sseRef = useRef<ReturnType<typeof simulateMatchSSE> | null>(null)

  const handleProgress = useCallback((event: MatchProgressEvent) => {
    setCurrentStep(event.step)
    setCurrentLabel(event.label)
    setProgress(event.progress)
    // 记录已完成的步骤
    setCompletedSteps((prev) => {
      const idx = ALL_STEPS.findIndex((s) => s.step === event.step)
      const completed = ALL_STEPS.slice(0, idx).map((s) => s.step)
      return [...new Set([...prev, ...completed])]
    })
  }, [])

  const handleDone = useCallback(() => {
    setProgress(100)
    setCurrentLabel('匹配完成！')
    setCompletedSteps(ALL_STEPS.map((s) => s.step))
    setTimeout(onComplete, 600)
  }, [onComplete])

  const handleError = useCallback(() => {
    setCurrentLabel('匹配出错，请重试')
    setTimeout(onComplete, 1500)
  }, [onComplete])

  useEffect(() => {
    // Mock 模式：使用 simulateMatchSSE
    // 真实后端：替换为 connectMatchSSE(lostId, { onProgress, onDone, onError })
    sseRef.current = simulateMatchSSE({
      onProgress: handleProgress,
      onDone: handleDone,
      onError: handleError,
    })

    return () => { sseRef.current?.cancel() }
  }, [handleProgress, handleDone, handleError])

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: '60px 40px', gap: '28px'
    }}>
      {/* AI 图标动画 */}
      <div style={{
        width: '72px', height: '72px', borderRadius: '20px',
        background: 'linear-gradient(135deg, rgba(107,139,164,0.12) 0%, rgba(139,123,176,0.12) 100%)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        animation: 'pulse 2s ease-in-out infinite',
      }}>
        <i className="fas fa-robot" style={{ fontSize: '28px', color: 'var(--primary-deep)' }}></i>
      </div>

      {/* 标题 */}
      <div style={{ textAlign: 'center' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text)', marginBottom: '6px' }}>AI 智能匹配中</h3>
        <p style={{ fontSize: '13px', color: 'var(--muted)' }}>正在为你寻找最匹配的招领信息</p>
      </div>

      {/* 总进度条 */}
      <div style={{ width: '100%', maxWidth: '360px' }}>
        <div style={{
          width: '100%', height: '8px', borderRadius: '4px',
          background: 'rgba(107,139,164,0.1)', overflow: 'hidden'
        }}>
          <div style={{
            width: `${progress}%`, height: '100%', borderRadius: '4px',
            background: 'linear-gradient(90deg, var(--primary) 0%, var(--purple) 100%)',
            transition: 'width 0.3s ease'
          }} />
        </div>
        <div style={{
          display: 'flex', justifyContent: 'space-between', marginTop: '8px',
          fontSize: '11px', color: 'var(--muted)'
        }}>
          <span>{currentLabel}</span>
          <span>{Math.round(progress)}%</span>
        </div>
      </div>

      {/* 步骤指示器 — 驱动自 SSE 推送的 step */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center' }}>
        {ALL_STEPS.map((step) => {
          const isDone = completedSteps.includes(step.step)
          const isCurrent = currentStep === step.step
          return (
            <div key={step.step} style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '6px 12px', borderRadius: '999px', fontSize: '12px',
              background: isDone ? 'rgba(107,158,122,0.1)' : isCurrent ? 'rgba(107,139,164,0.1)' : 'rgba(148,163,184,0.06)',
              color: isDone ? '#4a7a5a' : isCurrent ? 'var(--primary-deep)' : 'var(--muted)',
              fontWeight: isCurrent ? 700 : 500,
              transition: 'all 0.3s ease'
            }}>
              {isDone ? (
                <i className="fas fa-check text-[10px]"></i>
              ) : isCurrent ? (
                <i className="fas fa-spinner fa-spin text-[10px]"></i>
              ) : (
                <i className={`fas ${STEP_ICONS[step.step] || 'fa-circle'} text-[10px]`}></i>
              )}
              {step.label}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function CandidateListPage() {
  const { id: lostId } = useParams<{ id: string }>()
  const [isMatching, setIsMatching] = useState(true)

  const { data: candidates = [], isLoading } = useQuery({
    queryKey: ['candidates', lostId],
    queryFn: () => mockApi.getCandidates(lostId || ''),
  })

  return (
    <div className="h-full flex overflow-hidden" style={{ background: 'var(--color-neutral-50)' }}>
      {/* 左侧信息面板 — 紧凑 */}
      <div className="w-[260px] flex-shrink-0 border-r overflow-y-auto p-4"
        style={{ background: 'white', borderColor: 'var(--color-neutral-200)' }}
      >
        <Link to={`/lost/${lostId}`} style={{
          display: 'inline-flex', alignItems: 'center', gap: '4px',
          fontSize: '12px', color: 'var(--muted)', marginBottom: '12px', textDecoration: 'none',
        }}>
          <i className="fas fa-arrow-left text-[10px]"></i> 返回详情
        </Link>
        <p className="section-title mb-3">我的失物</p>
        <div className="w-full h-32 rounded-lg overflow-hidden mb-3"
          style={{ background: 'var(--color-neutral-100)' }}
        >
          <img src="https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=260&h=128&fit=crop"
            alt="黑色折叠伞" className="w-full h-full object-cover"
          />
        </div>
        <h3 className="text-base font-bold" style={{ color: 'var(--color-neutral-900)' }}>黑色折叠伞</h3>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-neutral-500)' }}>其他物品</p>

        <div className="mt-3 space-y-2">
          {[
            { icon: 'fa-clock', text: '7月16日 上午' },
            { icon: 'fa-location-dot', text: '教学楼' },
            { icon: 'fa-palette', text: '黑色' },
          ].map((item) => (
            <div key={item.icon} className="flex items-center gap-2">
              <i className={`fas ${item.icon} w-4 text-center text-[11px]`}
                style={{ color: 'var(--color-neutral-400)' }}
              ></i>
              <span className="text-xs" style={{ color: 'var(--color-neutral-600)' }}>{item.text}</span>
            </div>
          ))}
        </div>

        <div className="mt-3 p-2.5 rounded-md" style={{ background: 'var(--color-neutral-50)' }}>
          <p className="text-[10px] font-medium mb-0.5" style={{ color: 'var(--color-neutral-400)' }}>公开描述</p>
          <p className="text-xs" style={{ color: 'var(--color-neutral-700)' }}>黑色短柄折叠伞，普通款，无明显品牌标识</p>
        </div>
      </div>

      {/* 右侧候选列表 */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-5">
          {/* 标题行 */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold" style={{ color: 'var(--color-neutral-900)', letterSpacing: '-0.02em' }}>
                {candidates.length} 个候选
              </h2>
              <p className="text-xs" style={{ color: 'var(--color-neutral-500)' }}>按匹配度排列 · 匹配分仅供参考</p>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={() => setIsMatching(true)} style={{
                padding: '8px 16px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                background: 'rgba(255,255,255,0.88)', color: 'var(--primary-deep)', fontWeight: 600, fontSize: '12px',
                border: '1px solid rgba(107,139,164,0.15)', display: 'inline-flex', alignItems: 'center', gap: '6px',
              }}>
                <i className="fas fa-rotate text-[10px]"></i> 重新匹配
              </button>
              <Link to={`/lost/${lostId}/unmatched-review`} style={{
                padding: '8px 16px', borderRadius: '10px', border: 'none', textDecoration: 'none',
                background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-deep) 100%)',
                color: '#fff', fontWeight: 600, fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px',
                boxShadow: '0 4px 12px rgba(107,139,164,0.15)',
              }}>
                <i className="fas fa-flag text-[10px]"></i> 提交未匹配复核
              </Link>
            </div>
          </div>

          {/* 信息提示 */}
          <div className="callout callout-info mb-4 text-xs">
            <i className="fas fa-circle-info text-[11px] mt-0.5"></i>
            <span>匹配分仅表示信息相似程度，不代表物品归属。认领需通过身份核验。</span>
          </div>

          {/* 候选卡片列表 */}
          {isLoading || isMatching ? (
            <AIMatchingProgress onComplete={() => setIsMatching(false)} />
          ) : (
            <div className="space-y-3">
              {candidates.map((candidate, index) => (
                <Link
                  key={candidate.id}
                  to={`/candidates/${candidate.id}`}
                  className="card card-hover block p-4 transition-all"
                >
                  <div className="flex gap-4">
                    {/* 缩略图 */}
                    <div className="w-20 h-20 rounded-lg overflow-hidden flex-shrink-0"
                      style={{ background: 'var(--color-neutral-100)' }}
                    >
                      <img src="https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=80&h=80&fit=crop"
                        alt="物品" className="w-full h-full object-cover"
                      />
                    </div>

                    {/* 信息 */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                              style={{ background: 'var(--color-neutral-100)', color: 'var(--color-neutral-500)' }}
                            >
                              #{index + 1}
                            </span>
                            <h3 className="text-sm font-bold truncate" style={{ color: 'var(--color-neutral-900)' }}>
                              {candidate.found_record.name_public}
                            </h3>
                          </div>
                          <p className="text-xs mt-0.5" style={{ color: 'var(--color-neutral-500)' }}>
                            {candidate.found_record.location_public} · {candidate.found_record.event_time_public}
                          </p>
                        </div>
                        <ScoreBadge score={candidate.total_score} />
                      </div>

                      {/* 匹配点 & 冲突点 — 紧凑 tag */}
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {candidate.reason_texts.slice(0, 2).map((point, i) => (
                          <span key={i} className="badge badge-success">
                            <i className="fas fa-check text-[8px]"></i>
                            {point.split('——')[0]}
                          </span>
                        ))}
                        {candidate.conflict_texts.slice(0, 1).map((point, i) => (
                          <span key={i} className="badge badge-warning">
                            <i className="fas fa-exclamation text-[8px]"></i>
                            {point.split('——')[0]}
                          </span>
                        ))}
                      </div>

                      <p className="text-[11px] mt-2 truncate" style={{ color: 'var(--color-neutral-400)' }}>
                        {candidate.retention_reason}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}

          {/* 底部提示 */}
          <div className="mt-5 card p-4 flex items-center gap-2">
            <i className="fas fa-circle-question text-sm" style={{ color: 'var(--color-neutral-400)' }}></i>
            <span className="text-sm" style={{ color: 'var(--color-neutral-600)' }}>没有找到合适的候选？可点击上方「提交未匹配复核」由管理员协助查找。</span>
          </div>
        </div>
      </div>
    </div>
  )
}
