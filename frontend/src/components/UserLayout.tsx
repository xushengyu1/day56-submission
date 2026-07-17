import { Outlet } from 'react-router-dom'
import { Navbar } from './Navbar'

export function UserLayout() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'linear-gradient(180deg, #f7fbff 0%, #f3f8ff 48%, #f8fbff 100%)' }}>
      <Navbar />
      <main style={{ flex: 1, overflow: 'auto', position: 'relative', zIndex: 1 }}>
        <Outlet />
      </main>
    </div>
  )
}
