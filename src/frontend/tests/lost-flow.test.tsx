import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { LostCreatePage } from '@/features/lost-items/LostCreatePage'
import { UnmatchedReviewPage } from '@/features/claims/UnmatchedReviewPage'
import { lostRecordsApi } from '@/api/lostRecords'
import { uploadsApi } from '@/api/uploads'

vi.mock('@/api/lostRecords', () => ({
  lostRecordsApi: {
    create: vi.fn(),
    createUnmatchedReview: vi.fn(),
  },
}))

vi.mock('@/api/uploads', () => ({
  uploadsApi: { upload: vi.fn() },
}))

const createObjectURL = vi.fn()
const revokeObjectURL = vi.fn()
Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createObjectURL })
Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revokeObjectURL })

function renderLostCreate() {
  return render(
    <MemoryRouter initialEntries={['/lost/new']}>
      <Routes>
        <Route path="/lost/new" element={<LostCreatePage />} />
        <Route path="/lost/:id/candidates" element={<div>候选页面</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

function fillLostForm() {
  fireEvent.change(screen.getByPlaceholderText('物品名称'), { target: { value: '黑色折叠伞' } })
  const selects = screen.getAllByRole('combobox')
  fireEvent.change(selects[0], { target: { value: 'ELECTRONICS' } })
  fireEvent.change(selects[1], { target: { value: 'TEACHING_BUILDING' } })
  fireEvent.change(document.querySelector('input[type="datetime-local"]')!, { target: { value: '2026-07-17T10:30' } })
  fireEvent.change(screen.getByPlaceholderText(/物品描述/), { target: { value: '教学楼 B 区 301 教室，伞柄有白色划痕' } })
}

function renderReview(path = '/lost/lost-7/unmatched-review', route = '/lost/:id/unmatched-review') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={route} element={<UnmatchedReviewPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  createObjectURL.mockReset()
  revokeObjectURL.mockReset()
  createObjectURL.mockReturnValueOnce('blob:first').mockReturnValueOnce('blob:second')
  vi.mocked(lostRecordsApi.create).mockResolvedValue({ id: 'lost-7', status: 'PUBLISHED' })
  vi.mocked(uploadsApi.upload).mockResolvedValue({ image_asset_id: 'asset-1', purpose: 'OWNER_SUPPORT' })
  vi.mocked(lostRecordsApi.createUnmatchedReview).mockResolvedValue({ id: 'review-1', status: 'PENDING' })
})

describe('LostCreatePage', () => {
  it('shows the exact public categories and location areas', () => {
    renderLostCreate()

    for (const label of ['电子产品', '证件卡片', '服饰配饰', '学习用品', '其他']) {
      expect(screen.getByRole('option', { name: label })).toBeInTheDocument()
    }
    for (const label of ['宿舍区', '食堂', '教学楼', '科教楼', '图书馆']) {
      expect(screen.getByRole('option', { name: label })).toBeInTheDocument()
    }
  })

  it('submits exact enums, keeps detailed location in description, and navigates with the real id', async () => {
    renderLostCreate()
    fillLostForm()

    fireEvent.click(screen.getByRole('button', { name: '提交' }))

    await waitFor(() => expect(lostRecordsApi.create).toHaveBeenCalledWith({
      public_category: 'ELECTRONICS',
      location_area: 'TEACHING_BUILDING',
      event_time: new Date('2026-07-17T10:30').toISOString(),
      name_public: '黑色折叠伞',
      description_public: '教学楼 B 区 301 教室，伞柄有白色划痕',
    }))
    expect(uploadsApi.upload).not.toHaveBeenCalled()
    expect(await screen.findByText('候选页面')).toBeInTheDocument()
  })

  it('does not call the API when required fields are missing', () => {
    renderLostCreate()

    fireEvent.submit(screen.getByRole('button', { name: '提交' }).closest('form')!)

    expect(screen.getByRole('alert')).toHaveTextContent('请完整填写所有必填信息')
    expect(lostRecordsApi.create).not.toHaveBeenCalled()
  })

  it('retries a failed OWNER_SUPPORT upload without creating another record', async () => {
    vi.mocked(uploadsApi.upload).mockRejectedValueOnce(new Error('网络中断'))
    renderLostCreate()
    fillLostForm()
    const file = new File(['image'], 'umbrella.png', { type: 'image/png' })
    fireEvent.change(document.querySelector('input[type="file"]')!, { target: { files: [file] } })

    fireEvent.click(screen.getByRole('button', { name: '提交' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('记录已创建，图片上传失败：网络中断')
    expect(lostRecordsApi.create).toHaveBeenCalledTimes(1)
    expect(uploadsApi.upload).toHaveBeenCalledWith('lost-7', 'OWNER_SUPPORT', file)

    fireEvent.click(screen.getByRole('button', { name: '重试上传' }))

    expect(await screen.findByText('候选页面')).toBeInTheDocument()
    expect(lostRecordsApi.create).toHaveBeenCalledTimes(1)
    expect(uploadsApi.upload).toHaveBeenCalledTimes(2)
  })

  it('revokes replaced and unmounted local preview URLs', async () => {
    const { unmount } = renderLostCreate()
    const input = document.querySelector('input[type="file"]')!
    fireEvent.change(input, { target: { files: [new File(['one'], 'one.png', { type: 'image/png' })] } })
    fireEvent.change(input, { target: { files: [new File(['two'], 'two.png', { type: 'image/png' })] } })

    await waitFor(() => expect(revokeObjectURL).toHaveBeenCalledWith('blob:first'))
    unmount()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:second')
  })
})

describe('UnmatchedReviewPage', () => {
  function fillRequiredReviewFields() {
    fireEvent.change(screen.getByPlaceholderText('例如：黑色折叠伞'), { target: { value: '黑色折叠伞' } })
    fireEvent.change(screen.getByPlaceholderText(/请尽量详细描述/), { target: { value: '伞柄有白色划痕' } })
  }

  it('combines the form into a meaningful review reason and shows success', async () => {
    renderReview()
    fillRequiredReviewFields()
    fireEvent.change(screen.getByPlaceholderText('例如：教学楼B区3楼'), { target: { value: '教学楼 B 区 301' } })
    fireEvent.change(screen.getByPlaceholderText('例如：7月16日上午10点左右'), { target: { value: '7月17日 10:30' } })
    fireEvent.change(screen.getByPlaceholderText(/其他有助于找回物品的信息/), { target: { value: '同行人可以作证' } })

    fireEvent.click(screen.getByRole('button', { name: '提交复核申请' }))

    await waitFor(() => expect(lostRecordsApi.createUnmatchedReview).toHaveBeenCalledWith('lost-7', [
      '物品名称：黑色折叠伞',
      '物品描述：伞柄有白色划痕',
      '丢失地点：教学楼 B 区 301',
      '丢失时间段：7月17日 10:30',
      '补充说明：同行人可以作证',
    ].join('\n')))
    expect(await screen.findByText('复核申请已提交')).toBeInTheDocument()
  })

  it('shows a failure and allows retry', async () => {
    vi.mocked(lostRecordsApi.createUnmatchedReview).mockRejectedValueOnce(new Error('服务暂不可用'))
    renderReview()
    fillRequiredReviewFields()

    fireEvent.click(screen.getByRole('button', { name: '提交复核申请' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('服务暂不可用')

    fireEvent.click(screen.getByRole('button', { name: '重试提交' }))
    expect(await screen.findByText('复核申请已提交')).toBeInTheDocument()
    expect(lostRecordsApi.createUnmatchedReview).toHaveBeenCalledTimes(2)
  })

  it('does not request without a route id', () => {
    renderReview('/lost/unmatched-review', '/lost/unmatched-review')

    expect(screen.getByRole('alert')).toHaveTextContent('缺少寻物记录编号')
    expect(lostRecordsApi.createUnmatchedReview).not.toHaveBeenCalled()
  })

  it('rejects a combined reason longer than the backend limit', () => {
    renderReview()
    fireEvent.change(screen.getByPlaceholderText('例如：黑色折叠伞'), { target: { value: '黑色折叠伞' } })
    fireEvent.change(screen.getByPlaceholderText(/请尽量详细描述/), { target: { value: '特'.repeat(2000) } })

    fireEvent.submit(screen.getByRole('button', { name: '提交复核申请' }).closest('form')!)

    expect(screen.getByRole('alert')).toHaveTextContent('复核说明不能超过 2000 个字符')
    expect(lostRecordsApi.createUnmatchedReview).not.toHaveBeenCalled()
  })
})
