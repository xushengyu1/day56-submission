import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { locationAreaLabel, publicCategoryLabel } from '@/api/catalog'
import { lostRecordsApi } from '@/api/lostRecords'
import { streamMatch, type MatchProgressEvent } from '@/api/sse'
import type { CandidatePublic } from '@/api/types'
import { useAssetObjectUrl } from '@/hooks/useAssetObjectUrl'
import { conflictCodeLabel, formatCandidateScore, reasonCodeLabel } from './display'

const STEPS = [
  { stage: 'searching', label: '检索招领记录' },
  { stage: 'filtering', label: '筛选同类记录' },
  { stage: 'embedding', label: '生成公开信息向量' },
  { stage: 'matching', label: '计算语义匹配' },
  { stage: 'scoring', label: '整理候选结果' },
  { stage: 'finalizing', label: '完成匹配' },
]

function ScoreBadge({ score, level }: { score: number; level: string }) {
  const label = level === 'HIGH' ? '高' : level === 'MEDIUM' ? '中' : '低'
  return <div className="badge badge-success"><strong>{formatCandidateScore(score)}</strong> {label}</div>
}

function MatchingProgress({ lostId, attempt, onComplete }: {
  lostId: string
  attempt: number
  onComplete: () => void
}) {
  const [event, setEvent] = useState<MatchProgressEvent | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setEvent(null)
    setError(null)
    void streamMatch(lostId, {
      onProgress: setEvent,
      onDone: onComplete,
      onError: (nextError) => setError(nextError.message),
    }, controller.signal).catch((streamError: unknown) => {
      if (!controller.signal.aborted) {
        setError(streamError instanceof Error ? streamError.message : '匹配失败，请重试')
      }
    })
    return () => controller.abort()
  }, [attempt, lostId, onComplete])

  if (error) {
    return (
      <div className="card p-8 text-center" role="alert">
        <p className="mb-4" style={{ color: '#a44' }}>{error}</p>
        <p className="text-xs" style={{ color: 'var(--muted)' }}>可以重新发起匹配</p>
      </div>
    )
  }

  const currentIndex = STEPS.findIndex((step) => step.stage === event?.stage)
  return (
    <div className="card p-8 text-center" aria-label="AI 智能匹配中">
      <h3 className="text-lg font-bold mb-2">AI 智能匹配中</h3>
      <p className="text-sm mb-5" style={{ color: 'var(--muted)' }}>{event?.label ?? '准备中...'}</p>
      <div className="h-2 rounded overflow-hidden mb-5" style={{ background: 'var(--color-neutral-100)' }}>
        <div className="h-full" style={{ width: `${event?.progress ?? 0}%`, background: 'var(--primary)', transition: 'width .2s' }} />
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {STEPS.map((step, index) => (
          <span key={step.stage} className="badge" style={{ opacity: index <= currentIndex ? 1 : 0.45 }}>
            {index < currentIndex ? '✓ ' : ''}{step.label}
          </span>
        ))}
      </div>
    </div>
  )
}

function CandidateCard({ candidate, rank }: { candidate: CandidatePublic; rank: number }) {
  const image = useAssetObjectUrl(candidate.found_record.public_image_asset_id)
  return (
    <Link to={`/candidates/${candidate.id}`} className="card card-hover block p-4">
      <div className="flex gap-4">
        <div className="w-20 h-20 rounded-lg overflow-hidden flex-shrink-0" style={{ background: 'var(--color-neutral-100)' }}>
          {image.url ? <img src={image.url} alt={candidate.found_record.name_public ?? '候选物品'} className="w-full h-full object-cover" /> : <span className="h-full flex items-center justify-center text-[10px] text-center" style={{ color: 'var(--muted)' }}>{image.loading ? '图片加载中' : image.error ? '图片加载失败' : '暂无图片'}</span>}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2"><span className="badge">#{rank}</span><h3 className="text-sm font-bold truncate">{candidate.found_record.name_public ?? '未命名物品'}</h3></div>
              <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>{candidate.found_record.location_public ?? locationAreaLabel(candidate.found_record.location_area)} · {candidate.found_record.event_time_public ?? '时间未填写'}</p>
            </div>
            <ScoreBadge score={candidate.total_score} level={candidate.level} />
          </div>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {candidate.reason_codes.map((code) => <span key={`reason-${code}`} className="badge badge-success">{reasonCodeLabel(code)}</span>)}
            {candidate.conflict_codes.map((code) => <span key={`conflict-${code}`} className="badge badge-warning">{conflictCodeLabel(code)}</span>)}
          </div>
        </div>
      </div>
    </Link>
  )
}

export function CandidateListPage() {
  const { id: lostId = '' } = useParams<{ id: string }>()
  const [matching, setMatching] = useState(true)
  const [attempt, setAttempt] = useState(0)
  const lostQuery = useQuery({
    queryKey: ['records', 'lost', lostId],
    queryFn: () => lostRecordsApi.get(lostId),
    enabled: Boolean(lostId),
  })
  const candidatesQuery = useQuery({
    queryKey: ['records', 'lost', lostId, 'candidates'],
    queryFn: () => lostRecordsApi.candidates(lostId),
    enabled: Boolean(lostId) && !matching,
  })
  const lostImage = useAssetObjectUrl(lostQuery.data?.public_image_asset_id)
  const finishMatching = useCallback(() => setMatching(false), [])
  const retry = () => {
    setMatching(true)
    setAttempt((value) => value + 1)
  }

  if (!lostId) return <div className="p-8">寻物记录不存在</div>
  if (lostQuery.isLoading) return <div className="p-8">正在加载寻物记录...</div>
  if (lostQuery.isError || !lostQuery.data) return <div className="p-8" role="alert"><p className="mb-3">无法加载寻物记录</p><button type="button" className="btn btn-secondary" onClick={() => void lostQuery.refetch()}>重试加载</button></div>
  const lost = lostQuery.data
  const candidates = candidatesQuery.data ?? []

  return (
    <div className="h-full flex overflow-hidden" style={{ background: 'var(--color-neutral-50)' }}>
      <aside className="w-[260px] flex-shrink-0 border-r overflow-y-auto p-4" style={{ background: 'white', borderColor: 'var(--color-neutral-200)' }}>
        <Link to={`/lost/${lostId}`} className="text-xs">← 返回详情</Link>
        <p className="section-title my-3">我的失物</p>
        <div className="w-full h-32 rounded-lg overflow-hidden mb-3" style={{ background: 'var(--color-neutral-100)' }}>
          {lostImage.url ? <img src={lostImage.url} alt={lost.name_public ?? '失物'} className="w-full h-full object-cover" /> : <span className="h-full flex items-center justify-center text-xs" style={{ color: 'var(--muted)' }}>{lostImage.loading ? '图片加载中' : lostImage.error ? '图片加载失败' : '暂无图片'}</span>}
        </div>
        <h3 className="text-base font-bold">{lost.name_public ?? '未命名物品'}</h3>
        <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>{publicCategoryLabel(lost.public_category)}</p>
        <p className="text-xs mt-3">{lost.event_time_public ?? '时间未填写'}</p>
        <p className="text-xs mt-1">{lost.location_public ?? locationAreaLabel(lost.location_area)}</p>
        <div className="mt-3 p-2.5 rounded-md" style={{ background: 'var(--color-neutral-50)' }}><p className="text-xs">{lost.description_public ?? '暂无公开描述'}</p></div>
      </aside>

      <main className="flex-1 overflow-y-auto p-5">
        <div className="flex items-center justify-between mb-4">
          <div><h2 className="text-base font-bold">{candidates.length} 个候选</h2><p className="text-xs" style={{ color: 'var(--muted)' }}>按匹配度排列 · 匹配分仅供参考</p></div>
          <div className="flex gap-2">
            <button type="button" onClick={retry} className="btn btn-secondary">重新匹配</button>
            <Link to={`/lost/${lostId}/unmatched-review`} className="btn btn-primary">提交未匹配复核</Link>
          </div>
        </div>
        <div className="callout callout-info mb-4 text-xs">匹配分仅表示信息相似程度，不代表物品归属。认领需通过身份核验。</div>
        {matching ? <MatchingProgress key={attempt} lostId={lostId} attempt={attempt} onComplete={finishMatching} /> : candidatesQuery.isLoading ? <p>正在加载候选...</p> : candidatesQuery.isError ? <div role="alert"><p className="mb-3">候选列表加载失败。</p><button type="button" className="btn btn-secondary" onClick={() => void candidatesQuery.refetch()}>重试加载候选</button></div> : candidates.length === 0 ? <div className="card p-8 text-center">暂无匹配候选</div> : <div className="space-y-3">{candidates.map((candidate, index) => <CandidateCard key={candidate.id} candidate={candidate} rank={index + 1} />)}</div>}
      </main>
    </div>
  )
}
