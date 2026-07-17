import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { mockApi } from '@/api/mock'
import { StatusBadge } from '@/components/StatusBadge'
import { useState } from 'react'

const LOCATION_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  '宿舍区': { icon: 'fa-bed', color: '#c4a35a', bg: 'rgba(196,163,90,0.1)' },
  '食堂': { icon: 'fa-utensils', color: '#6b9e7a', bg: 'rgba(107,158,122,0.1)' },
  '教学楼': { icon: 'fa-chalkboard', color: '#6b8ba4', bg: 'rgba(107,139,164,0.1)' },
  '科教楼': { icon: 'fa-flask', color: '#8b7bb0', bg: 'rgba(139,123,176,0.1)' },
  '图书馆': { icon: 'fa-book', color: '#5a8a9a', bg: 'rgba(90,138,154,0.1)' },
}

const PAGE_SIZE = 5

export function LocationItemsPage() {
  const { location } = useParams<{ location: string }>()
  const decodedLocation = decodeURIComponent(location || '')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['items', 'location', decodedLocation, page],
    queryFn: () => mockApi.getItemsByLocation(decodedLocation, page, PAGE_SIZE),
  })

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const config = LOCATION_CONFIG[decodedLocation] || { icon: 'fa-map-marker-alt', color: '#7a8e9e', bg: 'rgba(122,142,158,0.1)' }

  return (
    <div className="page-shell">
      {/* 页面标题 */}
      <div style={{ maxWidth: '1200px', margin: '20px auto 0' }}>
        <Link to="/" style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px',
          fontSize: '13px', color: 'var(--muted)', marginBottom: '16px', textDecoration: 'none',
        }}>
          <i className="fas fa-arrow-left text-[11px]"></i> 返回首页
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '14px',
            background: config.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <i className={`fas ${config.icon} text-lg`} style={{ color: config.color }}></i>
          </div>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.02em' }}>{decodedLocation}</h1>
            <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '2px' }}>
              该区域的寻物与招领信息 · 共 {total} 条
            </p>
          </div>
        </div>
      </div>

      {/* 统计 */}
      <div style={{ maxWidth: '1200px', margin: '20px auto', display: 'flex', gap: '12px' }}>
        <div className="glass-card" style={{ padding: '14px 20px', borderRadius: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <i className="fas fa-box-open text-sm" style={{ color: '#4a6b82' }}></i>
          <span style={{ fontSize: '13px', color: 'var(--muted)' }}>寻物</span>
          <span style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text)' }}>
            {items.filter((i) => i.kind === 'LOST').length}
          </span>
        </div>
        <div className="glass-card" style={{ padding: '14px 20px', borderRadius: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <i className="fas fa-hand-holding-heart text-sm" style={{ color: '#4a7a5a' }}></i>
          <span style={{ fontSize: '13px', color: 'var(--muted)' }}>招领</span>
          <span style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text)' }}>
            {items.filter((i) => i.kind === 'FOUND').length}
          </span>
        </div>
      </div>

      {/* 物品列表 */}
      <section style={{ maxWidth: '1200px', margin: '0 auto 40px' }}>
        <div className="glass-card" style={{ padding: '24px', borderRadius: '24px' }}>
          <div className="item-list">
            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '60px 0' }}>
                <i className="fas fa-spinner fa-spin text-xl" style={{ color: 'var(--primary)' }}></i>
              </div>
            ) : items.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '60px 0' }}>
                <i className="fas fa-inbox" style={{ fontSize: '32px', color: '#b8c8d8', marginBottom: '12px', display: 'block' }}></i>
                <p style={{ fontSize: '14px', color: 'var(--muted)' }}>该区域暂无记录</p>
              </div>
            ) : (
              items.map((item) => (
                <Link
                  key={item.id}
                  to={item.kind === 'LOST' ? `/lost/${item.id}` : `/found/${item.id}`}
                  className="list-item"
                >
                  <div className="list-item-head">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{
                        padding: '3px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
                        background: item.kind === 'LOST' ? 'rgba(107,139,164,0.1)' : 'rgba(107,158,122,0.1)',
                        color: item.kind === 'LOST' ? '#4a6b82' : '#4a7a5a',
                      }}>
                        {item.kind === 'LOST' ? '寻物' : '招领'}
                      </span>
                      <span className="list-item-title">{item.name_public}</span>
                    </div>
                    {item.kind === 'LOST' ? (
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: '4px',
                        padding: '2px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
                        background: 'rgba(107,139,164,0.1)', color: '#4a6b82',
                      }}>
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#6b8ba4' }}></span>
                        寻物中
                      </span>
                    ) : (
                      <StatusBadge status={item.status} />
                    )}
                  </div>
                  <div className="list-item-meta">
                    {item.description_public && (
                      <span style={{ display: 'block', marginBottom: '4px' }}>{item.description_public}</span>
                    )}
                    {item.kind === 'LOST' ? '丢失于' : '拾得于'} {item.event_time_public}
                  </div>
                </Link>
              ))
            )}
          </div>

          {/* 分页控件 */}
          {totalPages > 1 && (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              marginTop: '20px', paddingTop: '16px', borderTop: '1px solid rgba(226,232,240,0.5)',
            }}>
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                style={{
                  width: '36px', height: '36px', borderRadius: '10px', border: 'none', cursor: page <= 1 ? 'not-allowed' : 'pointer',
                  background: page <= 1 ? 'rgba(148,163,184,0.1)' : 'rgba(107,139,164,0.1)',
                  color: page <= 1 ? '#b8c8d8' : '#4a6b82', display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}
              >
                <i className="fas fa-chevron-left text-xs"></i>
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  style={{
                    width: '36px', height: '36px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                    background: p === page ? 'linear-gradient(135deg, var(--primary) 0%, var(--primary-deep) 100%)' : 'transparent',
                    color: p === page ? '#fff' : 'var(--muted)', fontWeight: p === page ? 700 : 500, fontSize: '13px',
                  }}
                >
                  {p}
                </button>
              ))}
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                style={{
                  width: '36px', height: '36px', borderRadius: '10px', border: 'none', cursor: page >= totalPages ? 'not-allowed' : 'pointer',
                  background: page >= totalPages ? 'rgba(148,163,184,0.1)' : 'rgba(107,139,164,0.1)',
                  color: page >= totalPages ? '#b8c8d8' : '#4a6b82', display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}
              >
                <i className="fas fa-chevron-right text-xs"></i>
              </button>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
