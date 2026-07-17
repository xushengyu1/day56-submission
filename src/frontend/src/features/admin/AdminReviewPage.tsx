import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/api/admin'
import type { AdminDecision } from '@/api/types'

const RESULT_CODE_LABELS: Record<string, string> = {
  IDENTITY_VERIFIED: '身份已验证',
  IDENTITY_NOT_VERIFIED: '身份未验证',
  DUPLICATE_IDENTITY_REVIEW: '重复身份待复核',
  ATTEMPT_LOCKED: '尝试次数已锁定',
  ANSWERS_VERIFIED: '答案已验证',
  ALL_KEY_ANSWERS_MATCH: '所有关键答案匹配',
  ALL_MATCH: '全部匹配',
  PARTIAL_MATCH: '部分匹配',
  KEY_ANSWER_CONFLICT: '关键答案冲突',
  ANSWER_VAGUE: '答案模糊',
  ANSWER_UNCLEAR: '答案不清晰',
  CONFIDENCE_TOO_LOW: '置信度过低',
  MODEL_UNAVAILABLE: '模型不可用',
}

const RISK_FLAG_LABELS: Record<string, string> = {
  ATTEMPT_LIMIT: '尝试次数超限',
  DUPLICATE_IDENTITY: '重复身份',
}

export function AdminReviewPage() {
  const { id = '' } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [decision, setDecision] = useState<AdminDecision>('APPROVE_TO_HANDOFF')
  const [candidateId, setCandidateId] = useState('')
  const [reason, setReason] = useState('')
  const idempotency = useRef<{ intent: string; key: string } | null>(null)
  const detailQuery = useQuery({
    queryKey: ['admin', 'review', id],
    queryFn: () => adminApi.review(id),
    enabled: Boolean(id),
  })
  const unmatched = detailQuery.data?.source === 'UNMATCHED'

  useEffect(() => {
    if (!detailQuery.data) return
    setDecision(detailQuery.data.source === 'UNMATCHED' ? 'RECOMMEND_CANDIDATE' : 'APPROVE_TO_HANDOFF')
    setCandidateId('')
  }, [detailQuery.data])

  const decide = useMutation({
    mutationFn: async () => {
      const request = {
        decision,
        reason: reason.trim(),
        ...(decision === 'RECOMMEND_CANDIDATE' ? { candidate_id: candidateId } : {}),
      }
      const intent = JSON.stringify(request)
      if (idempotency.current?.intent !== intent) {
        idempotency.current = { intent, key: crypto.randomUUID() }
      }
      return adminApi.decide(id, request, idempotency.current.key)
    },
    onSuccess: async () => {
      idempotency.current = null
      await queryClient.invalidateQueries({ queryKey: ['admin', 'reviews'] })
      navigate('/admin')
    },
  })

  if (!id) return <div role="alert" className="p-8 text-center">缺少复核编号</div>
  if (detailQuery.isLoading) return <div className="p-8 text-center">正在加载复核详情...</div>
  if (detailQuery.isError || !detailQuery.data) return <div role="alert" className="p-8 text-center">复核详情加载失败</div>
  const review = detailQuery.data
  const primaryRecord = review.candidate?.found_record ?? review.lost_record
  const submitDisabled = !reason.trim() || decide.isPending || (decision === 'RECOMMEND_CANDIDATE' && !candidateId)

  return (
    <div>
      <Link to="/admin" className="inline-flex mb-4">← 返回队列</Link>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '20px' }}>
        <main style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <section className="glass-card" style={{ padding: '24px', borderRadius: '24px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 800 }}>{primaryRecord?.name_public ?? '复核详情'}</h2>
            <p className="text-sm mt-2">来源：{review.source} · 状态：{review.status}</p>
            <p className="text-sm mt-2">申请人：{review.requester_user_name}</p>
            {review.reason && <p className="text-sm mt-2">申请理由：{review.reason}</p>}
            {primaryRecord && <p className="text-sm mt-2">{primaryRecord.location_public ?? '地点未填写'} · {primaryRecord.event_time_public ?? '时间未填写'}</p>}
          </section>

          {unmatched && (
            <section className="glass-card" style={{ padding: '24px', borderRadius: '24px' }}>
              <h3 className="font-bold mb-4">安全候选 Top 5</h3>
              {review.candidates.length === 0 && <p className="text-sm text-gray-500">当前没有仍然有效的候选</p>}
              {review.candidates.map((candidate) => (
                <label key={candidate.id} className="block border rounded-xl p-4 mb-3">
                  <input
                    type="radio"
                    name="candidate"
                    aria-label={`${candidate.found_record.name_public ?? '未命名候选'} ${candidate.total_score} 分`}
                    checked={candidateId === candidate.id}
                    onChange={() => setCandidateId(candidate.id)}
                  />
                  <span className="ml-3 font-semibold">{candidate.found_record.name_public ?? '未命名候选'}</span>
                  <span className="ml-2 text-sm text-gray-500">{candidate.total_score} 分</span>
                </label>
              ))}
            </section>
          )}

          {!unmatched && (
            <section className="glass-card" style={{ padding: '24px', borderRadius: '24px' }}>
              <h3 className="font-bold mb-4">安全核验证据</h3>
              {review.evidence.length === 0 && <p className="text-sm text-gray-500">暂无核验证据</p>}
              {review.evidence.map((evidence) => (
                <div key={`${evidence.attempt_no}-${evidence.created_at}`} className="border rounded-xl p-4 mb-3">
                  <p className="font-semibold">第 {evidence.attempt_no} 次 · {RESULT_CODE_LABELS[evidence.result_code] ?? evidence.result_code}</p>
                  {evidence.risk_flag && <p className="text-sm mt-1">风险标记：{RISK_FLAG_LABELS[evidence.risk_flag] ?? evidence.risk_flag}</p>}
                  {evidence.answer_summary && <p className="text-sm mt-1">摘要：{JSON.stringify(evidence.answer_summary)}</p>}
                </div>
              ))}
            </section>
          )}
        </main>

        <aside className="glass-card" style={{ padding: '24px', borderRadius: '24px', alignSelf: 'start' }}>
          <h3 className="font-bold mb-4">复核决定</h3>
          {unmatched ? (
            <>
              <label className="block mb-3"><input type="radio" name="decision" checked={decision === 'RECOMMEND_CANDIDATE'} onChange={() => setDecision('RECOMMEND_CANDIDATE')} /> 推荐候选</label>
              <label className="block mb-3"><input type="radio" name="decision" checked={decision === 'REJECT'} onChange={() => setDecision('REJECT')} /> 驳回复核</label>
            </>
          ) : (
            <>
              <label className="block mb-3"><input type="radio" name="decision" checked={decision === 'APPROVE_TO_HANDOFF'} onChange={() => setDecision('APPROVE_TO_HANDOFF')} /> 进入交接</label>
              <label className="block mb-3"><input type="radio" name="decision" checked={decision === 'REJECT'} onChange={() => setDecision('REJECT')} /> 驳回认领</label>
            </>
          )}
          <form onSubmit={(event) => { event.preventDefault(); if (!submitDisabled) decide.mutate() }}>
            <label htmlFor="review-reason" className="block font-semibold mt-5 mb-2">处理理由</label>
            <textarea id="review-reason" value={reason} onChange={(event) => setReason(event.target.value)} rows={5} className="form-textarea" />
            {decide.isError && <p role="alert" className="text-sm text-red-600 mt-3">决定提交失败，可重试相同操作</p>}
            <button type="submit" disabled={submitDisabled} className="submit-btn mt-4 w-full">{decide.isPending ? '提交中…' : '提交决定'}</button>
          </form>
        </aside>
      </div>
    </div>
  )
}
