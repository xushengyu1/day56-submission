import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { candidatesApi } from '@/api/candidates'
import { claimsApi } from '@/api/claims'
import { isApiError } from '@/api/errors'

export function IdentityClaimForm() {
  const { candidateId = '' } = useParams<{ candidateId: string }>()
  const navigate = useNavigate()
  const [idNumber, setIdNumber] = useState('')
  const [feedback, setFeedback] = useState<string | null>(null)
  const [locked, setLocked] = useState(false)
  const [lockedClaimId, setLockedClaimId] = useState<string | null>(null)
  const [reviewReason, setReviewReason] = useState('')
  const candidateQuery = useQuery({
    queryKey: ['candidates', 'detail', candidateId],
    queryFn: () => candidatesApi.get(candidateId),
    enabled: Boolean(candidateId),
  })
  const verify = useMutation({
    mutationFn: () => claimsApi.verifyIdentity(candidateId, idNumber),
    onSuccess: (outcome) => {
      setIdNumber('')
      if (outcome.status === 'VERIFYING' || outcome.status === 'LOCKED') {
        setLocked(outcome.status === 'LOCKED')
        setLockedClaimId(outcome.status === 'LOCKED' ? outcome.claim_id : null)
        setFeedback(outcome.status === 'LOCKED'
          ? '安全核验已锁定，请提交人工复核'
          : `核验未通过，剩余 ${outcome.attempts_remaining} 次尝试`)
        return
      }
      navigate(`/claims/${encodeURIComponent(outcome.claim_id)}/progress`)
    },
    onError: (error) => {
      setIdNumber('')
      if (isApiError(error) && error.code === 'ATTEMPT_LOCKED') {
        setLocked(true)
        setFeedback('安全核验已锁定，请从我的记录进入认领进度申请人工复核')
      } else {
        setFeedback('核验提交失败，请稍后重试')
      }
    },
  })
  const requestReview = useMutation({
    mutationFn: () => claimsApi.createReview(lockedClaimId as string, reviewReason.trim()),
    onSuccess: () => navigate(`/claims/${encodeURIComponent(lockedClaimId as string)}/progress`),
  })

  if (!candidateId) return <div role="alert" className="p-8 text-center">缺少候选编号</div>
  if (candidateQuery.isLoading) return <div className="p-8 text-center">正在加载候选...</div>
  if (candidateQuery.isError || !candidateQuery.data) {
    return <div role="alert" className="p-8 text-center">候选加载失败，请稍后重试</div>
  }
  const found = candidateQuery.data.found_record

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (idNumber.length !== 18 || verify.isPending || locked) return
    setFeedback(null)
    verify.mutate()
  }

  return (
    <div className="max-w-xl mx-auto p-8">
      <header className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">身份证件号码核验</h2>
        <p className="text-gray-500">请输入完整证件号码进行安全比对</p>
      </header>
      <section className="bg-white rounded-2xl border border-gray-100 p-5 mb-6">
        <h3 className="font-bold text-gray-900">{found.name_public ?? '身份证件'}</h3>
        <p className="text-sm text-gray-500 mt-1">{found.location_public ?? '地点未填写'} · {found.event_time_public ?? '时间未填写'}</p>
        <p className="text-xs text-gray-400 mt-4">证件号码（掩码）</p>
        <p className="text-lg font-mono font-bold text-gray-700">{found.number_masked ?? '未提供'}</p>
      </section>
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-100 p-6">
        <label htmlFor="identity-number" className="block text-sm font-semibold text-gray-900 mb-3">请输入完整证件号码</label>
        <input
          id="identity-number"
          type="password"
          inputMode="text"
          autoComplete="off"
          placeholder="请输入 18 位身份证号码"
          maxLength={18}
          value={idNumber}
          onChange={(event) => setIdNumber(event.target.value.replace(/\s/g, ''))}
          className="w-full px-4 py-4 border-2 border-gray-200 rounded-xl text-lg font-mono"
        />
        <p className="text-xs text-gray-400 mt-3">号码将通过加密方式比对，不会明文存储；尝试次数与锁定状态以服务端结果为准。</p>
        {feedback && <p role="alert" className="mt-4 text-sm text-amber-700">{feedback}</p>}
        <button
          type="submit"
          disabled={idNumber.length !== 18 || verify.isPending || locked}
          className="mt-6 w-full py-4 bg-blue-600 disabled:bg-blue-300 text-white font-bold rounded-xl"
        >
          {verify.isPending ? '提交中…' : '提交验证'}
        </button>
      </form>
      {lockedClaimId && (
        <form
          className="bg-amber-50 rounded-2xl p-6 mt-6"
          onSubmit={(event) => {
            event.preventDefault()
            if (reviewReason.trim() && !requestReview.isPending) requestReview.mutate()
          }}
        >
          <label htmlFor="identity-review-reason" className="block text-sm font-semibold mb-3">人工复核说明</label>
          <textarea
            id="identity-review-reason"
            rows={3}
            value={reviewReason}
            onChange={(event) => setReviewReason(event.target.value)}
            className="w-full px-4 py-3 border border-amber-200 rounded-xl"
            placeholder="请说明需要人工复核的原因"
          />
          {requestReview.isError && <p role="alert" className="mt-3 text-sm text-red-600">复核申请提交失败，请重试</p>}
          <button
            type="submit"
            disabled={!reviewReason.trim() || requestReview.isPending}
            className="mt-4 w-full py-3 bg-amber-600 disabled:bg-amber-300 text-white font-bold rounded-xl"
          >
            {requestReview.isPending ? '提交中…' : '申请人工复核'}
          </button>
        </form>
      )}
    </div>
  )
}
