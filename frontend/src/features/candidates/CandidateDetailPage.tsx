import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { candidatesApi } from '@/api/candidates'
import { locationAreaLabel } from '@/api/catalog'
import { isApiError } from '@/api/errors'
import { useAssetObjectUrl } from '@/hooks/useAssetObjectUrl'
import { conflictCodeLabel, formatCandidateScore, reasonCodeLabel } from './display'

export function CandidateDetailPage() {
  const { id = '' } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const query = useQuery({
    queryKey: ['candidates', 'detail', id],
    queryFn: () => candidatesApi.get(id),
    enabled: Boolean(id),
  })
  const image = useAssetObjectUrl(query.data?.found_record.public_image_asset_id)

  if (!id) return <div className="flex items-center justify-center h-full">候选不存在</div>
  if (query.isLoading) return <div className="flex items-center justify-center h-full">正在加载候选...</div>
  if (isApiError(query.error) && query.error.status === 404) return <div className="flex items-center justify-center h-full">候选不存在</div>
  if (query.isError) return <div className="flex flex-col gap-3 items-center justify-center h-full" role="alert"><p>候选加载失败</p><button type="button" className="btn btn-secondary" onClick={() => void query.refetch()}>重试加载</button></div>
  if (!query.data) return <div className="flex items-center justify-center h-full">候选不存在</div>

  const candidate = query.data
  const found = candidate.found_record
  const handleClaim = () => navigate(found.item_type === 'IDENTITY_DOCUMENT' ? `/claims/identity/${candidate.id}` : `/claims/other/${candidate.id}`)

  return (
    <div className="h-full flex overflow-hidden" style={{ background: 'var(--color-neutral-50)' }}>
      <aside className="w-[320px] flex-shrink-0 border-r overflow-y-auto p-5" style={{ background: 'white', borderColor: 'var(--color-neutral-200)' }}>
        <div className="w-full h-48 rounded-xl overflow-hidden mb-4" style={{ background: 'var(--color-neutral-100)' }}>
          {image.url ? <img src={image.url} alt={found.name_public ?? '候选物品'} className="w-full h-full object-cover" /> : <span className="h-full flex items-center justify-center text-xs" style={{ color: 'var(--muted)' }}>{image.loading ? '图片加载中' : image.error ? '图片加载失败' : '暂无图片'}</span>}
        </div>
        <div className="flex items-center gap-3 mb-3">
          <div><span className="text-3xl font-bold" style={{ color: '#4a7a5a' }}>{formatCandidateScore(candidate.total_score)}</span><span className="text-sm"> 分</span></div>
          <span className="badge">{candidate.level === 'HIGH' ? '高匹配' : candidate.level === 'MEDIUM' ? '中匹配' : '低匹配'}</span>
          <span className="badge">{found.item_type === 'IDENTITY_DOCUMENT' ? '身份证件' : '其他物品'}</span>
        </div>
        <h2 className="text-lg font-bold">{found.name_public ?? '未命名物品'}</h2>
        <div className="mt-3 space-y-2 text-xs">
          <p><strong>发现时间：</strong>{found.event_time_public ?? '未填写'}</p>
          <p><strong>发现地点：</strong>{found.location_public ?? locationAreaLabel(found.location_area)}</p>
        </div>
        <div className="mt-4 p-3 rounded-lg" style={{ background: 'var(--color-neutral-50)' }}>
          <p className="text-[10px] mb-1" style={{ color: 'var(--muted)' }}>公开描述</p>
          <p className="text-xs">{found.description_public ?? '暂无公开描述'}</p>
        </div>
        <div className="mt-5 space-y-2">
          <button type="button" onClick={handleClaim} className="btn btn-primary w-full">发起认领</button>
          <Link to={`/lost/${candidate.lost_record_id}/candidates`} className="btn btn-secondary w-full text-center block">返回列表</Link>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-xl mx-auto px-6 py-5 space-y-5">
          <section>
            <h3 className="text-xs font-semibold mb-2.5" style={{ color: '#4a7a5a' }}>匹配点</h3>
            {candidate.reason_codes.length === 0 ? <p className="text-xs">暂无可展示的匹配点</p> : <div className="space-y-1.5">{candidate.reason_codes.map((code) => <div key={code} className="px-3 py-2 rounded-md text-xs" style={{ background: 'rgba(107,158,122,0.06)' }}>{reasonCodeLabel(code)}</div>)}</div>}
          </section>
          {candidate.conflict_codes.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold mb-2.5" style={{ color: '#8a7040' }}>冲突点</h3>
              <div className="space-y-1.5">{candidate.conflict_codes.map((code) => <div key={code} className="px-3 py-2 rounded-md text-xs" style={{ background: 'rgba(196,163,90,0.06)' }}>{conflictCodeLabel(code)}</div>)}</div>
            </section>
          )}
          <section>
            <h3 className="text-xs font-semibold mb-2.5">匹配总分</h3>
            <div className="card p-4"><strong className="text-2xl">{formatCandidateScore(candidate.total_score)}</strong><p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>综合考虑物品描述、时间、地点等公开信息</p></div>
          </section>
          <div className="callout callout-info text-[11px]">匹配分表示信息相似程度，不代表物品归属确认。认领需通过隐藏特征核验。</div>
        </div>
      </main>
    </div>
  )
}
