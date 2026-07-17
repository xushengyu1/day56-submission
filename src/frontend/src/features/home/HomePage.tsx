import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { recordsApi } from '@/api/records'
import { StatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import ArrowRightOutlined from '@ant-design/icons/ArrowRightOutlined'
import BookOutlined from '@ant-design/icons/BookOutlined'
import CoffeeOutlined from '@ant-design/icons/CoffeeOutlined'
import DatabaseOutlined from '@ant-design/icons/DatabaseOutlined'
import ExperimentOutlined from '@ant-design/icons/ExperimentOutlined'
import GiftOutlined from '@ant-design/icons/GiftOutlined'
import HomeOutlined from '@ant-design/icons/HomeOutlined'
import InboxOutlined from '@ant-design/icons/InboxOutlined'
import LinkOutlined from '@ant-design/icons/LinkOutlined'
import LoadingOutlined from '@ant-design/icons/LoadingOutlined'
import ReadOutlined from '@ant-design/icons/ReadOutlined'
import ReloadOutlined from '@ant-design/icons/ReloadOutlined'
import SafetyOutlined from '@ant-design/icons/SafetyOutlined'
import SearchOutlined from '@ant-design/icons/SearchOutlined'
import WarningOutlined from '@ant-design/icons/WarningOutlined'

export function HomePage() {
  const recentQuery = useQuery({ queryKey: ['records', 'recent', 5], queryFn: () => recordsApi.recent(5) })
  const summaryQuery = useQuery({ queryKey: ['records', 'summary'], queryFn: () => recordsApi.summary() })
  const recentItems = recentQuery.data ?? []
  const stats = summaryQuery.data

  return (
    <div className="page-shell">
      {/* Hero */}
      <section className="hero-section">
        <div className="hero-left glass-card">
          <div className="hero-badge">
            <SafetyOutlined aria-hidden="true" className="mr-1.5" /> 校园失物招领平台
          </div>
          <h1>物归原主{'\n'}屿过天晴</h1>
          <p>在这里可以快速发布寻物或招领信息，系统通过 AI 语义匹配和隐藏特征核验，让每一条记录都更容易被看见。</p>
          <div className="hero-actions">
            <Link to="/lost/new" className="hero-btn primary">
              <SearchOutlined aria-hidden="true" /> 我要寻物
            </Link>
            <Link to="/found/new" className="hero-btn secondary">
              <GiftOutlined aria-hidden="true" /> 我要招领
            </Link>
          </div>
        </div>

        {/* 数据概览面板 */}
        <div className="hero-panel glass-card">
          <div className="hero-panel-title">数据概览</div>
          <div className="hero-features">
            {summaryQuery.isLoading ? (
              <div style={{ fontSize: '13px', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <LoadingOutlined aria-hidden="true" spin />统计加载中
              </div>
            ) : summaryQuery.isError ? (
              <div className="callout callout-warning" style={{ fontSize: '13px', justifyContent: 'space-between' }}>
                <span><WarningOutlined aria-hidden="true" className="mr-1.5" />统计加载失败</span>
                <button type="button" onClick={() => void summaryQuery.refetch()} style={{ border: 'none', background: 'none', color: 'inherit', fontWeight: 700, cursor: 'pointer' }}><ReloadOutlined aria-hidden="true" className="mr-1" />重试</button>
              </div>
            ) : stats ? [
              { icon: <SearchOutlined aria-hidden="true" />, title: `${stats.lost_count}`, desc: '寻物记录', bg: 'rgba(107,139,164,0.1)', color: '#4a6b82' },
              { icon: <GiftOutlined aria-hidden="true" />, title: `${stats.found_count}`, desc: '招领记录', bg: 'rgba(107,158,122,0.1)', color: '#4a7a5a' },
              { icon: <LinkOutlined aria-hidden="true" />, title: `${stats.matched_count}`, desc: '已匹配', bg: 'rgba(139,123,176,0.1)', color: '#6b5b90' },
              { icon: <DatabaseOutlined aria-hidden="true" />, title: `${stats.total_count}`, desc: '总记录数', bg: 'rgba(196,163,90,0.1)', color: '#8a7040' },
            ].map((item) => (
              <div key={item.desc} className="hero-feature-item">
                <div className="hero-feature-icon" style={{ background: item.bg }}>
                  <span style={{ color: item.color }}>{item.icon}</span>
                </div>
                <div className="hero-feature-text">
                  <div className="feature-title">{item.title}</div>
                  <div className="feature-desc">{item.desc}</div>
                </div>
              </div>
            )) : null}
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
            { icon: <SearchOutlined aria-hidden="true" />, title: '我要寻物', desc: '快速登记丢失信息，AI 智能匹配 + 安全核验，帮你高效寻回失物。', link: '/lost/new', color: '#6b8ba4', deepColor: '#4a6b82', bgGrad: 'linear-gradient(135deg, rgba(232, 240, 248, 0.98) 0%, rgba(238, 244, 250, 0.98) 100%)' },
            { icon: <GiftOutlined aria-hidden="true" />, title: '我要招领', desc: '拾到物品后发布信息，AI 自动匹配失主，帮助物品更快回到主人身边。', link: '/found/new', color: '#6b9e7a', deepColor: '#4a7a5a', bgGrad: 'linear-gradient(135deg, rgba(232, 245, 236, 0.98) 0%, rgba(238, 248, 240, 0.98) 100%)' },
          ].map((card) => (
            <Link key={card.title} to={card.link} className="function-card" style={{ background: card.bgGrad, borderTopColor: card.color }}>
              <div className="card-icon-wrap" style={{ color: card.deepColor }}>
                {card.icon}
              </div>
              <div className="card-title" style={{ color: card.deepColor }}>{card.title}</div>
              <div className="card-desc">{card.desc}</div>
              <div style={{ marginTop: '14px', fontSize: '12px', color: card.color, fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                进入 <ArrowRightOutlined aria-hidden="true" />
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
              {recentQuery.isLoading ? (
                <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--muted)', fontSize: '13px' }}>
                  <LoadingOutlined aria-hidden="true" spin className="mr-1.5" />最新动态加载中
                </div>
              ) : recentQuery.isError ? (
                <ErrorState message="最新动态加载失败" onRetry={() => void recentQuery.refetch()} />
              ) : recentItems.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <InboxOutlined aria-hidden="true" style={{ fontSize: '28px', color: '#b8c8d8', marginBottom: '8px', display: 'block' }} />
                  <p style={{ fontSize: '13px', color: 'var(--muted)' }}>暂无记录，点击上方卡片开始发布</p>
                </div>
              ) : (
                recentItems.map((item) => (
                  <Link key={item.id} to={item.kind === 'LOST' ? `/lost/${item.id}` : `/found/${item.id}`} className="list-item">
                    <div className="list-item-head">
                      <span className="list-item-title">{item.name_public ?? '未命名物品'}</span>
                      {item.kind === 'LOST' && item.status === 'PUBLISHED' ? (
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
                      {item.kind === 'LOST' ? '丢失于' : '拾得于'} {item.location_public ?? '-'} · {item.event_time_public ?? '-'}
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
                { icon: <HomeOutlined aria-hidden="true" />, title: '宿舍区', desc: '查看该区域招领信息', color: '#c4a35a', location: '宿舍区' },
                { icon: <CoffeeOutlined aria-hidden="true" />, title: '食堂', desc: '查看该区域招领信息', color: '#6b9e7a', location: '食堂' },
                { icon: <ReadOutlined aria-hidden="true" />, title: '教学楼', desc: '查看该区域招领信息', color: '#6b8ba4', location: '教学楼' },
                { icon: <ExperimentOutlined aria-hidden="true" />, title: '科教楼', desc: '查看该区域招领信息', color: '#8b7bb0', location: '科教楼' },
                { icon: <BookOutlined aria-hidden="true" />, title: '图书馆', desc: '查看该区域招领信息', color: '#5a8a9a', location: '图书馆' },
              ].map((place) => (
                <Link key={place.location} to={`/location/${encodeURIComponent(place.location)}`} className="list-item">
                  <div className="list-item-head">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '32px', height: '32px', borderRadius: '10px', background: `${place.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <span style={{ color: place.color }}>{place.icon}</span>
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
