import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/api/admin'
import type { ReviewQueueItem } from '@/api/types'

const SOURCE_LABELS: Record<string, string> = {
  CLAIM: '认领复核',
  CLAIM_REVIEW: '认领复核',
  UNMATCHED: '未匹配复核',
}

const STATUS_LABELS: Record<string, string> = {
  PENDING_ADMIN_REVIEW: '待管理员复核',
  OPEN: '待处理',
  RESOLVED: '已处理',
}

function ReviewRow({ review }: { review: ReviewQueueItem }) {
  return (
    <Link to={`/admin/reviews/${encodeURIComponent(review.id)}`} className="list-item" style={{ marginBottom: '10px' }}>
      <div className="list-item-head">
        <div>
          <span className="list-item-title">{review.id}</span>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '4px' }}>
            {review.item_type === 'IDENTITY_DOCUMENT' ? '身份证件' : review.item_type === 'OTHER' ? '其他物品' : '寻物记录'}
          </p>
        </div>
        <span className="badge">{SOURCE_LABELS[review.source] ?? review.source}</span>
      </div>
      <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '12px', color: 'var(--muted)' }}>
        <span>{STATUS_LABELS[review.status] ?? review.status}</span>
        {review.result_code && <span>{review.result_code}</span>}
        <span>{new Date(review.created_at).toLocaleString('zh-CN')}</span>
      </div>
    </Link>
  )
}

export function AdminQueuePage() {
  const [filter, setFilter] = useState('ALL')
  const reviewsQuery = useQuery({ queryKey: ['admin', 'reviews'], queryFn: adminApi.reviews })
  const reviews = reviewsQuery.data ?? []
  const filtered = filter === 'ALL' ? reviews : reviews.filter((review) => review.source === filter)
  const sources = ['ALL', ...Array.from(new Set(reviews.map((review) => review.source)))]

  return (
    <div>
      <header style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 800 }}>复核队列</h2>
        <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>处理真实待审核认领和未匹配申请</p>
      </header>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {sources.map((source) => (
          <button key={source} type="button" onClick={() => setFilter(source)} className="btn btn-secondary">
            {source === 'ALL' ? `全部 (${reviews.length})` : `${SOURCE_LABELS[source] ?? source} (${reviews.filter((review) => review.source === source).length})`}
          </button>
        ))}
      </div>
      <div className="glass-card" style={{ padding: '20px', borderRadius: '24px' }}>
        {reviewsQuery.isLoading && <p className="text-center py-12">正在加载复核队列...</p>}
        {reviewsQuery.isError && <p role="alert" className="text-center py-12">复核队列加载失败</p>}
        {!reviewsQuery.isLoading && !reviewsQuery.isError && filtered.length === 0 && <p className="text-center py-12">暂无待处理复核</p>}
        {filtered.map((review) => <ReviewRow key={review.id} review={review} />)}
      </div>
    </div>
  )
}
