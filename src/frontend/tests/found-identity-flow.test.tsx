import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { FoundWizardPage } from '@/features/found-items/FoundWizardPage'
import { foundRecordsApi } from '@/api/foundRecords'
import { uploadsApi } from '@/api/uploads'

vi.mock('@/api/foundRecords', () => ({ foundRecordsApi: {
  createDraft: vi.fn(), extract: vi.fn(), confirm: vi.fn(), confirmIdentity: vi.fn(), redact: vi.fn(), confirmQuestions: vi.fn(), publish: vi.fn(),
} }))
vi.mock('@/api/uploads', () => ({ uploadsApi: { upload: vi.fn() } }))

function renderWizard() {
  return render(<MemoryRouter initialEntries={['/found/new']}><Routes><Route path="/found/new" element={<FoundWizardPage />} /><Route path="/found/:id" element={<div>证件发布成功</div>} /></Routes></MemoryRouter>)
}

async function reachIdentityConfirmation() {
  renderWizard()
  fireEvent.change(screen.getByPlaceholderText('物品名称'), { target: { value: '居民身份证' } })
  fireEvent.change(screen.getByLabelText('物品类别'), { target: { value: 'IDENTITY_CARD' } })
  fireEvent.change(screen.getByLabelText('拾取地点'), { target: { value: 'LIBRARY' } })
  fireEvent.change(screen.getByLabelText('拾取时间'), { target: { value: '2026-07-17T11:00' } })
  fireEvent.change(screen.getByPlaceholderText(/公开描述/), { target: { value: '图书馆三楼阅览室拾得' } })
  fireEvent.change(screen.getByLabelText('选择物品图片'), { target: { files: [new File(['identity'], 'identity.png', { type: 'image/png' })] } })
  fireEvent.click(screen.getByRole('button', { name: '创建草稿并继续' }))
  await screen.findByLabelText('完整证件号')
}

function selectNaturalRegion() {
  const image = screen.getByRole('img', { name: '选择证件号码遮挡区域' })
  Object.defineProperty(image, 'naturalWidth', { configurable: true, value: 1000 })
  Object.defineProperty(image, 'naturalHeight', { configurable: true, value: 500 })
  vi.spyOn(image, 'getBoundingClientRect').mockReturnValue({ x: 0, y: 0, left: 0, top: 0, right: 500, bottom: 250, width: 500, height: 250, toJSON: () => ({}) })
  const picker = screen.getByTestId('redaction-picker')
  fireEvent.pointerDown(picker, { clientX: 100, clientY: 50, pointerId: 1 })
  fireEvent.pointerUp(picker, { clientX: 300, clientY: 150, pointerId: 1 })
}

describe('FoundWizardPage identity flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:identity'), revokeObjectURL: vi.fn() })
    vi.stubGlobal('PointerEvent', MouseEvent)
    vi.mocked(foundRecordsApi.createDraft).mockResolvedValue({ id: 'identity-1', status: 'DRAFT', version: 1 })
    vi.mocked(uploadsApi.upload).mockResolvedValue({ image_asset_id: 'identity-original', purpose: 'FINDER_ORIGINAL' })
    vi.mocked(foundRecordsApi.extract).mockResolvedValue({ suggested_name: 'AI 证件', suggested_description: 'AI 描述', suggested_item_type: 'IDENTITY_DOCUMENT', confidence: 0.98, status: 'SUCCEEDED' })
    vi.mocked(foundRecordsApi.confirm).mockResolvedValue({ id: 'identity-1', version: 2 })
    vi.mocked(foundRecordsApi.confirmIdentity).mockResolvedValue({ number_masked: '1101********002X' })
    vi.mocked(foundRecordsApi.redact).mockResolvedValue({ asset_id: 'public-redacted', status: 'CONFIRMED' })
    vi.mocked(foundRecordsApi.publish).mockResolvedValue({ id: 'identity-1', status: 'PUBLISHED', version: 3 })
  })

  it('requires explicit number confirmation and a positive user-selected redaction rectangle', async () => {
    await reachIdentityConfirmation()
    fireEvent.change(screen.getByLabelText('完整证件号'), { target: { value: '11010519491231002X' } })
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('明确确认数字无误')
    expect(foundRecordsApi.confirmIdentity).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('选择有效的证件号遮挡区域')
    expect(foundRecordsApi.confirmIdentity).not.toHaveBeenCalled()
  })

  it('sends the full number only to identity confirmation, clears it immediately, redacts natural pixels, then publishes', async () => {
    let resolvePublish!: (value: { id: string; status: 'PUBLISHED'; version: number }) => void
    vi.mocked(foundRecordsApi.publish).mockReturnValueOnce(new Promise((resolve) => { resolvePublish = resolve }))
    await reachIdentityConfirmation()
    fireEvent.change(screen.getByLabelText('完整证件号'), { target: { value: '11010519491231002X' } })
    fireEvent.click(screen.getByRole('checkbox'))
    selectNaturalRegion()
    expect(screen.getByText(/x=200, y=100, 400×200/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))

    await waitFor(() => expect(foundRecordsApi.confirmIdentity).toHaveBeenCalledWith('identity-1', '11010519491231002X', true))
    expect(screen.queryByLabelText('完整证件号')).not.toBeInTheDocument()
    expect(await screen.findByText(/完整号码已从页面清除/)).toBeInTheDocument()
    expect(foundRecordsApi.confirm).toHaveBeenCalledWith('identity-1', expect.not.objectContaining({ full_number: expect.anything() }))
    expect(foundRecordsApi.redact).toHaveBeenCalledWith('identity-1', 'identity-original', { x: 200, y: 100, width: 400, height: 200 })
    expect(foundRecordsApi.publish).toHaveBeenCalledWith('identity-1', 2)

    resolvePublish({ id: 'identity-1', status: 'PUBLISHED', version: 3 })
    expect(await screen.findByText('证件发布成功')).toBeInTheDocument()
  })

  it('retries publish with the latest version without resending the cleared number or redacting twice', async () => {
    vi.mocked(foundRecordsApi.confirm)
      .mockResolvedValueOnce({ id: 'identity-1', version: 2 })
      .mockResolvedValueOnce({ id: 'identity-1', version: 3 })
    vi.mocked(foundRecordsApi.publish)
      .mockRejectedValueOnce(new Error('发布超时'))
      .mockResolvedValueOnce({ id: 'identity-1', status: 'PUBLISHED', version: 4 })
    await reachIdentityConfirmation()
    fireEvent.change(screen.getByLabelText('完整证件号'), { target: { value: '11010519491231002X' } })
    fireEvent.click(screen.getByRole('checkbox'))
    selectNaturalRegion()
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('发布超时')
    expect(screen.queryByLabelText('完整证件号')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))
    expect(await screen.findByText('证件发布成功')).toBeInTheDocument()

    expect(foundRecordsApi.confirm).toHaveBeenNthCalledWith(2, 'identity-1', expect.objectContaining({ expected_version: 2 }))
    expect(foundRecordsApi.confirmIdentity).toHaveBeenCalledOnce()
    expect(foundRecordsApi.redact).toHaveBeenCalledOnce()
    expect(foundRecordsApi.publish).toHaveBeenNthCalledWith(2, 'identity-1', 3)
  })
})
