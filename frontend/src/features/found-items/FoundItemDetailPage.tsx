import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { mockApi } from '@/api/mock'
import { StatusBadge } from '@/components/StatusBadge'

const CATEGORY_MAP: Record<string, string> = {
  'IDENTITY_DOCUMENT': '身份证件',
  'OTHER': '其他物品',
}

export function FoundItemDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: item, isLoading } = useQuery({
    queryKey: ['item', id],
    queryFn: () => mockApi.getFoundItemDetail(id || ''),
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
                    background: 'rgba(107,158,122,0.1)', color: '#4a7a5a',
                  }}>招领</span>
                  <StatusBadge status={item.status} />
                </div>
                <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.02em' }}>
                  {item.name_public}
                </h1>
              </div>

              {/* 信息列表 */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {[
                  { icon: 'fa-tag', label: '物品类型', value: CATEGORY_MAP[item.item_type] || item.item_type },
                  { icon: 'fa-location-dot', label: '捡到地点', value: item.location_public },
                  { icon: 'fa-clock', label: '捡到时间', value: item.event_time_public },
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

              {/* 证件号（仅身份证件） */}
              {item.masked_document_number && (
                <div style={{
                  padding: '18px', borderRadius: '16px',
                  background: 'rgba(196,163,90,0.04)', border: '1px solid rgba(196,163,90,0.12)',
                }}>
                  <p style={{ fontSize: '11px', fontWeight: 700, color: '#8a7040', marginBottom: '8px' }}>
                    <i className="fas fa-shield-halved mr-1"></i> 掩码证件号
                  </p>
                  <p style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text)', fontFamily: 'monospace', letterSpacing: '0.05em' }}>
                    {item.masked_document_number}
                  </p>
                </div>
              )}

              {/* 时间戳 */}
              <div style={{ fontSize: '12px', color: 'var(--muted)', display: 'flex', gap: '16px' }}>
                <span>发布于 {new Date(item.created_at).toLocaleString('zh-CN')}</span>
                <span>更新于 {new Date(item.updated_at).toLocaleString('zh-CN')}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
