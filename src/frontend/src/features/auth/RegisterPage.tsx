import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useRegister } from './hooks'

export function RegisterPage() {
  const [form, setForm] = useState({ username: '', email: '', password: '', confirmPassword: '' })
  const registerMutation = useRegister()

  const handleChange = (field: string, value: string) => setForm((prev) => ({ ...prev, [field]: value }))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.username.trim() || !form.email.trim() || form.password.length < 8) return
    if (form.password !== form.confirmPassword) return
    registerMutation.mutate({ username: form.username, email: form.email, password: form.password })
  }

  const passwordsMatch = form.password === form.confirmPassword || form.confirmPassword === ''

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(180deg, #f4f7fa 0%, #eef3f8 48%, #f2f6fa 100%)' }}>
      <div className="site-bg site-bg-1"></div>
      <div className="site-bg site-bg-2"></div>

      <div style={{ position: 'relative', zIndex: 1, display: 'flex', minHeight: '100vh' }}>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px' }}>
          <div style={{ maxWidth: '480px' }}>
            <div className="brand-link" style={{ marginBottom: '32px' }}>
              <div style={{
                width: '48px', height: '48px', borderRadius: '16px',
                background: 'linear-gradient(135deg, #6b9e7a 0%, #4a7a5a 100%)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 6px 16px rgba(107,158,122,0.3)'
              }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="rgba(255,255,255,0.15)"/>
                  <path d="M7 14.5c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
                  <path d="M9 15c0-1.7 1.3-3 3-3s3 1.3 3 3" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
                  <circle cx="12" cy="16" r="1.5" fill="white"/>
                  <path d="M12 4v3M8.5 5.5l1.5 2M15.5 5.5l-1.5 2" stroke="white" strokeWidth="1.2" strokeLinecap="round"/>
                </svg>
              </div>
              <div>
                <div className="brand-name" style={{ fontSize: '26px' }}>物屿</div>
                <div className="slogan-text">物归原主，屿过天晴</div>
              </div>
            </div>

            <div className="hero-badge"><i className="fas fa-user-plus mr-1.5"></i> 新用户注册</div>
            <h1 style={{ fontSize: '38px', lineHeight: 1.2, color: 'var(--text)', marginBottom: '16px', letterSpacing: '-0.03em', whiteSpace: 'pre-line' }}>
              加入校园{'\n'}失物招领网络
            </h1>
            <p style={{ fontSize: '16px', lineHeight: 1.8, color: 'var(--muted)' }}>
              注册账号后即可发布失物或招领信息，系统将通过 AI 智能匹配帮助物品回到主人身边。
            </p>
          </div>
        </div>

        <div style={{ width: '480px', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>
          <div className="glass-card" style={{ width: '100%', maxWidth: '380px', padding: '36px 32px', borderRadius: '28px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text)', marginBottom: '6px' }}>创建账号</h2>
            <p style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '24px' }}>注册后即可发布失物或招领信息</p>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div><label className="form-label">用户名 <span style={{ color: 'var(--danger)' }}>*</span></label><input type="text" placeholder="请输入用户名" value={form.username} onChange={(e) => handleChange('username', e.target.value)} className="form-input" required /></div>
              <div><label className="form-label">邮箱 <span style={{ color: 'var(--danger)' }}>*</span></label><input type="email" placeholder="请输入邮箱" value={form.email} onChange={(e) => handleChange('email', e.target.value)} className="form-input" required /></div>
              <div><label className="form-label">密码 <span style={{ color: 'var(--danger)' }}>*</span></label><input type="password" placeholder="请设置密码（至少8位）" value={form.password} onChange={(e) => handleChange('password', e.target.value)} className="form-input" required minLength={8} /></div>
              <div>
                <label className="form-label">确认密码 <span style={{ color: 'var(--danger)' }}>*</span></label>
                <input type="password" placeholder="请再次输入密码" value={form.confirmPassword} onChange={(e) => handleChange('confirmPassword', e.target.value)} className="form-input" style={!passwordsMatch ? { borderColor: 'var(--danger)' } : undefined} required />
                {!passwordsMatch && <p style={{ fontSize: '12px', color: 'var(--danger)', marginTop: '4px' }}>两次输入的密码不一致</p>}
              </div>

              {registerMutation.isError && (
                <div className="callout callout-warning" style={{ fontSize: '13px' }}>
                  <i className="fas fa-triangle-exclamation mt-0.5 text-xs"></i><span>注册失败，请稍后重试</span>
                </div>
              )}

              <button type="submit" disabled={registerMutation.isPending || !form.username.trim() || !form.email.trim() || form.password.length < 8 || !passwordsMatch} className="btn-main primary w-full" style={{ marginTop: '4px' }}>
                {registerMutation.isPending ? <><i className="fas fa-spinner fa-spin text-xs"></i> 注册中...</> : '注册'}
              </button>
            </form>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '18px 0' }}>
              <div style={{ flex: 1, height: '1px', background: 'var(--line)' }}></div>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>或</span>
              <div style={{ flex: 1, height: '1px', background: 'var(--line)' }}></div>
            </div>

            <div style={{ textAlign: 'center' }}>
              <span style={{ fontSize: '14px', color: 'var(--muted)' }}>已有账号？</span>
              <Link to="/login" style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary)', marginLeft: '4px' }}>立即登录</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
