import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { locationAreaOptions, publicCategoryOptions } from '@/api/catalog'
import { foundRecordsApi } from '@/api/foundRecords'
import { uploadsApi } from '@/api/uploads'
import type { LocationArea, PublicCategory, RedactionRegion } from '@/api/types'
import { RedactionRegionPicker } from './RedactionRegionPicker'

export type FoundWizardState = 'editing' | 'extracting' | 'confirming' | 'publishing' | 'published'

interface PublicForm {
  name: string
  category: PublicCategory | ''
  location: LocationArea | ''
  eventTime: string
  description: string
}

const initialForm: PublicForm = { name: '', category: '', location: '', eventTime: '', description: '' }

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : '操作失败，请重试'
}

export function FoundWizardPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [state, setState] = useState<FoundWizardState>('editing')
  const [form, setForm] = useState<PublicForm>(initialForm)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [recordId, setRecordId] = useState<string | null>(null)
  const [version, setVersion] = useState<number | null>(null)
  const [originalAssetId, setOriginalAssetId] = useState<string | null>(null)
  const [hiddenDescription, setHiddenDescription] = useState('')
  const [fullNumber, setFullNumber] = useState('')
  const [digitsConfirmed, setDigitsConfirmed] = useState(false)
  const [region, setRegion] = useState<RedactionRegion | null>(null)
  const [identityConfirmed, setIdentityConfirmed] = useState(false)
  const [redactionConfirmed, setRedactionConfirmed] = useState(false)
  const [questionsConfirmed, setQuestionsConfirmed] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [canContinueManually, setCanContinueManually] = useState(false)

  const updateForm = <K extends keyof PublicForm>(key: K, value: PublicForm[K]) => {
    setForm((current) => ({ ...current, [key]: value }))
    setError(null)
    if (key === 'category') {
      setFullNumber('')
      setDigitsConfirmed(false)
      setIdentityConfirmed(false)
      setRedactionConfirmed(false)
      setQuestionsConfirmed(false)
    }
  }

  const selectFile = (nextFile: File | null) => {
    setFile(nextFile)
    setOriginalAssetId(null)
    setRegion(null)
    setRedactionConfirmed(false)
    setCanContinueManually(false)
    setError(null)
    setPreview(nextFile ? URL.createObjectURL(nextFile) : null)
    if (!nextFile && fileInputRef.current) fileInputRef.current.value = ''
  }

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])

  const validateDraft = () => {
    if (!form.category || !form.location || !form.eventTime) return '请选择物品类别、拾取地点和时间'
    const parsed = new Date(form.eventTime)
    return Number.isNaN(parsed.getTime()) ? '请填写有效的拾取时间' : null
  }

  const prepareConfirmation = async () => {
    const validation = validateDraft()
    if (validation) { setError(validation); return }
    setState('extracting')
    setError(null)
    setCanContinueManually(false)
    try {
      let nextId = recordId
      let nextVersion = version
      if (!nextId) {
        const created = await foundRecordsApi.createDraft({ event_time: new Date(form.eventTime).toISOString(), location_area: form.location as LocationArea })
        if (created.version === undefined) throw new Error('服务端未返回草稿版本')
        nextId = created.id
        nextVersion = created.version
        setRecordId(nextId)
        setVersion(nextVersion)
      }
      if (file) {
        let assetId = originalAssetId
        if (!assetId) {
          const uploaded = await uploadsApi.upload(nextId, 'FINDER_ORIGINAL', file)
          assetId = uploaded.image_asset_id
          setOriginalAssetId(assetId)
        }
        try {
          const extraction = await foundRecordsApi.extract(nextId, assetId)
          setForm((current) => ({
            ...current,
            name: current.name.trim() ? current.name : extraction.suggested_name,
            description: current.description.trim() ? current.description : extraction.suggested_description,
          }))
        } catch (extractionError) {
          setError(`AI 识别失败：${errorMessage(extractionError)}`)
          setCanContinueManually(true)
          setState('editing')
          return
        }
      }
      if (nextVersion === null) throw new Error('草稿版本缺失')
      setState('confirming')
    } catch (requestError) {
      setError(errorMessage(requestError))
      setState('editing')
    }
  }

  const validateConfirmation = () => {
    if (!recordId || version === null) return '草稿状态丢失，请重新开始'
    if (!form.category || !form.location || !form.eventTime) return '请选择物品类别、拾取地点和时间'
    if (Number.isNaN(new Date(form.eventTime).getTime())) return '请填写有效的拾取时间'
    if (!form.name.trim() || !form.description.trim()) return '请填写物品名称和公开描述（包含具体楼宇/教室）'
    if (form.name.length > 160) return '物品名称不能超过 160 个字符'
    if (form.description.length > 2000) return '公开描述不能超过 2000 个字符'
    if (form.category === 'IDENTITY_CARD') {
      if (!originalAssetId || !preview) return '证件卡片必须上传原图并选择脱敏区域'
      if (!identityConfirmed && (!fullNumber.trim() || !digitsConfirmed)) return '请填写完整证件号并明确确认数字无误'
      if (!redactionConfirmed && (!region || region.width <= 0 || region.height <= 0)) return '请在原图上选择有效的证件号遮挡区域'
    } else if (!questionsConfirmed && !hiddenDescription.trim()) {
      return '请填写仅失主知道的隐藏特征'
    } else if (hiddenDescription.length > 4000) {
      return '隐藏特征不能超过 4000 个字符'
    }
    return null
  }

  const publish = async () => {
    const validation = validateConfirmation()
    if (validation) { setError(validation); return }
    const id = recordId as string
    setState('publishing')
    setError(null)
    try {
      const confirmed = await foundRecordsApi.confirm(id, {
        expected_version: version as number,
        public_category: form.category as PublicCategory,
        name_public: form.name.trim(),
        description_public: form.description.trim(),
        event_time: new Date(form.eventTime).toISOString(),
        location_area: form.location as LocationArea,
      })
      setVersion(confirmed.version)
      if (form.category === 'IDENTITY_CARD') {
        if (!identityConfirmed) {
          await foundRecordsApi.confirmIdentity(id, fullNumber.trim(), digitsConfirmed)
          setFullNumber('')
          setIdentityConfirmed(true)
        }
        if (!redactionConfirmed) {
          await foundRecordsApi.redact(id, originalAssetId as string, region as RedactionRegion)
          setRedactionConfirmed(true)
        }
      } else if (!questionsConfirmed) {
        await foundRecordsApi.confirmQuestions(id, hiddenDescription.trim())
        setQuestionsConfirmed(true)
      }
      const result = await foundRecordsApi.publish(id, confirmed.version)
      setVersion(result.version ?? confirmed.version)
      setState('published')
      navigate(`/found/${encodeURIComponent(id)}`)
    } catch (requestError) {
      setError(errorMessage(requestError))
      setState('confirming')
    }
  }

  const busy = state === 'extracting' || state === 'publishing'
  return (
    <div className="page-shell">
      <div className="page-title">我要招领</div>
      <div className="form-container">
        <section>
          <input ref={fileInputRef} aria-label="选择物品图片" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => selectFile(event.target.files?.[0] ?? null)} className="hidden" />
          {preview ? (
            <div>
              <img src={preview} alt="招领图片预览" className="w-full max-h-80 object-contain rounded-xl" />
              {state === 'editing' ? <div className="flex gap-2 mt-2"><button type="button" className="btn btn-secondary" onClick={() => fileInputRef.current?.click()}>更换图片</button><button type="button" className="btn btn-secondary" onClick={() => selectFile(null)}>移除图片</button></div> : null}
            </div>
          ) : <button type="button" className="upload-area w-full" onClick={() => fileInputRef.current?.click()}><span className="plus">+</span><span className="text block">上传图片</span><span className="text-xs">选择后仅本地预览，提交草稿时才上传</span></button>}
        </section>

        <form className="form-fields" onSubmit={(event) => { event.preventDefault(); if (state === 'editing') void prepareConfirmation(); else if (state === 'confirming') void publish() }}>
          <input className="form-input" placeholder="物品名称" maxLength={160} value={form.name} onChange={(event) => updateForm('name', event.target.value)} disabled={busy} />
          <select className="form-select" aria-label="物品类别" value={form.category} onChange={(event) => updateForm('category', event.target.value as PublicCategory | '')} disabled={busy}>
            <option value="">物品类别（下拉选择）</option>{publicCategoryOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
          <select className="form-select" aria-label="拾取地点" value={form.location} onChange={(event) => updateForm('location', event.target.value as LocationArea | '')} disabled={busy}>
            <option value="">拾取地点（下拉选择）</option>{locationAreaOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
          <input aria-label="拾取时间" type="datetime-local" className="form-input" value={form.eventTime} onChange={(event) => updateForm('eventTime', event.target.value)} disabled={busy} />
          <textarea className="form-textarea" maxLength={2000} placeholder="公开描述（请写明具体楼宇、楼层或教室）" value={form.description} onChange={(event) => updateForm('description', event.target.value)} disabled={busy} />

          {state === 'confirming' && form.category !== 'IDENTITY_CARD' ? <textarea className="form-textarea" maxLength={4000} style={{ gridColumn: '1 / -1' }} placeholder="隐藏特征（仅用于生成认领问题，不会公开或进入匹配向量）" value={hiddenDescription} onChange={(event) => { setHiddenDescription(event.target.value); setQuestionsConfirmed(false) }} /> : null}
          {state === 'confirming' && form.category === 'IDENTITY_CARD' ? (
            <div style={{ gridColumn: '1 / -1' }} className="space-y-3">
              {!identityConfirmed ? <><input aria-label="完整证件号" className="form-input w-full" type="password" autoComplete="off" value={fullNumber} onChange={(event) => { setFullNumber(event.target.value); setIdentityConfirmed(false) }} /><label className="flex gap-2"><input type="checkbox" checked={digitsConfirmed} onChange={(event) => setDigitsConfirmed(event.target.checked)} />我已逐位核对，确认证件号数字无误</label></> : <p role="status">证件号已安全确认，完整号码已从页面清除。</p>}
              {preview && !redactionConfirmed ? <RedactionRegionPicker src={preview} value={region} onChange={(next) => { setRegion(next); setRedactionConfirmed(false) }} /> : redactionConfirmed ? <p role="status">脱敏图片已确认。</p> : null}
            </div>
          ) : null}
          {state === 'publishing' && form.category === 'IDENTITY_CARD' && identityConfirmed ? <p role="status" style={{ gridColumn: '1 / -1' }}>证件号已安全确认，完整号码已从页面清除。</p> : null}

          {error ? <div role="alert" className="callout callout-warning" style={{ gridColumn: '1 / -1' }}>{error}</div> : null}
          {state === 'editing' && canContinueManually ? <button type="button" className="btn btn-secondary" onClick={() => { setError(null); setState('confirming') }}>跳过 AI，手工填写</button> : null}
          {state === 'confirming' ? <button type="button" className="btn btn-secondary" onClick={() => { setError(null); setState('editing') }}>返回编辑</button> : null}
          <button type="submit" className="submit-btn" disabled={busy || state === 'published'}>{state === 'extracting' ? 'AI 识别中...' : state === 'publishing' ? '发布中...' : state === 'confirming' ? '确认信息并发布' : '创建草稿并继续'}</button>
        </form>
      </div>
      <div className="page-slogan">物归原主，屿过天晴</div>
    </div>
  )
}
