import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { mockApi } from '@/api/mock'

export function CandidateDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: candidate } = useQuery({
    queryKey: ['candidate', id],
    queryFn: () => mockApi.getCandidateDetail(id || ''),
  })

  if (!candidate) {
    return (
      <div className="flex items-center justify-center h-full" style={{ background: 'var(--color-neutral-50)' }}>
        <p style={{ color: 'var(--color-neutral-400)' }}>候选不存在</p>
      </div>
    )
  }

  const handleClaim = () => {
    if (candidate.found_record.item_type === 'IDENTITY_DOCUMENT') {
      navigate(`/claims/identity/${candidate.id}`)
    } else {
      navigate(`/claims/other/${candidate.id}`)
    }
  }

  return (
    <div className="h-full flex overflow-hidden" style={{ background: 'var(--color-neutral-50)' }}>
      {/* 左侧物品信息 */}
      <div className="w-[320px] flex-shrink-0 border-r overflow-y-auto p-5"
        style={{ background: 'white', borderColor: 'var(--color-neutral-200)' }}
      >
        <div className="w-full h-48 rounded-xl overflow-hidden mb-4"
          style={{ background: 'var(--color-neutral-100)' }}
        >
          <img src="https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=320&h=192&fit=crop"
            alt="物品" className="w-full h-full object-cover"
          />
        </div>

        {/* 分数醒目展示 */}
        <div className="flex items-center gap-3 mb-3">
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold" style={{ color: '#4a7a5a', letterSpacing: '-0.03em' }}>
              {candidate.total_score}
            </span>
            <span className="text-sm font-medium" style={{ color: '#6b9e7a' }}>分</span>
          </div>
          <span style={{
            padding: '3px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
            background: candidate.total_score >= 80 ? 'rgba(107,158,122,0.1)' : candidate.total_score >= 60 ? 'rgba(107,139,164,0.1)' : 'rgba(148,163,184,0.1)',
            color: candidate.total_score >= 80 ? '#4a7a5a' : candidate.total_score >= 60 ? '#4a6b82' : '#7a8e9e',
          }}>
            {candidate.total_score >= 80 ? '高匹配' : candidate.total_score >= 60 ? '中匹配' : '低匹配'}
          </span>
          <span style={{
            padding: '3px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
            background: 'rgba(148,163,184,0.1)', color: '#7a8e9e',
          }}>
            {candidate.found_record.item_type === 'IDENTITY_DOCUMENT' ? '身份证件' : '其他物品'}
          </span>
        </div>

        <h2 className="text-lg font-bold" style={{ color: 'var(--color-neutral-900)', letterSpacing: '-0.02em' }}>
          {candidate.found_record.name_public}
        </h2>

        <div className="mt-3 space-y-2.5">
          {[
            { icon: 'fa-clock', label: '发现时间', value: candidate.found_record.event_time_public },
            { icon: 'fa-location-dot', label: '发现地点', value: candidate.found_record.location_public },
          ].map((item) => (
            <div key={item.icon} className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-md flex items-center justify-center"
                style={{ background: 'rgba(107,139,164,0.1)' }}
              >
                <i className={`fas ${item.icon} text-[11px]`} style={{ color: '#4a6b82' }}></i>
              </div>
              <div>
                <p className="text-[10px]" style={{ color: 'var(--color-neutral-400)' }}>{item.label}</p>
                <p className="text-xs font-medium" style={{ color: 'var(--color-neutral-700)' }}>{item.value}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 p-3 rounded-lg" style={{ background: 'var(--color-neutral-50)' }}>
          <p className="text-[10px] font-medium mb-0.5" style={{ color: 'var(--color-neutral-400)' }}>公开描述</p>
          <p className="text-xs" style={{ color: 'var(--color-neutral-700)' }}>{candidate.found_record.description_public}</p>
        </div>

        {/* 操作按钮 */}
        <div className="mt-5 space-y-2">
          <button onClick={handleClaim} className="btn btn-primary w-full py-2.5 text-sm">
            <i className="fas fa-hand-point-right text-xs"></i> 发起认领
          </button>
          <Link to={`/lost/${candidate.lost_record_id}/candidates`} className="btn btn-secondary w-full py-2 text-xs text-center block">
            返回列表
          </Link>
        </div>
      </div>

      {/* 右侧匹配详情 */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-xl mx-auto px-6 py-5 space-y-5">
          {/* 匹配点 */}
          <section>
            <h3 className="text-xs font-semibold flex items-center gap-1.5 mb-2.5"
              style={{ color: '#4a7a5a', letterSpacing: '0.03em' }}
            >
              <i className="fas fa-circle-check text-[10px]"></i> 匹配点
            </h3>
            <div className="space-y-1.5">
              {candidate.reason_texts.map((point, i) => (
                <div key={i} className="flex items-start gap-2.5 px-3 py-2 rounded-md"
                  style={{ background: 'rgba(107,158,122,0.06)' }}
                >
                  <div className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                    style={{ background: 'rgba(107,158,122,0.15)' }}
                  >
                    <i className="fas fa-check text-[8px]" style={{ color: '#4a7a5a' }}></i>
                  </div>
                  <p className="text-xs" style={{ color: '#3a6a4a' }}>{point}</p>
                </div>
              ))}
            </div>
          </section>

          {/* 冲突点 */}
          {candidate.conflict_texts.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold flex items-center gap-1.5 mb-2.5"
                style={{ color: '#8a7040', letterSpacing: '0.03em' }}
              >
                <i className="fas fa-triangle-exclamation text-[10px]"></i> 冲突点
              </h3>
              <div className="space-y-1.5">
                {candidate.conflict_texts.map((point, i) => (
                  <div key={i} className="flex items-start gap-2.5 px-3 py-2 rounded-md"
                    style={{ background: 'rgba(196,163,90,0.06)' }}
                  >
                    <div className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                      style={{ background: 'rgba(196,163,90,0.15)' }}
                    >
                      <i className="fas fa-exclamation text-[8px]" style={{ color: '#8a7040' }}></i>
                    </div>
                    <p className="text-xs" style={{ color: '#6a5a2a' }}>{point}</p>
                  </div>
                ))}
              </div>

              {/* 保留原因 */}
              <div className="mt-2.5 px-3 py-2.5 rounded-md border"
                style={{ background: 'rgba(107,139,164,0.04)', borderColor: 'rgba(107,139,164,0.12)' }}
              >
                <p className="text-[10px] font-semibold mb-0.5" style={{ color: '#4a6b82' }}>
                  <i className="fas fa-lightbulb mr-1"></i> 保留原因
                </p>
                <p className="text-xs" style={{ color: '#3a5a72' }}>{candidate.retention_reason}</p>
              </div>
            </section>
          )}

          {/* 匹配总分 */}
          <section>
            <h3 className="text-xs font-semibold mb-2.5"
              style={{ color: 'var(--color-neutral-500)', letterSpacing: '0.03em' }}
            >
              匹配总分
            </h3>
            <div className="card p-4">
              <div className="flex items-center gap-4">
                <div style={{
                  width: '64px', height: '64px', borderRadius: '16px',
                  background: candidate.total_score >= 80 ? 'rgba(107,158,122,0.1)' : candidate.total_score >= 60 ? 'rgba(107,139,164,0.1)' : 'rgba(148,163,184,0.1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <span className="text-2xl font-bold" style={{
                    color: candidate.total_score >= 80 ? '#4a7a5a' : candidate.total_score >= 60 ? '#4a6b82' : '#7a8e9e',
                  }}>{candidate.total_score}</span>
                </div>
                <div>
                  <p className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                    {candidate.total_score >= 80 ? '高度匹配' : candidate.total_score >= 60 ? '中度匹配' : '低度匹配'}
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                    综合考虑物品描述、时间、地点等公开信息的相似程度
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* 声明 */}
          <div className="callout callout-info text-[11px]">
            <i className="fas fa-circle-info text-[10px] mt-0.5"></i>
            <span>匹配分表示信息相似程度，不代表物品归属确认。认领需通过隐藏特征核验。</span>
          </div>
        </div>
      </div>
    </div>
  )
}
