import type { RecordStatus, ClaimStatus } from '@/api/types'

// 与后端 RecordStatus / ClaimStatus 枚举对齐
const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; dot: string }> = {
  // RecordStatus
  DRAFT: { label: '草稿', bg: 'rgba(148,163,184,0.1)', text: '#7a8e9e', dot: '#94a3b8' },
  PROCESSING: { label: 'AI处理中', bg: 'rgba(107,139,164,0.1)', text: '#4a6b82', dot: '#6b8ba4' },
  PUBLISHED: { label: '招领中', bg: 'rgba(107,158,122,0.1)', text: '#4a7a5a', dot: '#6b9e7a' },
  MATCHING_FAILED: { label: '匹配失败', bg: 'rgba(196,163,90,0.1)', text: '#8a7040', dot: '#c4a35a' },
  PENDING_HANDOFF: { label: '待交接', bg: 'rgba(107,158,122,0.1)', text: '#4a7a5a', dot: '#6b9e7a' },
  CLAIMED: { label: '已认领', bg: 'rgba(107,158,122,0.1)', text: '#3a6a4a', dot: '#4a7a5a' },
  CLOSED: { label: '已关闭', bg: 'rgba(148,163,184,0.08)', text: '#7a8e9e', dot: '#94a3b8' },
  CANCELLED: { label: '已取消', bg: 'rgba(148,163,184,0.08)', text: '#7a8e9e', dot: '#94a3b8' },

  // ClaimStatus
  SUBMITTED: { label: '已提交', bg: 'rgba(107,139,164,0.1)', text: '#4a6b82', dot: '#6b8ba4' },
  VERIFYING: { label: '核验中', bg: 'rgba(139,123,176,0.1)', text: '#6b5b90', dot: '#8b7bb0' },
  PENDING_ADMIN_REVIEW: { label: '待管理员复核', bg: 'rgba(196,163,90,0.1)', text: '#8a7040', dot: '#c4a35a' },
  REJECTED: { label: '已拒绝', bg: 'rgba(184,92,92,0.1)', text: '#8a4a4a', dot: '#b85c5c' },
  LOCKED: { label: '已锁定', bg: 'rgba(184,92,92,0.08)', text: '#7a4a4a', dot: '#b85c5c' },
}

export function StatusBadge({ status }: { status: RecordStatus | ClaimStatus | string }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG['DRAFT']
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium"
      style={{ background: config.bg, color: config.text }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: config.dot }}></span>
      {config.label}
    </span>
  )
}
