import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth, useLogout } from '@/features/auth/hooks'

export function AdminLayout() {
  const { user } = useAuth()
  const { logout } = useLogout()
  const location = useLocation()

  const menuItems = [
    { path: '/admin', icon: 'fa-inbox', label: '复核队列' },
    { path: '/admin/audit', icon: 'fa-clock-rotate-left', label: '审计日志' },
  ]

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ background: 'var(--bg)' }}>
      {/* 顶部导航 */}
      <header className="header-bar" style={{ margin: '12px auto 0', width: 'calc(100% - 32px)' }}>
        <Link to="/" className="brand-link">
          <div style={{
            width: '36px', height: '36px', borderRadius: '12px',
            background: 'linear-gradient(135deg, #6b8ba4 0%, #4a6b82 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(107,139,164,0.25)'
          }}>
            <i className="fas fa-shield-halved text-white text-sm"></i>
          </div>
          <div>
            <div className="brand-name">管理员工作台</div>
            <div className="slogan-text">物归原主，屿过天晴</div>
          </div>
        </Link>

        <nav className="nav-menu">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <Link key={item.path} to={item.path} className={isActive ? 'active' : ''}>
                <i className={`fas ${item.icon} mr-1.5 text-[11px]`}></i>
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="flex items-center gap-3">
          <Link to="/" className="text-xs font-medium flex items-center gap-1.5 px-3 py-1.5 rounded-full"
            style={{ color: 'var(--muted)', background: 'rgba(107,139,164,0.06)' }}
          >
            <i className="fas fa-arrow-left text-[10px]"></i> 返回前台
          </Link>
          <div className="w-px h-5" style={{ background: 'var(--line)' }}></div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ background: 'linear-gradient(135deg, #6b8ba4 0%, #4a6b82 100%)', color: 'white' }}
            >
              {(user?.username || '管')[0].toUpperCase()}
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-bold" style={{ color: 'var(--text)' }}>
                {user?.username || '管理员'}
              </p>
              <p className="text-[10px]" style={{ color: 'var(--muted)' }}>管理员</p>
            </div>
            <button onClick={logout} className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
              style={{ color: 'var(--muted)' }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(184,92,92,0.06)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              <i className="fas fa-right-from-bracket text-xs"></i>
            </button>
          </div>
        </div>
      </header>

      {/* 主内容 */}
      <div className="flex-1 overflow-y-auto" style={{ padding: '20px 16px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
