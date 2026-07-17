import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { IdentityClaimForm } from '@/features/claims/IdentityClaimForm'
import { OtherClaimForm } from '@/features/claims/OtherClaimForm'

vi.mock('@/features/auth/hooks', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'u1', username: 'test', email: 'test@test.com', role: 'USER', created_at: '' },
    isLoading: false,
    isAuthenticated: true,
    isAdmin: false,
  })),
  useLogout: vi.fn(() => ({ logout: vi.fn() })),
}))

function renderWithProviders(ui: React.ReactNode) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('IdentityClaimForm', () => {
  it('renders masked document number', () => {
    renderWithProviders(<IdentityClaimForm />)
    expect(screen.getByText('110***********1234')).toBeInTheDocument()
  })

  it('shows remaining attempts', () => {
    renderWithProviders(<IdentityClaimForm />)
    expect(screen.getByText(/剩余尝试/)).toBeInTheDocument()
    const attemptsSpan = screen.getByText(/剩余尝试/).closest('p')
    expect(attemptsSpan?.textContent).toContain('2')
  })

  it('submit button disabled when input is not 18 chars', () => {
    renderWithProviders(<IdentityClaimForm />)
    const input = screen.getByPlaceholderText('请输入 18 位身份证号码')
    fireEvent.change(input, { target: { value: '110101' } })
    const button = screen.getByText('提交验证')
    expect(button).toBeDisabled()
  })

  it('submit button enabled when input is 18 chars', () => {
    renderWithProviders(<IdentityClaimForm />)
    const input = screen.getByPlaceholderText('请输入 18 位身份证号码')
    fireEvent.change(input, { target: { value: '110101199901011234' } })
    const button = screen.getByText('提交验证')
    expect(button).not.toBeDisabled()
  })

  it('shows security notice', () => {
    renderWithProviders(<IdentityClaimForm />)
    expect(screen.getByText(/号码将通过加密方式比对/)).toBeInTheDocument()
    expect(screen.getByText(/同一账号最多尝试/)).toBeInTheDocument()
  })

  it('does not display full document number from found record', () => {
    renderWithProviders(<IdentityClaimForm />)
    // Should only show masked version, not any full number
    const maskedEl = screen.getByText('110***********1234')
    expect(maskedEl).toBeInTheDocument()
    // No 18-digit number should be visible
    expect(screen.queryByText(/110101\d{12}/)).not.toBeInTheDocument()
  })
})

describe('OtherClaimForm', () => {
  it('renders verification questions', () => {
    renderWithProviders(<OtherClaimForm />)
    expect(screen.getByText(/请描述伞套或伞袋上是否有任何特殊标记/)).toBeInTheDocument()
    expect(screen.getByText(/伞的把手部分有什么特别之处/)).toBeInTheDocument()
    expect(screen.getByText(/伞面上除了纯黑色外/)).toBeInTheDocument()
  })

  it('marks critical questions', () => {
    renderWithProviders(<OtherClaimForm />)
    // Critical questions have "问题 1（关键）" label
    const questionHeaders = screen.getAllByText(/问题 \d/)
    expect(questionHeaders.length).toBe(3)
    // First two are critical
    expect(screen.getAllByText(/关键/).length).toBeGreaterThanOrEqual(2)
  })

  it('submit button disabled when critical questions unanswered', () => {
    renderWithProviders(<OtherClaimForm />)
    const button = screen.getByText('提交核验')
    expect(button).toBeDisabled()
  })

  it('does not expose answer key to claimant', () => {
    renderWithProviders(<OtherClaimForm />)
    // The form should show questions but not the hidden feature answer key
    // Questions are shown as open-ended prompts
    expect(screen.getByText('请描述伞套或伞袋上是否有任何特殊标记或文字？')).toBeInTheDocument()
    // No "标准答案" or "answer" section visible
    expect(screen.queryByText('标准答案')).not.toBeInTheDocument()
  })

  it('shows AI assistance notice', () => {
    renderWithProviders(<OtherClaimForm />)
    expect(screen.getByText('AI 辅助核验')).toBeInTheDocument()
  })
})
