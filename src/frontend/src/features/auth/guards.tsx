import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './hooks'

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-3xl text-blue-500 mb-4"></i>
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAdmin, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-3xl text-blue-500 mb-4"></i>
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <i className="fas fa-ban text-5xl text-red-400 mb-4"></i>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">无权访问</h2>
          <p className="text-gray-500">您没有管理员权限，无法访问此页面。</p>
          <a href="/" className="inline-block mt-4 px-6 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700">
            返回首页
          </a>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
