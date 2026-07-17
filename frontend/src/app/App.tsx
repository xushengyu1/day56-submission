import { RouterProvider } from 'react-router-dom'
import { AppProviders } from './providers'
import { router } from './router'
import { isMockMode } from '@/api/client'
import { MockModeBanner } from '@/components/MockModeBanner'

export function App() {
  return (
    <AppProviders>
      {isMockMode && <MockModeBanner />}
      <RouterProvider router={router} />
    </AppProviders>
  )
}
