import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { mockApi } from '@/api/mock'
import { useAuth } from '@/features/auth/hooks'
import { StatusBadge } from '@/components/StatusBadge'

export function HomePage() {
  const { user } = useAuth()

  const { data: recentItems = [] } = useQuery({ queryKey: ['recent-items'], queryFn: () => mockApi.getRecentItems(5) })
  const { data: lostItems = [] } = useQuery({ queryKey: ['lost-items'], queryFn: () => mockApi.getMyLostItems() })
  const { data: foundItems = [] } = useQuery({ queryKey: ['found-items'], queryFn: () => mockApi.getMyFoundItems() })

  // 数据概览统计
  const stats = {
    lostCount: lostItems.length,
    foundCount: foundItems.length,
    matchedCount: [...lostItems, ...foundItems].filter((i) => i.status === 'PUBLISHED').length,
    totalCount: lostItems.length + foundItems.length,
  }

  return (
    <div className="page-shell">
      {/* Hero */}
      <section className="hero-section">
        <div className="hero-left glass-card">
          <div className="hero-badge">
            <i className="fas fa-leaf mr-1.5"></i> 校园失物招领平台
          </div>
          <h1>物归原主{'\n'}屿过天晴</h1>
          <p>在这里可以快速发布寻物或招领信息，系统通过 AI 语义匹配和隐藏特征核验，让每一条记录都更容易被看见。</p>
          <div className="hero-actions">
            <Link to="/lost/new" className="hero-btn primary">
              <i className="fas fa-box-open mr-1.5"></i> 我要寻物
            </Link>
            <Link to="/found/new" className="hero-btn secondary">
              <i className="fas fa-hand-holding-heart mr-1.5"></i> 我要招领
            </Link>
          </div>
        </div>

        {/* 数据概览面板 */}
        <div className="hero-panel glass-card">
          <div className="hero-panel-title">数据概览</div>
          <div className="hero-features">
            {[
              { icon: 'fa-box-open', title: `${stats.lostCount}`, desc: '寻物记录', bg: 'rgba(107,139,164,0.1)', color: '#4a6b82' },
              { icon: 'fa-hand-holding-heart', title: `${stats.foundCount}`, desc: '招领记录', bg: 'rgba(107,158,122,0.1)', color: '#4a7a5a' },
              { icon: 'fa-link', title: `${stats.matchedCount}`, desc: '已匹配', bg: 'rgba(139,123,176,0.1)', color: '#6b5b90' },
              { icon: 'fa-database', title: `${stats.totalCount}`, desc: '总记录数', bg: 'rgba(196,163,90,0.1)', color: '#8a7040' },
            ].map((item) => (
              <div key={item.desc} className="hero-feature-item">
                <div className="hero-feature-icon" style={{ background: item.bg }}>
                  <i className={`fas ${item.icon} text-sm`} style={{ color: item.color }}></i>
                </div>
                <div className="hero-feature-text">
                  <div className="feature-title">{item.title}</div>
                  <div className="feature-desc">{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 核心功能 */}
      <section className="page-section">
        <div className="section-head">
          <div>
            <h2>核心功能</h2>
            <p>寻物招领，一站完成。</p>
          </div>
        </div>
        <div className="function-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
          {[
            { icon: 'fa-box-open', title: '我要寻物', desc: '快速登记丢失信息，AI 智能匹配 + 安全核验，帮你高效寻回失物。', link: '/lost/new', color: '#6b8ba4', deepColor: '#4a6b82', bgGrad: 'linear-gradient(135deg, rgba(232, 240, 248, 0.98) 0%, rgba(238, 244, 250, 0.98) 100%)' },
            { icon: 'fa-hand-holding-heart', title: '我要招领', desc: '拾到物品后发布信息，AI 自动匹配失主，帮助物品更快回到主人身边。', link: '/found/new', color: '#6b9e7a', deepColor: '#4a7a5a', bgGrad: 'linear-gradient(135deg, rgba(232, 245, 236, 0.98) 0%, rgba(238, 248, 240, 0.98) 100%)' },
          ].map((card) => (
            <Link key={card.title} to={card.link} className="function-card" style={{ background: card.bgGrad, borderTopColor: card.color }}>
              <div className="card-icon-wrap" style={{ color: card.deepColor }}>
                <i className={`fas ${card.icon} text-lg`}></i>
              </div>
              <div className="card-title" style={{ color: card.deepColor }}>{card.title}</div>
              <div className="card-desc">{card.desc}</div>
              <div style={{ marginTop: '14px', fontSize: '12px', color: card.color, fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                进入 <i className="fas fa-arrow-right text-[10px]"></i>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* 最新动态 & 快速入口 */}
      <section className="page-section">
        <div className="preview-grid">
          <div className="preview-card glass-card">
            <div className="section-head compact">
              <h2>最新动态</h2>
            </div>
            <div className="item-list">
              {recentItems.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <i className="fas fa-inbox" style={{ fontSize: '28px', color: '#b8c8d8', marginBottom: '8px', display: 'block' }}></i>
                  <p style={{ fontSize: '13px', color: 'var(--muted)' }}>暂无记录，点击上方卡片开始发布</p>
                </div>
              ) : (
                recentItems.map((item) => (
                  <Link key={item.id} to={item.kind === 'LOST' ? `/lost/${item.id}` : `/found/${item.id}`} className="list-item">
                    <div className="list-item-head">
                      <span className="list-item-title">{item.name_public}</span>
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
                      {item.kind === 'LOST' ? '丢失于' : '拾得于'} {item.location_public} · {item.event_time_public}
                    </div>
                  </Link>
                ))
              )}
            </div>
          </div>

          <div className="preview-card glass-card">
            <div className="section-head compact">
              <h2>快速入口</h2>
            </div>
            <div className="item-list">
              {[
                { icon: 'fa-bed', title: '宿舍区', desc: '查看该区域招领信息', color: '#c4a35a', location: '宿舍区' },
                { icon: 'fa-utensils', title: '食堂', desc: '查看该区域招领信息', color: '#6b9e7a', location: '食堂' },
                { icon: 'fa-chalkboard', title: '教学楼', desc: '查看该区域招领信息', color: '#6b8ba4', location: '教学楼' },
                { icon: 'fa-flask', title: '科教楼', desc: '查看该区域招领信息', color: '#8b7bb0', location: '科教楼' },
                { icon: 'fa-book', title: '图书馆', desc: '查看该区域招领信息', color: '#5a8a9a', location: '图书馆' },
              ].map((place) => (
                <Link key={place.location} to={`/location/${encodeURIComponent(place.location)}`} className="list-item">
                  <div className="list-item-head">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '32px', height: '32px', borderRadius: '10px', background: `${place.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <i className={`fas ${place.icon} text-xs`} style={{ color: place.color }}></i>
                      </div>
                      <span className="list-item-title" style={{ fontSize: '15px' }}>{place.title}</span>
                    </div>
                    <span style={{ fontSize: '12px', color: 'var(--muted)' }}>{place.desc}</span>
                  </div>
                </Link>
              ))}
            </div>

            <div></div>
          </div>
        </div>
      </section>

      <footer className="footer" style={{ padding: '0 24px 20px' }}>
        <div>
          <div className="footer-title">物屿</div>
          <div className="footer-desc">物归原主，屿过天晴</div>
        </div>
        <div className="footer-links">
          <Link to="/">首页</Link>
          <Link to="/found/new">招领</Link>
          <Link to="/lost/new">寻物</Link>
          <Link to="/records">我的记录</Link>
        </div>
      </footer>
    </div>
  )
}
