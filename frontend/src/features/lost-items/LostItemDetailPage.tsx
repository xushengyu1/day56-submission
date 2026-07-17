import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { mockApi } from '@/api/mock'
import { StatusBadge } from '@/components/StatusBadge'
import { useAuth } from '@/features/auth/hooks'

const CATEGORY_MAP: Record<string, string> = {
  'IDENTITY_DOCUMENT': '身份证件',
  'OTHER': '其他物品',
}

export function LostItemDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()

  const { data: item, isLoading } = useQuery({
    queryKey: ['item', id],
    queryFn: () => mockApi.getItemDetail(id || ''),
  })

  if (isLoading) {
    return (
      <div className="page-shell" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <i className="fas fa-spinner fa-spin text-xl" style={{ color: 'var(--primary)' }}></i>
      </div>
    )
  }

  if (!item) {
    return (
      <div className="page-shell" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: '12px' }}>
        <i className="fas fa-inbox" style={{ fontSize: '32px', color: '#b8c8d8' }}></i>
        <p style={{ color: 'var(--muted)' }}>物品不存在</p>
        <Link to="/" style={{ fontSize: '13px', color: 'var(--primary)', textDecoration: 'none' }}>返回首页</Link>
      </div>
    )
  }

  const isOwner = item.owner_user_id === user?.id

  return (
    <div className="page-shell">
      {/* 返回 */}
      <div style={{ maxWidth: '1200px', margin: '20px auto 0' }}>
        <Link to="/" style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px',
          fontSize: '13px', color: 'var(--muted)', marginBottom: '16px', textDecoration: 'none',
        }}>
          <i className="fas fa-arrow-left text-[11px]"></i> 返回首页
        </Link>
      </div>

      {/* 详情卡片 */}
      <section style={{ maxWidth: '1200px', margin: '0 auto 40px' }}>
        <div className="glass-card" style={{ padding: '32px', borderRadius: '28px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '32px' }}>
            {/* 左侧图片 */}
            <div>
              <div style={{
                width: '100%', aspectRatio: '4/3', borderRadius: '20px', overflow: 'hidden',
                background: 'linear-gradient(180deg, rgba(232, 240, 248, 0.9) 0%, rgba(248, 250, 252, 0.92) 100%)',
                border: '1.5px dashed rgba(107, 139, 164, 0.3)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '12px',
              }}>
                {item.public_image_path ? (
                  <img src={item.public_image_path} alt={item.name_public}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <>
                    <i className="fas fa-image" style={{ fontSize: '40px', color: '#b8c8d8' }}></i>
                    <span style={{ fontSize: '14px', color: '#b8c8d8' }}>暂无图片</span>
                  </>
                )}
              </div>
            </div>

            {/* 右侧信息 */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* 标题行 */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                  <span style={{
                    padding: '4px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: 700,
                    background: 'rgba(107,139,164,0.1)', color: '#4a6b82',
                  }}>寻物</span>
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: '4px',
                    padding: '2px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
                    background: 'rgba(107,139,164,0.1)', color: '#4a6b82',
                  }}>
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#6b8ba4' }}></span>
                    寻物中
                  </span>
                </div>
                <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.02em' }}>
                  {item.name_public}
                </h1>
              </div>

              {/* 信息列表 */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {[
                  { icon: 'fa-tag', label: '物品类型', value: CATEGORY_MAP[item.item_type] || item.item_type },
                  { icon: 'fa-location-dot', label: '丢失地点', value: item.location_public },
                  { icon: 'fa-clock', label: '丢失时间', value: item.event_time_public },
                ].map((field) => (
                  <div key={field.label} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '36px', height: '36px', borderRadius: '12px',
                      background: 'rgba(107,139,164,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                    }}>
                      <i className={`fas ${field.icon} text-xs`} style={{ color: '#4a6b82' }}></i>
                    </div>
                    <div>
                      <p style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '2px' }}>{field.label}</p>
                      <p style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)' }}>{field.value}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* 描述 */}
              {item.description_public && (
                <div style={{
                  padding: '18px', borderRadius: '16px',
                  background: 'rgba(248,250,252,0.8)', border: '1px solid rgba(226,232,240,0.5)',
                }}>
                  <p style={{ fontSize: '11px', fontWeight: 700, color: 'var(--muted)', marginBottom: '8px', letterSpacing: '0.03em' }}>
                    物品描述
                  </p>
                  <p style={{ fontSize: '14px', color: 'var(--text)', lineHeight: 1.8 }}>
                    {item.description_public}
                  </p>
                </div>
              )}

              {/* 时间戳 */}
              <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                发布于 {new Date(item.created_at).toLocaleString('zh-CN')}
              </div>

              {/* 操作按钮 */}
              <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                {isOwner && item.status === 'CLAIMED' ? (
                  <div style={{
                    padding: '14px 20px', borderRadius: '14px',
                    background: 'rgba(107,158,122,0.06)', border: '1px solid rgba(107,158,122,0.15)',
                    fontSize: '13px', color: '#4a7a5a', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600,
                  }}>
                    <i className="fas fa-check-circle"></i>
                    物品已找回
                  </div>
                ) : isOwner ? (
                  <Link to={`/lost/${item.id}/candidates`} style={{
                    padding: '12px 24px', borderRadius: '14px', border: 'none', textDecoration: 'none',
                    background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-deep) 100%)',
                    color: '#fff', fontWeight: 700, fontSize: '14px', display: 'inline-flex', alignItems: 'center', gap: '8px',
                    boxShadow: 'var(--shadow-btn)',
                  }}>
                    <i className="fas fa-magnifying-glass text-xs"></i>
                    查看匹配结果
                  </Link>
                ) : (
                  <div style={{
                    padding: '14px 20px', borderRadius: '14px',
                    background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.15)',
                    fontSize: '13px', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '8px',
                  }}>
                    <i className="fas fa-eye text-xs"></i>
                    仅可查看，匹配功能仅限发布者使用
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
