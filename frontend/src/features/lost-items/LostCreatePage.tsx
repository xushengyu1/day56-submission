import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const ITEM_CATEGORIES = ['电子产品', '证件卡片', '服饰配饰', '学习用品', '其他']
const LOCATIONS = ['宿舍区', '食堂', '教学楼', '科教楼', '图书馆']

export function LostCreatePage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [form, setForm] = useState({
    item_type: 'OTHER' as 'OTHER' | 'IDENTITY_DOCUMENT',
    item_name: '',
    category: '',
    color: '黑色',
    date: '2026-07-16',
    time: '10:30',
    location: '',
    description: '',
  })

  const handleChange = (field: string, value: string) => setForm((prev) => ({ ...prev, [field]: value }))

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const url = URL.createObjectURL(file)
    setImagePreview(url)
  }

  const handleRemoveImage = () => {
    setImagePreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  useEffect(() => {
    return () => { if (imagePreview) URL.revokeObjectURL(imagePreview) }
  }, [imagePreview])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    navigate('/lost/lr-001/candidates')
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
            value={form.item_name} onChange={(e) => handleChange('item_name', e.target.value)} />

          <select className="form-select" value={form.category} onChange={(e) => handleChange('category', e.target.value)}>
            <option value="">物品类别（下拉选择）</option>
            {ITEM_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>

          <select className="form-select" value={form.location} onChange={(e) => handleChange('location', e.target.value)}>
            <option value="">丢失地点（下拉选择）</option>
            {LOCATIONS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>

          <input type="datetime-local" className="form-input" value={`${form.date}T${form.time}`}
            onChange={(e) => {
              const [d, t] = e.target.value.split('T')
              handleChange('date', d)
              handleChange('time', t || '10:30')
            }} />

          <textarea placeholder="物品描述（备注）" className="form-textarea"
            value={form.description} onChange={(e) => handleChange('description', e.target.value)} />

          <button type="submit" className="submit-btn">
            <i className="fas fa-paper-plane"></i>
            提交
          </button>
        </form>
      </div>

      <div className="page-slogan">物归原主，屿过天晴</div>
    </div>
  )
}
