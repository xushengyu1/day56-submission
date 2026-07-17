import { createBrowserRouter } from 'react-router-dom'
import { UserLayout } from '@/components/UserLayout'
import { AdminLayout } from '@/components/AdminLayout'
import { RequireAuth, RequireAdmin } from '@/features/auth/guards'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { HomePage } from '@/features/home/HomePage'
import { LocationItemsPage } from '@/features/home/LocationItemsPage'
import { LostCreatePage } from '@/features/lost-items/LostCreatePage'
import { LostItemDetailPage } from '@/features/lost-items/LostItemDetailPage'
import { FoundWizardPage } from '@/features/found-items/FoundWizardPage'
import { FoundItemDetailPage } from '@/features/found-items/FoundItemDetailPage'
import { CandidateListPage } from '@/features/candidates/CandidateListPage'
import { CandidateDetailPage } from '@/features/candidates/CandidateDetailPage'
import { IdentityClaimForm } from '@/features/claims/IdentityClaimForm'
import { OtherClaimForm } from '@/features/claims/OtherClaimForm'
import { ClaimProgressPage } from '@/features/claims/ClaimProgressPage'
import { UnmatchedReviewPage } from '@/features/claims/UnmatchedReviewPage'
import { AdminQueuePage } from '@/features/admin/AdminQueuePage'
import { AdminReviewPage } from '@/features/admin/AdminReviewPage'
import { AdminAuditPage } from '@/features/admin/AdminAuditPage'
import { MyRecordsPage } from '@/features/records/MyRecordsPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    path: '/',
    element: <RequireAuth><UserLayout /></RequireAuth>,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'location/:location', element: <LocationItemsPage /> },
      { path: 'lost/new', element: <LostCreatePage /> },
      { path: 'lost/:id', element: <LostItemDetailPage /> },
      { path: 'lost/:id/candidates', element: <CandidateListPage /> },
      { path: 'lost/:id/unmatched-review', element: <UnmatchedReviewPage /> },
      { path: 'found/new', element: <FoundWizardPage /> },
      { path: 'found/:id', element: <FoundItemDetailPage /> },
      { path: 'candidates/:id', element: <CandidateDetailPage /> },
      { path: 'claims/identity/:candidateId', element: <IdentityClaimForm /> },
      { path: 'claims/other/:candidateId', element: <OtherClaimForm /> },
      { path: 'claims/:id/progress', element: <ClaimProgressPage /> },
      { path: 'records', element: <MyRecordsPage /> },
    ],
  },
  {
    path: '/admin',
    element: <RequireAdmin><AdminLayout /></RequireAdmin>,
    children: [
      { index: true, element: <AdminQueuePage /> },
      { path: 'reviews/:id', element: <AdminReviewPage /> },
      { path: 'audit', element: <AdminAuditPage /> },
    ],
  },
])
