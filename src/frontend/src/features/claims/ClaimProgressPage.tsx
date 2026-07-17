import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { candidatesApi } from '@/api/candidates'
import { claimsApi } from '@/api/claims'
import { useAssetObjectUrl } from '@/hooks/useAssetObjectUrl'

const STATUS_LABELS = {
  SUBMITTED: '已提交',
  VERIFYING: '核验中',
  PENDING_ADMIN_REVIEW: '等待管理员复核',
  PENDING_HANDOFF: '待交接',
  REJECTED: '认领已驳回',
  CLAIMED: '已认领',
  LOCKED: '核验已锁定',
} as const

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

const EVENT_TYPE_LABELS: Record<string, string> = {
  CLAIM_SUBMITTED: '认领已提交',
  IDENTITY_CLAIM_ATTEMPTED: '身份认领尝试',
  OTHER_CLAIM_VERIFIED: '其他认领核验',
  ADMIN_REVIEW_DECIDED: '管理员复核决定',
  HANDOFF_COMPLETED: '交接完成',
}

export function ClaimProgressPage() {
  const { id = '' } = useParams<{ id: string }>()
  const claimQuery = useQuery({
    queryKey: ['claims', 'detail', id],
    queryFn: () => claimsApi.get(id),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'VERIFYING' || status === 'PENDING_ADMIN_REVIEW' ? 2000 : false
    },
  })
  const contactQuery = useQuery({
    queryKey: ['claims', 'contact', id],
    queryFn: () => claimsApi.contact(id),
    enabled: claimQuery.data?.status === 'PENDING_HANDOFF',
  })
  const candidateId = claimQuery.data?.candidate_id ?? ''
  const candidateQuery = useQuery({
    queryKey: ['candidates', 'detail', candidateId],
    queryFn: () => candidatesApi.get(candidateId),
    enabled: Boolean(candidateId),
  })
  const found = candidateQuery.data?.found_record
  const image = useAssetObjectUrl(found?.public_image_asset_id)

  if (!id) return <div role="alert" className="p-8 text-center">缺少认领编号</div>
  if (claimQuery.isLoading) return <div className="p-8 text-center">正在加载认领进度...</div>
  if (claimQuery.isError || !claimQuery.data) return <div role="alert" className="p-8 text-center">认领进度加载失败</div>
  const claim = claimQuery.data

  return (
    <div className="max-w-2xl mx-auto p-8">
      <header className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
        <p className="text-xs text-gray-400">认领编号：{claim.id}</p>
        <h2 className="text-2xl font-bold mt-2">{STATUS_LABELS[claim.status]}</h2>
        <p className="text-sm text-gray-500 mt-2">结果：{RESULT_CODE_LABELS[claim.result_code] ?? claim.result_code ?? '处理中'}</p>
        <p className="text-sm text-gray-500">已尝试 {claim.attempt_count} 次；剩余 {claim.attempts_remaining} 次</p>
      </header>
      <section className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
        <h3 className="font-bold mb-3">认领物品</h3>
        {candidateQuery.isLoading && <p className="text-sm">正在加载物品信息...</p>}
        {candidateQuery.isError && <p role="alert" className="text-sm">物品信息加载失败</p>}
        {image.url && <img src={image.url} alt={found?.name_public ?? '认领物品'} className="w-full max-h-64 object-contain rounded-xl mb-4" />}
        {found && (
          <>
            <p className="font-semibold">{found.name_public ?? '未命名物品'}</p>
            <p className="text-sm text-gray-500 mt-1">{found.location_public ?? '地点未填写'} · {found.event_time_public ?? '时间未填写'}</p>
            {found.description_public && <p className="text-sm mt-2">{found.description_public}</p>}
          </>
        )}
      </section>
      {claim.status === 'PENDING_HANDOFF' && (
        <section className="bg-emerald-50 rounded-2xl p-6 mb-6">
          <h3 className="font-bold">拾得者联系方式</h3>
          {contactQuery.isLoading && <p className="text-sm mt-2">正在加载...</p>}
          {contactQuery.data && <p className="text-sm mt-2">{contactQuery.data.email}</p>}
          {contactQuery.isError && <p role="alert" className="text-sm mt-2">联系方式加载失败</p>}
        </section>
      )}
      {claim.timeline.length > 0 && (
        <section className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
          <h3 className="font-bold mb-3">处理时间线</h3>
          {claim.timeline.map((event, index) => (
            <p key={`${event.created_at}-${index}`} className="text-sm py-2 border-b last:border-0">
              {EVENT_TYPE_LABELS[event.event_type] ?? event.event_type} · {RESULT_CODE_LABELS[event.result_code] ?? event.result_code}
            </p>
          ))}
        </section>
      )}
      <Link to="/records" className="inline-flex px-5 py-3 border rounded-xl">返回我的记录</Link>
    </div>
  )
}
