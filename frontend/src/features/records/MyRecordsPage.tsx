import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { recordsApi } from '@/api/records'
import { claimsApi } from '@/api/claims'
import { StatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { useRef, useState } from 'react'
import type { ItemRecordPublic } from '@/api/types'

function LostRecordCard({ item }: { item: ItemRecordPublic }) {
  return (
    <Link to={`/lost/${item.id}`} className="list-item">
      <div className="list-item-head">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{
            padding: '3px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
            background: 'rgba(107,139,164,0.1)', color: '#4a6b82',
          }}>寻物</span>
          <span className="list-item-title">{item.name_public ?? '未命名物品'}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {item.status === 'PUBLISHED' && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              padding: '2px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
              background: 'rgba(107,139,164,0.1)', color: '#4a6b82',
            }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#6b8ba4' }}></span>
              寻物中
            </span>
          )}
          {item.status === 'PENDING_HANDOFF' && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              padding: '2px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
              background: 'rgba(107,158,122,0.1)', color: '#4a7a5a',
            }}>
              <i className="fas fa-link text-[9px]"></i>
              已匹配
            </span>
          )}
          {item.status === 'CLAIMED' && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              padding: '2px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
              background: 'rgba(107,158,122,0.15)', color: '#3a6a4a',
            }}>
              <i className="fas fa-check-circle text-[9px]"></i>
              已找回
            </span>
          )}
          <StatusBadge status={item.status} />
        </div>
      </div>
      <div className="list-item-meta">
        <span>{item.description_public}</span>
        <span style={{ display: 'block', marginTop: '4px' }}>
          丢失于 {item.location_public} · {item.event_time_public}
        </span>
      </div>
      {item.status === 'PUBLISHED' && (
        <div style={{ marginTop: '10px' }}>
          <span style={{
            fontSize: '12px', color: '#4a6b82', fontWeight: 600,
            display: 'inline-flex', alignItems: 'center', gap: '4px',
          }}>
            <i className="fas fa-magnifying-glass text-[10px]"></i> 查看匹配结果
          </span>
        </div>
      )}
      {item.status === 'PENDING_HANDOFF' && (
        <div style={{ marginTop: '10px' }}>
          <span style={{
            fontSize: '12px', color: '#4a7a5a', fontWeight: 600,
            display: 'inline-flex', alignItems: 'center', gap: '4px',
          }}>
            <i className="fas fa-handshake text-[10px]"></i> 已有匹配，请前往交接
          </span>
        </div>
      )}
    </Link>
  )
}

function FoundRecordCard({ item }: { item: ItemRecordPublic }) {
  const queryClient = useQueryClient()
  const [confirming, setConfirming] = useState(false)
  const idempotencyKey = useRef<string | null>(null)

  const pickupMutation = useMutation({
    mutationFn: () => {
      if (!item.claim_id) throw new Error('交接申请尚未就绪')
      idempotencyKey.current ??= crypto.randomUUID()
      return claimsApi.completeHandoff(item.claim_id, idempotencyKey.current)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['records', 'mine'] })
      void queryClient.invalidateQueries({ queryKey: ['records', 'found', item.id] })
      idempotencyKey.current = null
      setConfirming(false)
    },
  })

  return (
    <div className="list-item">
      <Link to={`/found/${item.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}>
        <div className="list-item-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{
              padding: '3px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
              background: 'rgba(107,158,122,0.1)', color: '#4a7a5a',
            }}>招领</span>
            <span className="list-item-title">{item.name_public ?? '未命名物品'}</span>
          </div>
          <StatusBadge status={item.status} />
        </div>
        <div className="list-item-meta">
          <span>{item.description_public}</span>
          <span style={{ display: 'block', marginTop: '4px' }}>
            拾得于 {item.location_public} · {item.event_time_public}
          </span>
        </div>
      </Link>

      {/* 待交接：提示有认领申请 */}
      {item.status === 'PENDING_HANDOFF' && (
        <div style={{
          marginTop: '12px', padding: '12px 16px', borderRadius: '14px',
          background: 'rgba(107,158,122,0.06)', border: '1px solid rgba(107,158,122,0.15)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <i className="fas fa-handshake text-sm" style={{ color: '#4a7a5a' }}></i>
            <div>
              <p style={{ fontSize: '13px', fontWeight: 700, color: '#3a6a4a' }}>有人认领了这件物品</p>
              <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>确认物品已被取走后点击右侧按钮</p>
            </div>
          </div>
          {!item.claim_id ? (
            <span style={{ fontSize: '12px', color: 'var(--muted)' }}>交接信息处理中</span>
          ) : confirming ? (
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => pickupMutation.mutate()}
                disabled={pickupMutation.isPending}
                style={{
                  padding: '8px 16px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                  background: 'linear-gradient(135deg, #6b9e7a 0%, #4a7a5a 100%)',
                  color: '#fff', fontSize: '12px', fontWeight: 700,
                }}
              >
                {pickupMutation.isPending ? '确认中...' : '确认已取走'}
              </button>
              <button
                disabled={pickupMutation.isPending}
                onClick={() => {
                  if (pickupMutation.isPending) return
                  setConfirming(false)
                }}
                style={{
                  padding: '8px 12px', borderRadius: '10px', border: 'none', cursor: pickupMutation.isPending ? 'not-allowed' : 'pointer',
                  background: 'rgba(148,163,184,0.1)', color: 'var(--muted)', fontSize: '12px',
                }}
              >
                取消
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirming(true)}
              style={{
                padding: '8px 16px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-deep) 100%)',
                color: '#fff', fontSize: '12px', fontWeight: 700,
                boxShadow: '0 4px 12px rgba(107,139,164,0.2)',
              }}
            >
              <i className="fas fa-check mr-1"></i> 确认交接
            </button>
          )}
        </div>
      )}

      {pickupMutation.isError && (
        <p style={{ marginTop: '8px', fontSize: '12px', color: 'var(--danger)' }}>确认交接失败，请重试</p>
      )}

      {/* 已认领 */}
      {item.status === 'CLAIMED' && (
        <div style={{
          marginTop: '12px', padding: '10px 16px', borderRadius: '14px',
          background: 'rgba(107,158,122,0.06)', border: '1px solid rgba(107,158,122,0.1)',
          fontSize: '12px', color: '#4a7a5a', display: 'flex', alignItems: 'center', gap: '8px',
        }}>
          <i className="fas fa-check-circle"></i>
          物品已完成交接
        </div>
      )}
    </div>
  )
}

const PAGE_SIZE = 5

export function MyRecordsPage() {
  const [filter, setFilter] = useState<'all' | 'LOST' | 'FOUND'>('all')
  const [page, setPage] = useState(1)

  const kind = filter === 'all' ? undefined : filter
  const recordsQuery = useQuery({
    queryKey: ['records', 'mine', kind ?? 'all', page, PAGE_SIZE],
    queryFn: () => recordsApi.mine(kind, page, PAGE_SIZE),
  })
  const summaryQuery = useQuery({ queryKey: ['records', 'summary'], queryFn: () => recordsApi.summary() })
  const records = recordsQuery.data?.items ?? []
  const isLoading = recordsQuery.isLoading

  const total = recordsQuery.data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)
  const summary = summaryQuery.data

  // 切换筛选时重置到第1页
  const handleFilterChange = (key: 'all' | 'LOST' | 'FOUND') => {
    setFilter(key)
    setPage(1)
  }

  return (
    <div className="page-shell">
      <div style={{ maxWidth: '1200px', margin: '20px auto 0' }}>
        <Link to="/" style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px',
          fontSize: '13px', color: 'var(--muted)', marginBottom: '16px', textDecoration: 'none',
        }}>
          <i className="fas fa-arrow-left text-[11px]"></i> 返回首页
        </Link>
        <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.02em' }}>我的记录</h1>
        <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>查看我发布的寻物和招领信息</p>
      </div>

      {/* 筛选标签 */}
      <div style={{ maxWidth: '1200px', margin: '20px auto', display: 'flex', gap: '8px' }}>
        {[
          { key: 'all' as const, label: `全部 (${summary?.total_count ?? '-'})` },
          { key: 'LOST' as const, label: `寻物 (${summary?.lost_count ?? '-'})` },
          { key: 'FOUND' as const, label: `招领 (${summary?.found_count ?? '-'})` },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => handleFilterChange(tab.key)}
            style={{
              padding: '8px 18px', borderRadius: '999px', border: 'none', cursor: 'pointer', fontSize: '13px', fontWeight: filter === tab.key ? 700 : 500,
              background: filter === tab.key ? 'linear-gradient(135deg, var(--primary) 0%, var(--primary-deep) 100%)' : 'rgba(255,255,255,0.88)',
              color: filter === tab.key ? '#fff' : 'var(--text)',
              boxShadow: filter === tab.key ? '0 4px 12px rgba(107,139,164,0.2)' : 'none',
            }}
          >
            {tab.label}
          </button>
        ))}
        {summaryQuery.isLoading && <span style={{ alignSelf: 'center', fontSize: '12px', color: 'var(--muted)' }}>统计加载中</span>}
        {summaryQuery.isError && (
          <button type="button" onClick={() => void summaryQuery.refetch()} style={{ border: 'none', background: 'none', fontSize: '12px', color: 'var(--danger)', cursor: 'pointer' }}>
            统计加载失败，重试
          </button>
        )}
      </div>

      {/* 记录列表 */}
      <section style={{ maxWidth: '1200px', margin: '0 auto 40px' }}>
        <div className="glass-card" style={{ padding: '24px', borderRadius: '24px' }}>
          <div className="item-list">
            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '60px 0' }}>
                <i className="fas fa-spinner fa-spin text-xl" style={{ color: 'var(--primary)' }}></i>
              </div>
            ) : recordsQuery.isError ? (
              <ErrorState message="我的记录加载失败" onRetry={() => void recordsQuery.refetch()} />
            ) : records.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '60px 0' }}>
                <i className="fas fa-inbox" style={{ fontSize: '32px', color: '#b8c8d8', marginBottom: '12px', display: 'block' }}></i>
                <p style={{ fontSize: '14px', color: 'var(--muted)' }}>暂无记录</p>
              </div>
            ) : (
              records.map((item) =>
                item.kind === 'LOST' ? (
                  <LostRecordCard key={item.id} item={item} />
                ) : (
                  <FoundRecordCard key={item.id} item={item} />
                )
              )
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
