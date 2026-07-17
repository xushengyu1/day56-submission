import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { mockApi } from '@/api/mock'

export function AdminReviewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [decision, setDecision] = useState<'approve' | 'reject'>('approve')
  const [reason, setReason] = useState('')

  const { data: review } = useQuery({
    queryKey: ['admin', 'review', id],
    queryFn: () => mockApi.getReviewDetail(id || ''),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim()) return
    navigate('/admin')
  }

  if (!review) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <p style={{ color: 'var(--muted)' }}>复核记录不存在</p>
      </div>
    )
  }

  return (
    <div>
      {/* 返回按钮 */}
      <Link to="/admin" style={{
        display: 'inline-flex', alignItems: 'center', gap: '6px',
        fontSize: '13px', color: 'var(--muted)', marginBottom: '16px', textDecoration: 'none'
      }}>
        <i className="fas fa-arrow-left text-[11px]"></i> 返回队列
      </Link>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '20px' }}>
        {/* 左侧：核验信息 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* 物品公开信息 */}
          <div className="glass-card" style={{ padding: '24px', borderRadius: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <i className="fas fa-cube" style={{ color: 'var(--primary)' }}></i> 物品公开信息
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '20px' }}>
              <div style={{
                width: '100%', height: '160px', borderRadius: '16px', overflow: 'hidden',
                background: 'var(--color-neutral-100)'
              }}>
                <img src="https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=200&h=160&fit=crop"
                  alt="物品图片" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>
              <div>
                <p style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text)' }}>黑色折叠伞</p>
                <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
                  <span style={{
                    padding: '4px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: 700,
                    background: 'rgba(107,139,164,0.1)', color: 'var(--primary-deep)'
                  }}>其他物品</span>
                  <span style={{
                    padding: '4px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: 700,
                    background: 'rgba(184,92,92,0.1)', color: 'var(--danger)'
                  }}>多人认领</span>
                </div>
                <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--muted)' }}>
                    <i className="fas fa-clock w-4 text-center text-[11px]"></i>
                    <span>7 月 16 日 上午 10:30</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--muted)' }}>
                    <i className="fas fa-location-dot w-4 text-center text-[11px]"></i>
                    <span>教学楼</span>
                  </div>
                </div>
              </div>
            </div>
            <div style={{
              marginTop: '16px', padding: '14px', borderRadius: '14px',
              background: 'rgba(107,139,164,0.04)', border: '1px solid rgba(107,139,164,0.08)'
            }}>
              <p style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '6px' }}>拾得者信息</p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '32px', height: '32px', borderRadius: '50%',
                  background: 'linear-gradient(135deg, #6b9e7a 0%, #4a7a5a 100%)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'white', fontSize: '12px', fontWeight: 700
                }}>李</div>
                <div>
                  <p style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text)' }}>李同学</p>
                  <p style={{ fontSize: '11px', color: 'var(--muted)' }}>发布于 7月16日 11:00</p>
                </div>
              </div>
            </div>
          </div>

          {/* 认领申请人对比 */}
          <div className="glass-card" style={{ padding: '24px', borderRadius: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text)', marginBottom: '16px' }}>认领申请人</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              {/* 张同学 */}
              <div style={{
                padding: '18px', borderRadius: '18px',
                border: '2px solid rgba(107,158,122,0.3)',
                background: 'rgba(107,158,122,0.04)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '50%',
                    background: 'linear-gradient(135deg, #6b8ba4 0%, #4a6b82 100%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', fontSize: '13px', fontWeight: 700
                  }}>张</div>
                  <div>
                    <p style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)' }}>张同学</p>
                    <p style={{ fontSize: '11px', color: 'var(--muted)' }}>7月16日 14:30</p>
                  </div>
                </div>
                <div style={{
                  padding: '10px', borderRadius: '12px', background: 'rgba(248,250,252,0.8)',
                  marginBottom: '10px'
                }}>
                  <p style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>隐藏特征回答</p>
                  <p style={{ fontSize: '13px', color: 'var(--text)' }}>"伞套内侧有 SZY 字样"</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <i className="fas fa-check-circle" style={{ color: 'var(--success)', fontSize: '13px' }}></i>
                  <span style={{ fontSize: '12px', color: 'var(--success)', fontWeight: 600 }}>回答匹配</span>
                </div>
              </div>

              {/* 孙同学 */}
              <div style={{
                padding: '18px', borderRadius: '18px',
                border: '1px solid rgba(226,232,240,0.75)',
                background: 'rgba(255,255,255,0.5)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '50%',
                    background: 'linear-gradient(135deg, #b8c8d8 0%, #7a8e9e 100%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', fontSize: '13px', fontWeight: 700
                  }}>孙</div>
                  <div>
                    <p style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)' }}>孙同学</p>
                    <p style={{ fontSize: '11px', color: 'var(--muted)' }}>7月16日 15:10</p>
                  </div>
                </div>
                <div style={{
                  padding: '10px', borderRadius: '12px', background: 'rgba(248,250,252,0.8)',
                  marginBottom: '10px'
                }}>
                  <p style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>隐藏特征回答</p>
                  <p style={{ fontSize: '13px', color: 'var(--text)' }}>"伞套上有字母标记，不太记得了"</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <i className="fas fa-question-circle" style={{ color: 'var(--warning)', fontSize: '13px' }}></i>
                  <span style={{ fontSize: '12px', color: 'var(--warning)', fontWeight: 600 }}>部分匹配</span>
                </div>
              </div>
            </div>
          </div>

          {/* 标准答案 */}
          <div className="glass-card" style={{ padding: '24px', borderRadius: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <i className="fas fa-key" style={{ color: 'var(--warning)' }}></i> 拾得者隐藏特征（标准答案）
            </h3>
            <div style={{
              padding: '16px', borderRadius: '14px',
              background: 'rgba(196,163,90,0.06)', border: '1px solid rgba(196,163,90,0.12)'
            }}>
              <p style={{ fontSize: '14px', color: '#6a5a2a', lineHeight: 1.8 }}>
                伞套内侧用黑色笔写着 SZY 三个字母；伞的第三根骨架有一小段用白色胶带缠绕修复过。
              </p>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <i className="fas fa-shield-halved text-[10px]"></i>仅管理员复核可见
            </p>
          </div>

          {/* AI 分析 */}
          <div className="glass-card" style={{ padding: '24px', borderRadius: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <i className="fas fa-robot" style={{ color: 'var(--primary)' }}></i> AI 分析结果
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{
                padding: '14px', borderRadius: '14px',
                background: 'rgba(107,158,122,0.06)', border: '1px solid rgba(107,158,122,0.12)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <div style={{
                    width: '24px', height: '24px', borderRadius: '50%',
                    background: 'linear-gradient(135deg, #6b9e7a 0%, #4a7a5a 100%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', fontSize: '10px', fontWeight: 700
                  }}>张</div>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: '#3a6a4a' }}>张同学</span>
                </div>
                <p style={{ fontSize: '12px', color: '#4a7a5a', lineHeight: 1.6 }}>
                  回答准确描述了 SZY 标记，置信度 <strong>0.94</strong>。
                </p>
              </div>
              <div style={{
                padding: '14px', borderRadius: '14px',
                background: 'rgba(196,163,90,0.06)', border: '1px solid rgba(196,163,90,0.12)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <div style={{
                    width: '24px', height: '24px', borderRadius: '50%',
                    background: 'linear-gradient(135deg, #b8c8d8 0%, #7a8e9e 100%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', fontSize: '10px', fontWeight: 700
                  }}>孙</div>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: '#6a5a2a' }}>孙同学</span>
                </div>
                <p style={{ fontSize: '12px', color: '#8a7040', lineHeight: 1.6 }}>
                  回答提到字母标记但未准确说明内容，置信度 <strong>0.62</strong>。
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 右侧：操作区 */}
        <div>
          <div className="glass-card" style={{ padding: '24px', borderRadius: '24px', position: 'sticky', top: '80px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text)', marginBottom: '18px' }}>复核决定</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
              <label style={{ cursor: 'pointer' }}>
                <input type="radio" name="decision" checked={decision === 'approve'} onChange={() => setDecision('approve')} style={{ display: 'none' }} />
                <div style={{
                  padding: '16px', borderRadius: '16px',
                  border: decision === 'approve' ? '2px solid var(--success)' : '1px solid rgba(226,232,240,0.75)',
                  background: decision === 'approve' ? 'rgba(107,158,122,0.06)' : 'rgba(255,255,255,0.5)',
                  transition: 'all 0.2s ease'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '36px', height: '36px', borderRadius: '12px',
                      background: decision === 'approve' ? 'rgba(107,158,122,0.15)' : 'rgba(148,163,184,0.1)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                      <i className="fas fa-check text-sm" style={{ color: decision === 'approve' ? 'var(--success)' : 'var(--muted)' }}></i>
                    </div>
                    <div>
                      <p style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)' }}>确认张同学认领</p>
                      <p style={{ fontSize: '11px', color: 'var(--muted)' }}>进入待交接状态</p>
                    </div>
                  </div>
                </div>
              </label>
              <label style={{ cursor: 'pointer' }}>
                <input type="radio" name="decision" checked={decision === 'reject'} onChange={() => setDecision('reject')} style={{ display: 'none' }} />
                <div style={{
                  padding: '16px', borderRadius: '16px',
                  border: decision === 'reject' ? '2px solid var(--danger)' : '1px solid rgba(226,232,240,0.75)',
                  background: decision === 'reject' ? 'rgba(184,92,92,0.06)' : 'rgba(255,255,255,0.5)',
                  transition: 'all 0.2s ease'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '36px', height: '36px', borderRadius: '12px',
                      background: decision === 'reject' ? 'rgba(184,92,92,0.15)' : 'rgba(148,163,184,0.1)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                      <i className="fas fa-xmark text-sm" style={{ color: decision === 'reject' ? 'var(--danger)' : 'var(--muted)' }}></i>
                    </div>
                    <div>
                      <p style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)' }}>驳回全部认领</p>
                      <p style={{ fontSize: '11px', color: 'var(--muted)' }}>保留招领记录</p>
                    </div>
                  </div>
                </div>
              </label>
            </div>

            <form onSubmit={handleSubmit}>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: 'var(--text)', marginBottom: '8px' }}>
                处理理由 <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <textarea
                rows={5}
                placeholder="请填写审核理由..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="form-textarea"
                style={{ minHeight: '100px' }}
              />
              <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <button type="submit" disabled={!reason.trim()} className="submit-btn" style={{ width: '100%', gridColumn: 'unset', justifyContent: 'center' }}>
                  <i className="fas fa-paper-plane"></i> 提交决定
                </button>
                <Link to="/admin" className="hero-btn secondary" style={{ width: '100%', justifyContent: 'center', textAlign: 'center' }}>
                  返回队列
                </Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
