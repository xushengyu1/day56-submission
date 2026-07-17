import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'

export function UnmatchedReviewPage() {
  const { id: lostId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [submitted, setSubmitted] = useState(false)
  const [form, setForm] = useState({
    item_name: '',
    item_description: '',
    location: '',
    time_range: '',
    supplement: '',
  })

  const handleChange = (field: string, value: string) => setForm((prev) => ({ ...prev, [field]: value }))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Mock: 提交后显示成功
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="page-shell">
        <div style={{ maxWidth: '640px', margin: '60px auto', textAlign: 'center' }}>
          <div style={{
            width: '72px', height: '72px', borderRadius: '50%', margin: '0 auto 24px',
            background: 'rgba(107,158,122,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <i className="fas fa-check-circle" style={{ fontSize: '32px', color: '#4a7a5a' }}></i>
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text)', marginBottom: '8px' }}>复核申请已提交</h2>
          <p style={{ fontSize: '14px', color: 'var(--muted)', lineHeight: 1.8, marginBottom: '32px' }}>
            管理员会根据你提供的信息重新检查匹配结果，<br />
            处理结果将在「我的记录」中更新。
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <Link to={`/lost/${lostId}/candidates`} style={{
              padding: '12px 24px', borderRadius: '14px', border: 'none', textDecoration: 'none',
              background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-deep) 100%)',
              color: '#fff', fontWeight: 700, fontSize: '14px', display: 'inline-flex', alignItems: 'center', gap: '8px',
              boxShadow: 'var(--shadow-btn)',
            }}>
              <i className="fas fa-arrow-left text-xs"></i> 返回候选列表
            </Link>
            <Link to="/records" style={{
              padding: '12px 24px', borderRadius: '14px', textDecoration: 'none',
              background: 'rgba(255,255,255,0.88)', color: 'var(--primary-deep)', fontWeight: 700, fontSize: '14px',
              border: '1px solid rgba(107,139,164,0.15)', display: 'inline-flex', alignItems: 'center', gap: '8px',
            }}>
              <i className="fas fa-folder text-xs"></i> 查看我的记录
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page-shell">
      {/* 返回 */}
      <div style={{ maxWidth: '800px', margin: '20px auto 0' }}>
        <Link to={`/lost/${lostId}/candidates`} style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px',
          fontSize: '13px', color: 'var(--muted)', marginBottom: '16px', textDecoration: 'none',
        }}>
          <i className="fas fa-arrow-left text-[11px]"></i> 返回候选列表
        </Link>
        <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.02em' }}>
          <i className="fas fa-flag mr-2" style={{ color: '#6b8ba4' }}></i>
          提交未匹配复核
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '6px', lineHeight: 1.8 }}>
          当前候选中没有找到合适的匹配？请补充物品信息，管理员会根据你提供的描述重新检查已有招领记录。
        </p>
      </div>

      {/* 表单 */}
      <section style={{ maxWidth: '800px', margin: '24px auto 40px' }}>
        <div className="glass-card" style={{ padding: '32px', borderRadius: '24px' }}>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* 物品名称 */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: 'var(--text)', marginBottom: '8px' }}>
                物品名称 <span style={{ color: '#b85c5c' }}>*</span>
              </label>
              <input type="text" placeholder="例如：黑色折叠伞" className="form-input"
                value={form.item_name} onChange={(e) => handleChange('item_name', e.target.value)} required />
            </div>

            {/* 物品描述 */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: 'var(--text)', marginBottom: '8px' }}>
                物品详细描述 <span style={{ color: '#b85c5c' }}>*</span>
              </label>
              <textarea placeholder="请尽量详细描述物品特征，如颜色、品牌、尺寸、特殊标记等，有助于管理员匹配到正确的招领记录。" className="form-textarea"
                style={{ minHeight: '120px' }}
                value={form.item_description} onChange={(e) => handleChange('item_description', e.target.value)} required />
            </div>

            {/* 丢失地点和时间 */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: 'var(--text)', marginBottom: '8px' }}>
                  丢失地点
                </label>
                <input type="text" placeholder="例如：教学楼B区3楼" className="form-input"
                  value={form.location} onChange={(e) => handleChange('location', e.target.value)} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: 'var(--text)', marginBottom: '8px' }}>
                  丢失时间段
                </label>
                <input type="text" placeholder="例如：7月16日上午10点左右" className="form-input"
                  value={form.time_range} onChange={(e) => handleChange('time_range', e.target.value)} />
              </div>
            </div>

            {/* 补充说明 */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: 'var(--text)', marginBottom: '8px' }}>
                补充说明
              </label>
              <textarea placeholder="其他有助于找回物品的信息，例如：在哪个教室丢失的、是否有同行人、物品内部有什么特征等。" className="form-textarea"
                style={{ minHeight: '80px' }}
                value={form.supplement} onChange={(e) => handleChange('supplement', e.target.value)} />
            </div>

            {/* 提示 */}
            <div style={{
              padding: '14px 16px', borderRadius: '14px',
              background: 'rgba(107,139,164,0.04)', border: '1px solid rgba(107,139,164,0.1)',
              fontSize: '12px', color: '#4a6b82', lineHeight: 1.7, display: 'flex', gap: '10px',
            }}>
              <i className="fas fa-circle-info mt-0.5 text-xs"></i>
              <span>提交后，管理员会查看已有招领记录并尝试为你匹配。处理结果将在「我的记录」中更新，届时会通知你。</span>
            </div>

            {/* 按钮 */}
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <Link to={`/lost/${lostId}/candidates`} style={{
                padding: '12px 24px', borderRadius: '14px', textDecoration: 'none',
                background: 'rgba(255,255,255,0.88)', color: 'var(--text)', fontWeight: 600, fontSize: '14px',
                border: '1px solid rgba(107,139,164,0.15)', display: 'inline-flex', alignItems: 'center', gap: '8px',
              }}>
                取消
              </Link>
              <button type="submit" style={{
                padding: '12px 24px', borderRadius: '14px', border: 'none', cursor: 'pointer',
                background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-deep) 100%)',
                color: '#fff', fontWeight: 700, fontSize: '14px', display: 'inline-flex', alignItems: 'center', gap: '8px',
                boxShadow: 'var(--shadow-btn)',
              }}>
                <i className="fas fa-paper-plane text-xs"></i> 提交复核申请
              </button>
            </div>
          </form>
        </div>
      </section>

      <div className="page-slogan">物归原主，屿过天晴</div>
    </div>
  )
}
