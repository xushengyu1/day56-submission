import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { publicCategoryOptions, locationAreaOptions } from '@/api/catalog'
import { lostRecordsApi } from '@/api/lostRecords'
import { uploadsApi } from '@/api/uploads'
import type { LocationArea, PublicCategory } from '@/api/types'

export function LostCreatePage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [createdRecordId, setCreatedRecordId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [form, setForm] = useState({
    item_name: '',
    category: '' as PublicCategory | '',
    location: '' as LocationArea | '',
    event_time: '',
    description: '',
  })

  const handleChange = (field: string, value: string) => setForm((prev) => ({ ...prev, [field]: value }))

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const url = URL.createObjectURL(file)
    setImageFile(file)
    setImagePreview(url)
    setSubmitError(null)
  }

  const handleRemoveImage = () => {
    setImageFile(null)
    setImagePreview(null)
    setSubmitError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  useEffect(() => {
    return () => { if (imagePreview) URL.revokeObjectURL(imagePreview) }
  }, [imagePreview])

  const continueToCandidates = (recordId: string) => navigate(`/lost/${recordId}/candidates`)

  const uploadAndContinue = async (recordId: string) => {
    if (!imageFile) {
      continueToCandidates(recordId)
      return
    }
    await uploadsApi.upload(recordId, 'OWNER_SUPPORT', imageFile)
    continueToCandidates(recordId)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.item_name.trim() || !form.category || !form.location || !form.event_time || !form.description.trim()) {
      setSubmitError('请完整填写所有必填信息')
      return
    }
    const eventTime = new Date(form.event_time)
    if (Number.isNaN(eventTime.getTime())) {
      setSubmitError('请选择有效的丢失时间')
      return
    }

    setIsSubmitting(true)
    setSubmitError(null)
    try {
      if (createdRecordId) {
        await uploadAndContinue(createdRecordId)
        return
      }
      const record = await lostRecordsApi.create({
        public_category: form.category,
        location_area: form.location,
        event_time: eventTime.toISOString(),
        name_public: form.item_name.trim(),
        description_public: form.description.trim(),
      })
      setCreatedRecordId(record.id)
      await uploadAndContinue(record.id)
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : '提交失败，请重试')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="page-shell">
      {/* 页面标题 */}
      <div className="page-title">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
          <circle cx="11" cy="11" r="7" stroke="#6b8ba4" strokeWidth="2"/>
          <path d="M16 16l4 4" stroke="#6b8ba4" strokeWidth="2" strokeLinecap="round"/>
          <path d="M9 8h4M9 11h2" stroke="#6b8ba4" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        我要寻物
      </div>

      {/* 表单容器 */}
      <div className="form-container">
        {/* 左侧图片上传 */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleImageSelect}
          style={{ display: 'none' }}
        />
        {imagePreview ? (
          <div style={{ position: 'relative' }}>
            <div style={{
              width: '100%', minHeight: '300px', borderRadius: '24px', overflow: 'hidden',
              border: '1.5px solid rgba(107,139,164,0.3)',
            }}>
              <img src={imagePreview} alt="预览" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
            </div>
            <button
              type="button"
              onClick={handleRemoveImage}
              style={{
                position: 'absolute', top: '12px', right: '12px',
                width: '32px', height: '32px', borderRadius: '50%', border: 'none',
                background: 'rgba(0,0,0,0.5)', color: '#fff', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              <i className="fas fa-times text-xs"></i>
            </button>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              style={{
                position: 'absolute', bottom: '12px', right: '12px',
                padding: '6px 14px', borderRadius: '999px', border: 'none',
                background: 'rgba(255,255,255,0.9)', color: 'var(--text)', cursor: 'pointer',
                fontSize: '12px', fontWeight: 600, backdropFilter: 'blur(8px)',
              }}
            >
              <i className="fas fa-redo mr-1"></i> 更换
            </button>
          </div>
        ) : (
          <div className="upload-area" onClick={() => fileInputRef.current?.click()}>
            <div className="plus">+</div>
            <div className="text">上传图片</div>
            <div style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '4px' }}>
              支持 JPG / PNG / WebP，最大 10MB
            </div>
          </div>
        )}

        {/* 右侧表单 */}
        <form onSubmit={handleSubmit} className="form-fields">
          <input type="text" placeholder="物品名称" className="form-input" id="itemName"
            value={form.item_name} onChange={(e) => handleChange('item_name', e.target.value)} required maxLength={160} disabled={Boolean(createdRecordId)} />

          <select className="form-select" value={form.category} onChange={(e) => handleChange('category', e.target.value)} required disabled={Boolean(createdRecordId)}>
            <option value="">物品类别（下拉选择）</option>
            {publicCategoryOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>

          <select className="form-select" value={form.location} onChange={(e) => handleChange('location', e.target.value)} required disabled={Boolean(createdRecordId)}>
            <option value="">丢失地点（下拉选择）</option>
            {locationAreaOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>

          <input type="datetime-local" className="form-input" value={form.event_time}
            onChange={(e) => handleChange('event_time', e.target.value)} required disabled={Boolean(createdRecordId)} />

          <textarea placeholder="物品描述（请包含具体楼栋、楼层或教室等详细地点）" className="form-textarea"
            value={form.description} onChange={(e) => handleChange('description', e.target.value)} required maxLength={2000} disabled={Boolean(createdRecordId)} />

          {submitError && (
            <div role="alert" style={{ color: 'var(--danger)', fontSize: '13px' }}>
              {createdRecordId ? `记录已创建，图片上传失败：${submitError}` : submitError}
            </div>
          )}

          <button type="submit" className="submit-btn" disabled={isSubmitting}>
            <i className="fas fa-paper-plane"></i>
            {isSubmitting ? '提交中…' : createdRecordId ? (imageFile ? '重试上传' : '继续匹配') : '提交'}
          </button>
          {createdRecordId && submitError && (
            <button type="button" className="submit-btn" disabled={isSubmitting} onClick={() => continueToCandidates(createdRecordId)}>
              暂不上传，继续匹配
            </button>
          )}
        </form>
      </div>

      <div className="page-slogan">物归原主，屿过天晴</div>
    </div>
  )
}
