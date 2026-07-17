import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/api/admin'

const EVENT_TYPE_LABELS: Record<string, string> = {
  RECORD_CREATED: '记录创建',
  RECORD_STATUS_CHANGED: '记录状态变更',
  LOST_RECORD_CREATED: '寻物记录发布',
  FOUND_RECORD_PUBLISHED: '招领记录发布',
  CLAIM_SUBMITTED: '认领申请提交',
  CLAIM_STATUS_CHANGED: '认领状态变更',
  CLAIM_ATTEMPT_RESULT: '认领核验结果',
  IDENTITY_CLAIM_ATTEMPTED: '身份认领尝试',
  OTHER_CLAIM_VERIFIED: '其他认领核验',
  ADMIN_REVIEW_DECIDED: '管理员复核决定',
  ADMIN_REVIEW_DECISION: '管理员复核决定',
  HANDOFF_COMPLETED: '交接完成',
  CANDIDATE_MATCH_CREATED: '候选匹配创建',
  IDENTITY_SECRET_STORED: '身份信息存储',
  AI_EXTRACTION_COMPLETED: 'AI识别完成',
  VERIFICATION_SET_CREATED: '验证问题集创建',
  VERIFICATION_CONFIRMED: '验证问题确认',
  REVIEW_REQUEST_CREATED: '复核申请创建',
}

const AGGREGATE_TYPE_LABELS: Record<string, string> = {
  claim: '认领申请',
  Claim: '认领申请',
  review_request: '复核申请',
  ReviewRequest: '复核申请',
  item_record: '物品记录',
  ItemRecord: '物品记录',
  ClaimAttempt: '认领核验',
  AdminReview: '管理员复核',
  CandidateMatch: '候选匹配',
  IdentityDocumentSecret: '身份信息',
  AIExtraction: 'AI识别',
  VerificationSet: '验证问题集',
}

const RESULT_CODE_LABELS: Record<string, string> = {
  OK: '成功',
  PUBLISHED: '已发布',
  CLAIMED: '已认领',
  PASS: '通过',
  FAIL: '未通过',
  APPROVE_TO_HANDOFF: '批准交接',
  REJECT: '驳回',
  RECOMMEND_CANDIDATE: '推荐候选',
  MODEL_UNAVAILABLE: '模型不可用',
  // 身份核验结果
  IDENTITY_VERIFIED: '身份已验证',
  IDENTITY_NOT_VERIFIED: '身份未验证',
  DUPLICATE_IDENTITY_REVIEW: '重复身份待复核',
  ATTEMPT_LOCKED: '尝试次数已锁定',
  // 其他物品核验结果
  ANSWERS_VERIFIED: '答案已验证',
  ALL_KEY_ANSWERS_MATCH: '所有关键答案匹配',
  ALL_MATCH: '全部匹配',
  PARTIAL_MATCH: '部分匹配',
  KEY_ANSWER_CONFLICT: '关键答案冲突',
  ANSWER_VAGUE: '答案模糊',
  ANSWER_DETAILED: '答案详细',
  MINOR_DIFF: '轻微差异',
  MAJOR_DIFF: '重大差异',
  UNRELATED: '无关',
  MISSING_INFO: '信息缺失',
  ANSWER_UNCLEAR: '答案不清晰',
  CONFIDENCE_TOO_LOW: '置信度过低',
  MODEL_RESPONSE_INVALID: '模型响应无效',
  // 发布相关
  FOUND_RECORD_PUBLISHED: '招领记录已发布',
  HANDOFF_COMPLETED: '交接完成',
  CLAIM_SUBMITTED: '认领已提交',
  // 状态相关
  DRAFT: '草稿',
  PROCESSING: '处理中',
  PUBLISHED_STATUS: '已发布',
  MATCHING_FAILED: '匹配失败',
  PENDING_HANDOFF: '待交接',
  CLAIMED_STATUS: '已认领',
  CLOSED: '已关闭',
  CANCELLED: '已取消',
}

const ITEM_TYPE_LABELS: Record<string, string> = {
  IDENTITY_DOCUMENT: '身份证明文件',
  OTHER: '其他物品',
}

const PUBLIC_CATEGORY_LABELS: Record<string, string> = {
  ELECTRONICS: '电子产品',
  IDENTITY_CARD: '证件卡片',
  CLOTHING: '服饰配饰',
  STATIONERY: '学习用品',
  OTHER_CATEGORY: '其他',
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: '草稿',
  PROCESSING: '处理中',
  PUBLISHED: '已发布',
  MATCHING_FAILED: '匹配失败',
  PENDING_HANDOFF: '待交接',
  CLAIMED: '已认领',
  CLOSED: '已关闭',
  CANCELLED: '已取消',
  SUBMITTED: '已提交',
  VERIFYING: '验证中',
  PENDING_ADMIN_REVIEW: '待管理员审核',
  REJECTED: '已驳回',
  LOCKED: '已锁定',
}

const METADATA_KEY_LABELS: Record<string, string> = {
  reason_present: '处理理由',
  attempt_no: '尝试次数',
  confidence: '置信度',
  hard_conflict: '硬冲突',
  needs_admin_review: '需要管理员复核',
  item_type: '物品类型',
  old_status: '原状态',
  new_status: '新状态',
  decision: '决定',
  reason: '原因',
  masked_number: '脱敏号码',
  document_type: '证件类型',
  total_score: '总分',
  lost_record_id: '丢失记录ID',
  found_record_id: '拾到记录ID',
  claim_id: '认领ID',
  request_type: '请求类型',
  question_count: '问题数量',
  confirmed_count: '已确认问题数',
  suggested_item_type: '建议物品类型',
  kind: '类型',
  public_category: '公开分类',
  record_kind: '记录类型',
  finder_confirmed_at: '拾得者确认时间',
  verification_result: '验证结果',
  witness: '见证人',
  handoff_location: '交接地点',
  answers: '答案',
  route_source: '路由来源',
  // 用户信息
  owner_name: '失主姓名',
  owner_email: '失主邮箱',
  finder_name: '拾得者姓名',
  finder_email: '拾得者邮箱',
  // 物品信息
  item_name: '物品名称',
  location: '地点',
  confirmation: '确认交接',
}

const RECORD_KIND_LABELS: Record<string, string> = {
  LOST: '丢失',
  FOUND: '拾到',
}

function formatValue(key: string, value: unknown): string {
  if (key === 'item_type') return ITEM_TYPE_LABELS[String(value)] ?? String(value)
  if (key === 'public_category') return PUBLIC_CATEGORY_LABELS[String(value)] ?? String(value)
  if (key === 'old_status' || key === 'new_status' || key === 'status') return STATUS_LABELS[String(value)] ?? String(value)
  if (key === 'decision') return RESULT_CODE_LABELS[String(value)] ?? String(value)
  if (key === 'kind' || key === 'record_kind') return RECORD_KIND_LABELS[String(value)] ?? String(value)
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function formatMetadata(metadata: Record<string, unknown>): string {
  const entries = Object.entries(metadata)
  if (entries.length === 0) return ''
  return entries
    .map(([key, value]) => {
      const label = METADATA_KEY_LABELS[key] ?? key
      return `${label}: ${formatValue(key, value)}`
    })
    .join(' · ')
}

export function AdminAuditPage() {
  const [page, setPage] = useState(1)
  const pageSize = 5

  const auditQuery = useQuery({
    queryKey: ['admin', 'audit', page],
    queryFn: () => adminApi.audit(page, pageSize),
  })

  const events = auditQuery.data?.items ?? []
  const totalPages = auditQuery.data?.total_pages ?? 0
  const total = auditQuery.data?.total ?? 0

  return (
    <div>
      <header style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 800 }}>审计日志</h2>
        <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>
          系统返回的脱敏审计时间线 · 共 {total} 条记录
        </p>
      </header>
      <div className="glass-card" style={{ padding: '28px', borderRadius: '24px' }}>
        {auditQuery.isLoading && <p className="text-center py-12">正在加载审计日志...</p>}
        {auditQuery.isError && <p role="alert" className="text-center py-12">审计日志加载失败</p>}
        {!auditQuery.isLoading && !auditQuery.isError && events.length === 0 && (
          <p className="text-center py-12">暂无审计事件</p>
        )}
        {events.map((event) => (
          <article key={event.event_id} className="border-b last:border-0 py-4">
            <div className="flex justify-between gap-4">
              <h3 className="font-bold">{EVENT_TYPE_LABELS[event.event_type] ?? event.event_type}</h3>
              <time className="text-xs text-gray-500">{new Date(event.created_at).toLocaleString('zh-CN')}</time>
            </div>
            <p className="text-sm mt-2">
              {AGGREGATE_TYPE_LABELS[event.aggregate_type] ?? event.aggregate_type}
              {event.result_code && <span> · {RESULT_CODE_LABELS[event.result_code] ?? event.result_code}</span>}
            </p>
            {Object.keys(event.metadata_redacted).length > 0 && (
              <p className="text-xs text-gray-500 mt-2">{formatMetadata(event.metadata_redacted)}</p>
            )}
          </article>
        ))}

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px', marginTop: '24px', paddingTop: '20px', borderTop: '1px solid var(--line)' }}>
            <button
              type="button"
              className="btn btn-secondary"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              上一页
            </button>
            <span style={{ fontSize: '14px', color: 'var(--muted)' }}>
              第 {page} / {totalPages} 页
            </span>
            <button
              type="button"
              className="btn btn-secondary"
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
            >
              下一页
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
