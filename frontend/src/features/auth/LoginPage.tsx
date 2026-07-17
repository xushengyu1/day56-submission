import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useLogin } from './hooks'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const loginMutation = useLogin()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password.trim()) return
    loginMutation.mutate({ email, password })
  }

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(180deg, #f4f7fa 0%, #eef3f8 48%, #f2f6fa 100%)' }}>
      <div className="site-bg site-bg-1"></div>
      <div className="site-bg site-bg-2"></div>

      <div style={{ position: 'relative', zIndex: 1, display: 'flex', minHeight: '100vh' }}>
        {/* 左侧 */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px' }}>
          <div style={{ maxWidth: '480px' }}>
            {/* Logo */}
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

            <div className="hero-badge">
              <i className="fas fa-leaf mr-1.5"></i> 校园失物招领平台
            </div>
            <h1 style={{ fontSize: '42px', lineHeight: 1.2, color: 'var(--text)', marginBottom: '16px', letterSpacing: '-0.03em', whiteSpace: 'pre-line' }}>
              物归原主{'\n'}屿过天晴
            </h1>
            <p style={{ fontSize: '16px', lineHeight: 1.8, color: 'var(--muted)', marginBottom: '32px' }}>
              上传照片即可自动识别物品特征，通过 AI 智能匹配和隐藏特征核验，在校园场景中高效连接失主与拾物者。
            </p>

            {/* 功能说明 */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {[
                { icon: 'fa-robot', text: 'AI 自动提取物品名称与特征描述' },
                { icon: 'fa-shield-halved', text: '四级数据分类，敏感信息脱敏展示' },
                { icon: 'fa-link', text: '语义匹配 + 隐藏核验，防止冒领' },
              ].map((item) => (
                <div key={item.text} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '32px', height: '32px', borderRadius: '10px',
                    background: 'rgba(107, 139, 164, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <i className={`fas ${item.icon}`} style={{ fontSize: '13px', color: 'var(--primary)' }}></i>
                  </div>
                  <span style={{ fontSize: '14px', color: '#4a5568' }}>{item.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 右侧登录 */}
        <div style={{ width: '480px', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>
          <div className="glass-card" style={{ width: '100%', maxWidth: '380px', padding: '36px 32px', borderRadius: '28px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text)', marginBottom: '6px', letterSpacing: '-0.02em' }}>
              登录账号
            </h2>
            <p style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '28px' }}>
              登录后即可发布或查找失物信息
            </p>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label className="form-label">邮箱</label>
                <div style={{ position: 'relative' }}>
                  <i className="fas fa-envelope" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', fontSize: '13px' }}></i>
                  <input type="email" placeholder="请输入邮箱地址" value={email} onChange={(e) => setEmail(e.target.value)} className="form-input" style={{ paddingLeft: '38px' }} />
                </div>
              </div>

              <div>
                <label className="form-label">密码</label>
                <div style={{ position: 'relative' }}>
                  <i className="fas fa-lock" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', fontSize: '13px' }}></i>
                  <input type={showPassword ? 'text' : 'password'} placeholder="请输入密码" value={password} onChange={(e) => setPassword(e.target.value)} className="form-input" style={{ paddingLeft: '38px', paddingRight: '38px' }} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    style={{ position: 'absolute', right: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer' }}>
                    <i className={`fas ${showPassword ? 'fa-eye-slash' : 'fa-eye'} text-xs`}></i>
                  </button>
                </div>
              </div>

              {loginMutation.isError && (
                <div className="callout callout-warning" style={{ fontSize: '13px' }}>
                  <i className="fas fa-triangle-exclamation mt-0.5 text-xs"></i>
                  <span>邮箱或密码错误，请检查后重试</span>
                </div>
              )}

              <button type="submit" disabled={loginMutation.isPending || !email.trim() || !password.trim()} className="btn-main primary w-full" style={{ marginTop: '4px' }}>
                {loginMutation.isPending ? <><i className="fas fa-spinner fa-spin text-xs"></i> 登录中...</> : '登录'}
              </button>
            </form>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '20px 0' }}>
              <div style={{ flex: 1, height: '1px', background: 'var(--line)' }}></div>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>或</span>
              <div style={{ flex: 1, height: '1px', background: 'var(--line)' }}></div>
            </div>

            <div style={{ textAlign: 'center' }}>
              <span style={{ fontSize: '14px', color: 'var(--muted)' }}>还没有账号？</span>
              <Link to="/register" style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary)', marginLeft: '4px' }}>注册新账号</Link>
            </div>

            <div className="callout callout-info" style={{ marginTop: '20px', fontSize: '12px' }}>
              <i className="fas fa-circle-info text-xs mt-0.5"></i>
              <span>管理员请使用 <strong>admin@campus.edu.cn</strong> 登录</span>
            </div>

            <p style={{ textAlign: 'center', fontSize: '11px', color: '#94a3b8', marginTop: '16px' }}>
              登录即表示同意 <a href="#" style={{ color: 'var(--primary)' }}>服务条款</a> 和 <a href="#" style={{ color: 'var(--primary)' }}>隐私政策</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
