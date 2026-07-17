import { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth, useLogout } from '@/features/auth/hooks'

export function Navbar() {
  const { user } = useAuth()
  const { logout } = useLogout()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const navItems = [
    { path: '/', label: '首页' },
    { path: '/found/new', label: '我要招领' },
    { path: '/lost/new', label: '我要寻物' },
    { path: '/records', label: '我的记录' },
  ]

  return (
    <>
      <div className="site-bg site-bg-1"></div>
      <div className="site-bg site-bg-2"></div>
      <header className="header-bar">
        <Link to="/" className="brand-link">
          {/* 绿色岛屿 Logo */}
          <div style={{
            width: '38px', height: '38px', borderRadius: '12px',
            background: 'linear-gradient(135deg, #6b9e7a 0%, #4a7a5a 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(107,158,122,0.25)'
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="rgba(255,255,255,0.15)"/>
              <path d="M7 14.5c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
              <path d="M9 15c0-1.7 1.3-3 3-3s3 1.3 3 3" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
              <circle cx="12" cy="16" r="1.5" fill="white"/>
              <path d="M12 4v3M8.5 5.5l1.5 2M15.5 5.5l-1.5 2" stroke="white" strokeWidth="1.2" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <div className="brand-name">物屿</div>
            <div className="slogan-text">物归原主，屿过天晴</div>
          </div>
        </Link>

        <nav className="nav-menu">
          {navItems.map((item) => (
            <Link key={item.path} to={item.path} className={location.pathname === item.path ? 'active' : ''}>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2.5 px-3 py-2 rounded-2xl transition-all"
            style={{ background: menuOpen ? 'rgba(107,139,164,0.06)' : 'transparent' }}
          >
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ background: 'linear-gradient(135deg, #6b9e7a 0%, #4a7a5a 100%)', color: 'white' }}
            >
              {(user?.username || '用')[0].toUpperCase()}
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-xs font-bold" style={{ color: 'var(--text)' }}>{user?.username || '用户'}</p>
              <p className="text-[10px]" style={{ color: 'var(--muted)' }}>
                {user?.role === 'ADMIN' ? '管理员' : '普通用户'}
              </p>
            </div>
            <i className={`fas fa-chevron-${menuOpen ? 'up' : 'down'} text-[9px]`} style={{ color: 'var(--muted)' }}></i>
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full mt-2 w-52 rounded-2xl border py-2 z-50 glass-card"
              style={{ borderColor: 'rgba(226,232,240,0.6)' }}
            >
              <div className="px-4 py-2.5 border-b" style={{ borderColor: 'var(--line)' }}>
                <p className="text-sm font-bold" style={{ color: 'var(--text)' }}>{user?.username}</p>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>{user?.email}</p>
              </div>
              {user?.role === 'ADMIN' && (
                <Link to="/admin" onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2.5 text-sm transition-colors"
                  style={{ color: 'var(--text)' }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(107,139,164,0.06)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <i className="fas fa-shield-halved w-5 text-center text-xs" style={{ color: 'var(--purple)' }}></i>
                  管理员工作台
                </Link>
              )}
              <div className="border-t my-1" style={{ borderColor: 'var(--line)' }}></div>
              <button onClick={() => { setMenuOpen(false); logout() }}
                className="flex items-center gap-2.5 px-4 py-2.5 text-sm w-full text-left transition-colors"
                style={{ color: 'var(--danger)' }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(184,92,92,0.06)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <i className="fas fa-right-from-bracket w-5 text-center text-xs"></i>
                退出登录
              </button>
            </div>
          )}
        </div>
      </header>
    </>
  )
}
