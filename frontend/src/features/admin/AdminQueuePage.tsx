import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { mockApi } from '@/api/mock'
import type { ReviewRecord } from '@/api/types'

const REVIEW_TYPE_CONFIG: Record<string, { label: string; color: string; bg: string; icon: string }> = {
  MULTI_CLAIM: { label: '多人认领', color: '#b85c5c', bg: 'rgba(184,92,92,0.08)', icon: 'fa-users' },
  VERIFICATION_FAILED: { label: '核验未通过', color: '#c4a35a', bg: 'rgba(196,163,90,0.08)', icon: 'fa-xmark-circle' },
  IDENTITY_ANOMALY: { label: '证件异常', color: '#d97706', bg: 'rgba(217,119,6,0.08)', icon: 'fa-id-card' },
  UNMATCHED: { label: '未匹配复核', color: '#6b8ba4', bg: 'rgba(107,139,164,0.08)', icon: 'fa-flag' },
  CLAIM_REVIEW: { label: '认领复核', color: '#8b7bb0', bg: 'rgba(139,123,176,0.08)', icon: 'fa-clipboard-check' },
}

function ReviewRow({ review }: { review: ReviewRecord }) {
  const config = REVIEW_TYPE_CONFIG[review.review_type] || { label: review.review_type, color: '#7a8e9e', bg: 'rgba(122,142,158,0.08)', icon: 'fa-circle' }
  return (
    <Link to={`/admin/reviews/${review.id}`} className="list-item" style={{ marginBottom: '10px' }}>
      <div className="list-item-head">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: '12px',
            background: config.bg, display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <i className={`fas ${config.icon} text-xs`} style={{ color: config.color }}></i>
          </div>
          <div>
            <span className="list-item-title" style={{ fontSize: '14px' }}>{review.target_name || review.target_id}</span>
            <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>{review.target_type === 'LOST' ? '寻物' : '认领'} · {review.id}</p>
          </div>
        </div>
        <span style={{
          padding: '4px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
          background: config.bg, color: config.color
        }}>
          {config.label}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '8px', fontSize: '12px', color: 'var(--muted)' }}>
        <span><i className="fas fa-user mr-1.5"></i>{review.applicant_name || review.applicant_id}</span>
        <span><i className="fas fa-comment mr-1.5"></i>{review.reason}</span>
        <span><i className="fas fa-clock mr-1.5"></i>{new Date(review.created_at).toLocaleDateString('zh-CN')}</span>
      </div>
    </Link>
  )
}

export function AdminQueuePage() {
  const { data: reviews = [], isLoading } = useQuery({
    queryKey: ['admin', 'reviews'],
    queryFn: () => mockApi.getReviewQueue(),
  })

  const stats = {
    total: reviews.length,
    multiClaim: reviews.filter((r) => r.review_type === 'MULTI_CLAIM').length,
    verifyFailed: reviews.filter((r) => r.review_type === 'VERIFICATION_FAILED').length,
    unmatched: reviews.filter((r) => r.review_type === 'UNMATCHED').length,
    claimReview: reviews.filter((r) => r.review_type === 'CLAIM_REVIEW').length,
  }

  const statCards = [
    { label: '待处理', count: stats.total, icon: 'fa-inbox', color: '#8b7bb0', bg: 'rgba(139,123,176,0.1)' },
    { label: '多人认领', count: stats.multiClaim, icon: 'fa-users', color: '#b85c5c', bg: 'rgba(184,92,92,0.1)' },
    { label: '核验未通过', count: stats.verifyFailed, icon: 'fa-xmark-circle', color: '#c4a35a', bg: 'rgba(196,163,90,0.1)' },
    { label: '未匹配复核', count: stats.unmatched, icon: 'fa-flag', color: '#6b8ba4', bg: 'rgba(107,139,164,0.1)' },
    { label: '认领复核', count: stats.claimReview, icon: 'fa-clipboard-check', color: '#6b9e7a', bg: 'rgba(107,158,122,0.1)' },
  ]

  return (
    <div>
      {/* 页面标题 */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.02em' }}>复核队列</h2>
        <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>处理待审核的认领申请和异常情况</p>
      </div>

      {/* 统计卡片 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '14px', marginBottom: '20px' }}>
        {statCards.map((stat) => (
          <div key={stat.label} className="glass-card" style={{ padding: '18px', borderRadius: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontSize: '12px', color: 'var(--muted)' }}>{stat.label}</span>
              <div style={{
                width: '32px', height: '32px', borderRadius: '10px',
                background: stat.bg, display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <i className={`fas ${stat.icon} text-xs`} style={{ color: stat.color }}></i>
              </div>
            </div>
            <p style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text)' }}>{stat.count}</p>
          </div>
        ))}
      </div>

      {/* 筛选标签 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button style={{
          padding: '8px 16px', borderRadius: '999px', fontSize: '13px', fontWeight: 700, border: 'none',
          background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-deep) 100%)', color: '#fff'
        }}>
          全部 ({stats.total})
        </button>
        {Object.entries(REVIEW_TYPE_CONFIG).map(([key, config]) => {
          const count = reviews.filter((r) => r.review_type === key).length
          return count > 0 ? (
            <button key={key} style={{
              padding: '8px 16px', borderRadius: '999px', fontSize: '13px', fontWeight: 500, border: 'none',
              background: 'rgba(255,255,255,0.88)', color: 'var(--text)', cursor: 'pointer'
            }}>
              {config.label} ({count})
            </button>
          ) : null
        })}
      </div>

      {/* 复核列表 */}
      <div className="glass-card" style={{ padding: '20px', borderRadius: '24px' }}>
        <div className="item-list">
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <i className="fas fa-spinner fa-spin text-xl" style={{ color: 'var(--primary)' }}></i>
            </div>
          ) : reviews.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <i className="fas fa-check-circle" style={{ fontSize: '32px', color: 'var(--success)', marginBottom: '12px', display: 'block' }}></i>
              <p style={{ fontSize: '14px', color: 'var(--muted)' }}>暂无待处理复核</p>
            </div>
          ) : (
            reviews.map((review) => <ReviewRow key={review.id} review={review} />)
          )}
        </div>
      </div>
    </div>
  )
}
