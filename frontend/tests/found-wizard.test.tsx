import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { FoundWizardPage } from '@/features/found-items/FoundWizardPage'
import { ApiError } from '@/api/errors'
import { foundRecordsApi } from '@/api/foundRecords'
import { uploadsApi } from '@/api/uploads'

vi.mock('@/api/foundRecords', () => ({
  foundRecordsApi: {
    createDraft: vi.fn(), get: vi.fn(), extract: vi.fn(), confirm: vi.fn(), confirmIdentity: vi.fn(),
    redact: vi.fn(), confirmQuestions: vi.fn(), publish: vi.fn(),
  },
}))
vi.mock('@/api/uploads', () => ({ uploadsApi: { upload: vi.fn() } }))

function renderWizard() {
  return render(
    <MemoryRouter initialEntries={['/found/new']}>
      <Routes>
        <Route path="/found/new" element={<FoundWizardPage />} />
        <Route path="/found/:id" element={<div>发布成功</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

function fillBase(category = 'ELECTRONICS') {
  fireEvent.change(screen.getByPlaceholderText('物品名称'), { target: { value: '用户填写的耳机' } })
  fireEvent.change(screen.getByLabelText('物品类别'), { target: { value: category } })
  fireEvent.change(screen.getByLabelText('拾取地点'), { target: { value: 'TEACHING_BUILDING' } })
  fireEvent.change(screen.getByLabelText('拾取时间'), { target: { value: '2026-07-17T10:30' } })
  fireEvent.change(screen.getByPlaceholderText(/公开描述/), { target: { value: '教学楼 B 区 302 教室拾得' } })
}

function serverRecord(status: 'DRAFT' | 'PUBLISHED', version: number) {
  return {
    id: 'found-1', owner_user_id: 'user-1', kind: 'FOUND' as const, item_type: 'OTHER' as const,
    public_category: 'ELECTRONICS' as const, location_area: 'TEACHING_BUILDING' as const,
    status, name_public: '用户填写的耳机', description_public: '教学楼 B 区 302 教室拾得',
    event_time_public: '2026-07-17 10:30', location_public: '教学楼', public_image_asset_id: null,
    number_masked: null, claim_id: null, version, published_at: status === 'PUBLISHED' ? '2026-07-17T02:30:00Z' : null,
    created_at: '2026-07-17T02:30:00Z', updated_at: '2026-07-17T02:30:00Z',
  }
}

describe('FoundWizardPage OTHER flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    let previewNumber = 0
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => `blob:preview-${++previewNumber}`), revokeObjectURL: vi.fn() })
    vi.mocked(foundRecordsApi.createDraft).mockResolvedValue({ id: 'found-1', status: 'DRAFT', version: 1 })
    vi.mocked(foundRecordsApi.get).mockResolvedValue(serverRecord('DRAFT', 2))
    vi.mocked(uploadsApi.upload).mockResolvedValue({ image_asset_id: 'asset-original', purpose: 'FINDER_ORIGINAL' })
    vi.mocked(foundRecordsApi.extract).mockResolvedValue({ suggested_name: 'AI 名称', suggested_description: 'AI 描述', suggested_item_type: 'OTHER', confidence: 0.9, status: 'SUCCEEDED' })
    vi.mocked(foundRecordsApi.confirm).mockResolvedValue({ id: 'found-1', version: 2 })
    vi.mocked(foundRecordsApi.confirmQuestions).mockResolvedValue({ verification_set_id: 'set-1' })
    vi.mocked(foundRecordsApi.publish).mockResolvedValue({ id: 'found-1', status: 'PUBLISHED', version: 3 })
  })

  it('renders the approved exact catalog and current slogan', () => {
    renderWizard()
    expect(screen.getByText('我要招领')).toBeInTheDocument()
    for (const label of ['电子产品', '证件卡片', '服饰配饰', '学习用品', '其他']) expect(screen.getByRole('option', { name: label })).toBeInTheDocument()
    for (const label of ['宿舍区', '食堂', '教学楼', '科教楼', '图书馆']) expect(screen.getByRole('option', { name: label })).toBeInTheDocument()
    expect(screen.getByText('物归原主，屿过天晴')).toBeInTheDocument()
  })

  it('keeps file selection local and revokes preview on replacement and unmount', () => {
    const view = renderWizard()
    const input = screen.getByLabelText('选择物品图片')
    fireEvent.change(input, { target: { files: [new File(['one'], 'one.png', { type: 'image/png' })] } })

    expect(screen.getByRole('img', { name: '招领图片预览' })).toHaveAttribute('src', 'blob:preview-1')
    expect(foundRecordsApi.createDraft).not.toHaveBeenCalled()
    expect(uploadsApi.upload).not.toHaveBeenCalled()
    expect(foundRecordsApi.extract).not.toHaveBeenCalled()

    fireEvent.change(input, { target: { files: [new File(['two'], 'two.png', { type: 'image/png' })] } })
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview-1')
    view.unmount()
    expect(URL.revokeObjectURL).toHaveBeenCalledTimes(2)
    expect(URL.revokeObjectURL).toHaveBeenLastCalledWith('blob:preview-2')
  })

  it('creates, uploads and extracts on first submit without overriding user public fields, then explicitly publishes', async () => {
    renderWizard()
    fillBase('ELECTRONICS')
    fireEvent.change(screen.getByLabelText('选择物品图片'), { target: { files: [new File(['image'], 'item.png', { type: 'image/png' })] } })

    fireEvent.click(screen.getByRole('button', { name: '创建草稿并继续' }))
    expect(await screen.findByRole('button', { name: '确认信息并发布' })).toBeInTheDocument()

    expect(foundRecordsApi.createDraft).toHaveBeenCalledWith({ event_time: new Date('2026-07-17T10:30').toISOString(), location_area: 'TEACHING_BUILDING' })
    expect(uploadsApi.upload).toHaveBeenCalledWith('found-1', 'FINDER_ORIGINAL', expect.any(File))
    expect(foundRecordsApi.extract).toHaveBeenCalledWith('found-1', 'asset-original')
    expect(vi.mocked(foundRecordsApi.createDraft).mock.invocationCallOrder[0]).toBeLessThan(vi.mocked(uploadsApi.upload).mock.invocationCallOrder[0])
    expect(vi.mocked(uploadsApi.upload).mock.invocationCallOrder[0]).toBeLessThan(vi.mocked(foundRecordsApi.extract).mock.invocationCallOrder[0])
    expect(screen.getByPlaceholderText('物品名称')).toHaveValue('用户填写的耳机')
    expect(screen.getByPlaceholderText(/公开描述/)).toHaveValue('教学楼 B 区 302 教室拾得')
    expect(screen.getByLabelText('物品类别')).toHaveValue('ELECTRONICS')
    expect(foundRecordsApi.publish).not.toHaveBeenCalled()

    fireEvent.change(screen.getByPlaceholderText(/隐藏特征/), { target: { value: '右侧耳机内侧有一个小红点' } })
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))

    expect(await screen.findByText('发布成功')).toBeInTheDocument()
    expect(foundRecordsApi.confirm).toHaveBeenCalledWith('found-1', expect.objectContaining({ expected_version: 1, public_category: 'ELECTRONICS', description_public: '教学楼 B 区 302 教室拾得' }))
    expect(foundRecordsApi.confirmQuestions).toHaveBeenCalledWith('found-1', '右侧耳机内侧有一个小红点')
    expect(foundRecordsApi.publish).toHaveBeenCalledWith('found-1', 2)
  })

  it('supports a no-image manual draft without calling upload or extraction', async () => {
    renderWizard()
    fillBase('STATIONERY')
    fireEvent.click(screen.getByRole('button', { name: '创建草稿并继续' }))

    expect(await screen.findByRole('button', { name: '确认信息并发布' })).toBeInTheDocument()
    expect(uploadsApi.upload).not.toHaveBeenCalled()
    expect(foundRecordsApi.extract).not.toHaveBeenCalled()
  })

  it('revalidates editable confirmation fields and exposes backend length limits', async () => {
    renderWizard()
    fillBase('OTHER_CATEGORY')
    expect(screen.getByPlaceholderText('物品名称')).toHaveAttribute('maxlength', '160')
    expect(screen.getByPlaceholderText(/公开描述/)).toHaveAttribute('maxlength', '2000')
    fireEvent.click(screen.getByRole('button', { name: '创建草稿并继续' }))
    await screen.findByRole('button', { name: '确认信息并发布' })
    expect(screen.getByPlaceholderText(/隐藏特征/)).toHaveAttribute('maxlength', '4000')

    fireEvent.change(screen.getByLabelText('物品类别'), { target: { value: '' } })
    fireEvent.change(screen.getByLabelText('拾取时间'), { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('请选择物品类别、拾取地点和时间')
    expect(foundRecordsApi.confirm).not.toHaveBeenCalled()
  })

  it('preserves the draft and upload after AI failure and offers retry plus manual entry', async () => {
    vi.mocked(foundRecordsApi.extract).mockRejectedValueOnce(new Error('模型暂时不可用'))
    renderWizard()
    fillBase()
    fireEvent.change(screen.getByLabelText('选择物品图片'), { target: { files: [new File(['image'], 'item.png', { type: 'image/png' })] } })
    fireEvent.click(screen.getByRole('button', { name: '创建草稿并继续' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('AI 识别失败')
    expect(screen.getByRole('button', { name: '跳过 AI，手工填写' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '创建草稿并继续' }))

    expect(await screen.findByRole('button', { name: '确认信息并发布' })).toBeInTheDocument()
    expect(foundRecordsApi.createDraft).toHaveBeenCalledOnce()
    expect(uploadsApi.upload).toHaveBeenCalledOnce()
    expect(foundRecordsApi.extract).toHaveBeenCalledTimes(2)
  })

  it('retries a failed publish with the latest version without generating questions twice', async () => {
    vi.mocked(foundRecordsApi.confirm)
      .mockResolvedValueOnce({ id: 'found-1', version: 2 })
      .mockResolvedValueOnce({ id: 'found-1', version: 3 })
    vi.mocked(foundRecordsApi.publish)
      .mockRejectedValueOnce(new Error('发布网络中断'))
      .mockResolvedValueOnce({ id: 'found-1', status: 'PUBLISHED', version: 4 })
    renderWizard()
    fillBase('CLOTHING')
    fireEvent.click(screen.getByRole('button', { name: '创建草稿并继续' }))
    await screen.findByRole('button', { name: '确认信息并发布' })
    fireEvent.change(screen.getByPlaceholderText(/隐藏特征/), { target: { value: '衣服内标写有手写字母 A' } })
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('发布网络中断')
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))
    expect(await screen.findByText('发布成功')).toBeInTheDocument()

    expect(foundRecordsApi.confirm).toHaveBeenNthCalledWith(2, 'found-1', expect.objectContaining({ expected_version: 2 }))
    expect(foundRecordsApi.confirmQuestions).toHaveBeenCalledOnce()
    expect(foundRecordsApi.publish).toHaveBeenNthCalledWith(1, 'found-1', 2)
    expect(foundRecordsApi.publish).toHaveBeenNthCalledWith(2, 'found-1', 3)
  })

  it('reconciles a lost confirmation response and retries with the server version', async () => {
    vi.mocked(foundRecordsApi.confirm)
      .mockRejectedValueOnce(new Error('确认响应丢失'))
      .mockResolvedValueOnce({ id: 'found-1', version: 3 })
    renderWizard()
    fillBase('OTHER_CATEGORY')
    fireEvent.click(screen.getByRole('button', { name: '创建草稿并继续' }))
    await screen.findByRole('button', { name: '确认信息并发布' })
    fireEvent.change(screen.getByPlaceholderText(/隐藏特征/), { target: { value: '杯底刻有字母 A' } })
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('已同步服务端状态，请重试')
    expect(foundRecordsApi.get).toHaveBeenCalledWith('found-1')
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))
    expect(await screen.findByText('发布成功')).toBeInTheDocument()

    expect(foundRecordsApi.confirm).toHaveBeenNthCalledWith(2, 'found-1', expect.objectContaining({ expected_version: 2 }))
    expect(foundRecordsApi.confirmQuestions).toHaveBeenCalledOnce()
  })

  it('navigates directly when reconciliation proves a lost publish response succeeded', async () => {
    vi.mocked(foundRecordsApi.publish).mockRejectedValueOnce(new Error('发布响应丢失'))
    vi.mocked(foundRecordsApi.get).mockResolvedValueOnce(serverRecord('PUBLISHED', 3))
    renderWizard()
    fillBase('CLOTHING')
    fireEvent.click(screen.getByRole('button', { name: '创建草稿并继续' }))
    await screen.findByRole('button', { name: '确认信息并发布' })
    fireEvent.change(screen.getByPlaceholderText(/隐藏特征/), { target: { value: '内标有手写字母 B' } })
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))

    expect(await screen.findByText('发布成功')).toBeInTheDocument()
    expect(foundRecordsApi.get).toHaveBeenCalledWith('found-1')
    expect(foundRecordsApi.confirmQuestions).toHaveBeenCalledOnce()
    expect(foundRecordsApi.publish).toHaveBeenCalledOnce()
  })

  it('does not reconcile a definite API error response', async () => {
    vi.mocked(foundRecordsApi.confirm).mockRejectedValueOnce(
      new ApiError(409, 'VERSION_CONFLICT', '记录已被更新，请重新加载'),
    )
    renderWizard()
    fillBase('OTHER_CATEGORY')
    fireEvent.click(screen.getByRole('button', { name: '创建草稿并继续' }))
    await screen.findByRole('button', { name: '确认信息并发布' })
    fireEvent.change(screen.getByPlaceholderText(/隐藏特征/), { target: { value: '杯底刻有字母 C' } })
    fireEvent.click(screen.getByRole('button', { name: '确认信息并发布' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('记录已被更新，请重新加载')
    expect(foundRecordsApi.get).not.toHaveBeenCalled()
  })
})
