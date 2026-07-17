import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/api/admin'

export function AdminAuditPage() {
  const auditQuery = useQuery({ queryKey: ['admin', 'audit'], queryFn: adminApi.audit })

  return (
    <div>
      <header style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 800 }}>审计日志</h2>
        <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>系统返回的脱敏审计时间线</p>
      </header>
      <div className="glass-card" style={{ padding: '28px', borderRadius: '24px' }}>
        {auditQuery.isLoading && <p className="text-center py-12">正在加载审计日志...</p>}
        {auditQuery.isError && <p role="alert" className="text-center py-12">审计日志加载失败</p>}
        {auditQuery.data?.length === 0 && <p className="text-center py-12">暂无审计事件</p>}
        {auditQuery.data?.map((event) => (
          <article key={event.event_id} className="border-b last:border-0 py-4">
            <div className="flex justify-between gap-4">
              <h3 className="font-bold">{event.event_type}</h3>
              <time className="text-xs text-gray-500">{new Date(event.created_at).toLocaleString('zh-CN')}</time>
            </div>
            <p className="text-sm mt-2">{event.aggregate_type} · {event.aggregate_id}</p>
            <p className="text-sm mt-1">{event.result_code}</p>
            {Object.keys(event.metadata_redacted).length > 0 && <p className="text-xs text-gray-500 mt-2">{JSON.stringify(event.metadata_redacted)}</p>}
          </article>
        ))}
      </div>
    </div>
  )
}
