import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const ITEM_CATEGORIES = ['电子产品', '证件卡片', '服饰配饰', '学习用品', '其他']
const LOCATIONS = ['宿舍区', '食堂', '教学楼', '科教楼', '图书馆']

const MOCK_AI_RESULTS = [
  { item_name: '黑色折叠伞', category: '其他', description: '黑色短柄折叠伞，伞面完好，手柄无磨损，无明显品牌标识。' },
  { item_name: '白色AirPods Pro', category: '电子产品', description: '白色AirPods Pro二代耳机，充电仓有轻微划痕，耳机功能正常。' },
  { item_name: '校园一卡通', category: '证件卡片', description: '校园一卡通，卡面有姓名拼音，卡号部分可见。' },
  { item_name: '灰色双肩包', category: '服饰配饰', description: '灰色双肩包，品牌为耐克，侧袋有钥匙扣，内有少量物品。' },
  { item_name: '蓝色保温杯', category: '其他', description: '蓝色保温杯，品牌为膳魔师，杯身有贴纸，保温功能正常。' },
]

export function FoundWizardPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [aiRecognizing, setAiRecognizing] = useState(false)
  const [aiDone, setAiDone] = useState(false)
  const [form, setForm] = useState({
    item_name: '',
    category: '',
    location: '',
    date: '2026-07-16',
    time: '10:30',
    description: '',
    hiddenInfo: '',
  })

  const handleChange = (field: string, value: string) => setForm((prev) => ({ ...prev, [field]: value }))

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const url = URL.createObjectURL(file)
    setImagePreview(url)
    setAiDone(false)

    setAiRecognizing(true)
    setTimeout(() => {
      const result = MOCK_AI_RESULTS[Math.floor(Math.random() * MOCK_AI_RESULTS.length)]
      setForm((prev) => ({
        ...prev,
        item_name: prev.item_name || result.item_name,
        category: prev.category || result.category,
        description: prev.description || result.description,
      }))
      setAiRecognizing(false)
      setAiDone(true)
    }, 1500)
  }

  const handleRemoveImage = () => {
    setImagePreview(null)
    setAiDone(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  useEffect(() => {
    return () => { if (imagePreview) URL.revokeObjectURL(imagePreview) }
  }, [imagePreview])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    navigate('/')
  }

  return (
    <div className="page-shell">
      {/* 页面标题 */}
      <div className="page-title">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
          <path d="M12 3C7 3 3 7 3 12s4 9 9 9 9-4 9-9-4-9-9-9z" stroke="#6b9e7a" strokeWidth="2"/>
          <path d="M8 14c0-2.2 1.8-4 4-4s4 1.8 4 4" stroke="#6b9e7a" strokeWidth="2" strokeLinecap="round"/>
          <circle cx="12" cy="15.5" r="1.5" fill="#6b9e7a"/>
          <path d="M12 5v2.5M9 6.5l1.5 1.5M15 6.5l-1.5 1.5" stroke="#6b9e7a" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        我要招领
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
            {aiRecognizing && (
              <div style={{
                position: 'absolute', bottom: '12px', left: '12px',
                padding: '8px 16px', borderRadius: '999px',
                background: 'rgba(107,139,164,0.9)', color: '#fff',
                fontSize: '12px', fontWeight: 600, backdropFilter: 'blur(8px)',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                <i className="fas fa-robot fa-spin"></i> AI 识别中...
              </div>
            )}
            {aiDone && !aiRecognizing && (
              <div style={{
                position: 'absolute', bottom: '12px', left: '12px',
                padding: '8px 16px', borderRadius: '999px',
                background: 'rgba(107,158,122,0.9)', color: '#fff',
                fontSize: '12px', fontWeight: 600, backdropFilter: 'blur(8px)',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                <i className="fas fa-check-circle"></i> AI 识别完成，已自动填充
              </div>
            )}
          </div>
        ) : (
          <div className="upload-area" onClick={() => fileInputRef.current?.click()}>
            <div className="plus">+</div>
            <div className="text">上传图片</div>
            <div style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '4px' }}>
              支持 JPG / PNG / WebP，最大 10MB
            </div>
            <div style={{ fontSize: '11px', color: 'var(--primary)', marginTop: '10px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <i className="fas fa-robot"></i> 上传后 AI 自动识别物品信息
            </div>
          </div>
        )}

        {/* 右侧表单 — 结构与寻物页完全一致 */}
        <form onSubmit={handleSubmit} className="form-fields">
          <input type="text" placeholder="物品名称" className="form-input"
            value={form.item_name} onChange={(e) => handleChange('item_name', e.target.value)} />

          <select className="form-select" value={form.category} onChange={(e) => handleChange('category', e.target.value)}>
            <option value="">物品类别（下拉选择）</option>
            {ITEM_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>

          <select className="form-select" value={form.location} onChange={(e) => handleChange('location', e.target.value)}>
            <option value="">捡到地点（下拉选择）</option>
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

          <div style={{ gridColumn: '1 / -1' }}>
            <textarea
              placeholder="请填写物品的隐藏特征，例如：物品内部标记、磨损位置、特殊贴纸、手写文字等。这些信息不会公开展示，仅用于认领时核验失主身份。"
              className="form-textarea"
              style={{ minHeight: '100px', borderColor: form.hiddenInfo ? 'rgba(107,158,122,0.4)' : undefined }}
              value={form.hiddenInfo}
              onChange={(e) => handleChange('hiddenInfo', e.target.value)}
            />
            <div style={{
              marginTop: '6px', padding: '8px 12px', borderRadius: '10px',
              background: 'rgba(107,158,122,0.06)', border: '1px solid rgba(107,158,122,0.12)',
              fontSize: '12px', color: '#4a7a5a', lineHeight: 1.6, display: 'flex', gap: '8px',
            }}>
              <i className="fas fa-shield-halved mt-0.5 text-xs" style={{ color: '#6b9e7a' }}></i>
              <span>
                <strong>什么是隐藏信息？</strong> 填写只有物品持有者才知道的细节特征。认领时，系统会根据这些信息生成验证问题，回答正确才能认领。填写越详细，防冒领效果越好。
              </span>
            </div>
          </div>

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
