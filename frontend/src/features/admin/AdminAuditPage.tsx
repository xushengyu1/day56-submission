const MOCK_AUDIT_EVENTS = [
  { id: 'ae-001', type: 'HANDOFF_COMPLETE', actor: '李同学', target: 'FR-20260716-003', detail: '拾得者确认已完成线下交接，物品已归还失主', time: '2026-07-16 16:30' },
  { id: 'ae-002', type: 'CLAIM_APPROVED', actor: '王管理员', target: 'CLM-20260716-001', detail: '多人认领复核通过，确认张同学认领', time: '2026-07-16 16:00' },
  { id: 'ae-003', type: 'ADMIN_DECISION', actor: '王管理员', target: 'RV-20260716-001', detail: '管理员驳回孙同学的认领申请，隐藏特征回答不匹配', time: '2026-07-16 15:45' },
  { id: 'ae-004', type: 'CLAIM_SUBMITTED', actor: '张同学', target: 'CLM-20260716-001', detail: '失主发起认领申请，提交隐藏特征回答', time: '2026-07-16 14:30' },
  { id: 'ae-005', type: 'REVIEW_SUBMITTED', actor: '孙同学', target: 'RV-20260716-001', detail: '认领核验未通过，提交认领复核申请', time: '2026-07-16 14:00' },
  { id: 'ae-006', type: 'MATCH_GENERATED', actor: '系统', target: 'LR-20260716-001', detail: '为失物"黑色折叠伞"生成 3 个候选匹配', time: '2026-07-16 14:05' },
  { id: 'ae-007', type: 'FOUND_PUBLISHED', actor: '李同学', target: 'FR-20260716-003', detail: '拾得者发布招领信息：黑色折叠伞', time: '2026-07-16 11:00' },
  { id: 'ae-008', type: 'VERIFICATION_PASSED', actor: '系统', target: 'FR-20260716-002', detail: '身份证件核验通过，号码 HMAC 精确匹配', time: '2026-07-16 10:30' },
  { id: 'ae-009', type: 'LOST_PUBLISHED', actor: '张同学', target: 'LR-20260716-001', detail: '失主发布失物信息：黑色折叠伞', time: '2026-07-16 09:00' },
  { id: 'ae-010', type: 'FOUND_PUBLISHED', actor: '王同学', target: 'FR-20260715-002', detail: '拾得者发布招领信息：居民身份证', time: '2026-07-15 12:30' },
  { id: 'ae-011', type: 'VERIFICATION_FAILED', actor: '系统', target: 'CLM-20260715-003', detail: '普通物品核验未通过，隐藏特征回答存在关键冲突', time: '2026-07-15 11:20' },
  { id: 'ae-012', type: 'LOST_PUBLISHED', actor: '赵同学', target: 'LR-20260715-003', detail: '失主发布失物信息：蓝色水杯', time: '2026-07-15 10:00' },
]

const EVENT_CONFIG: Record<string, { label: string; color: string; bg: string; icon: string }> = {
  CLAIM_APPROVED: { label: '认领通过', color: '#6b9e7a', bg: 'rgba(107,158,122,0.1)', icon: 'fa-check-circle' },
  HANDOFF_COMPLETE: { label: '交接完成', color: '#4a7a5a', bg: 'rgba(74,122,90,0.1)', icon: 'fa-handshake' },
  CLAIM_SUBMITTED: { label: '提交认领', color: '#c4a35a', bg: 'rgba(196,163,90,0.1)', icon: 'fa-paper-plane' },
  FOUND_PUBLISHED: { label: '招领发布', color: '#6b8ba4', bg: 'rgba(107,139,164,0.1)', icon: 'fa-hand-holding-heart' },
  LOST_PUBLISHED: { label: '寻物发布', color: '#8b7bb0', bg: 'rgba(139,123,176,0.1)', icon: 'fa-box-open' },
  VERIFICATION_PASSED: { label: '核验通过', color: '#6b9e7a', bg: 'rgba(107,158,122,0.1)', icon: 'fa-shield-check' },
  VERIFICATION_FAILED: { label: '核验失败', color: '#b85c5c', bg: 'rgba(184,92,92,0.1)', icon: 'fa-shield-xmark' },
  MATCH_GENERATED: { label: '匹配生成', color: '#6b8ba4', bg: 'rgba(107,139,164,0.1)', icon: 'fa-link' },
  ADMIN_DECISION: { label: '管理员决定', color: '#8b7bb0', bg: 'rgba(139,123,176,0.1)', icon: 'fa-gavel' },
  REVIEW_SUBMITTED: { label: '提交复核', color: '#c4a35a', bg: 'rgba(196,163,90,0.1)', icon: 'fa-flag' },
}

export function AdminAuditPage() {
  return (
    <div>
      {/* 页面标题 */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.02em' }}>审计日志</h2>
        <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>系统操作的完整时间线记录</p>
      </div>

      {/* 时间线 */}
      <div className="glass-card" style={{ padding: '28px', borderRadius: '24px' }}>
        <div style={{ position: 'relative' }}>
          {/* 竖线 */}
          <div style={{
            position: 'absolute', left: '18px', top: '36px', bottom: '0',
            width: '2px', background: 'rgba(148,163,184,0.15)'
          }}></div>

          {MOCK_AUDIT_EVENTS.map((event) => {
            const config = EVENT_CONFIG[event.type] || { label: event.type, color: '#7a8e9e', bg: 'rgba(122,142,158,0.1)', icon: 'fa-circle' }
            return (
              <div key={event.id} style={{
                position: 'relative', display: 'flex', gap: '16px', marginBottom: '20px',
                paddingLeft: '0'
              }}>
                {/* 圆点 */}
                <div style={{
                  width: '38px', height: '38px', borderRadius: '50%', flexShrink: 0,
                  background: config.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  zIndex: 1, border: `2px solid ${config.color}20`
                }}>
                  <i className={`fas ${config.icon}`} style={{ color: config.color, fontSize: '13px' }}></i>
                </div>

                {/* 内容卡片 */}
                <div style={{
                  flex: 1, padding: '16px 18px', borderRadius: '16px',
                  background: 'rgba(248,250,252,0.6)', border: '1px solid rgba(226,232,240,0.5)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <p style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)' }}>{event.detail}</p>
                    <span style={{ fontSize: '11px', color: 'var(--muted)', whiteSpace: 'nowrap', marginLeft: '12px' }}>{event.time}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '12px', color: 'var(--muted)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <i className="fas fa-user text-[10px]"></i>{event.actor}
                    </span>
                    <span style={{
                      padding: '2px 8px', borderRadius: '999px', fontSize: '10px', fontWeight: 700,
                      background: config.bg, color: config.color
                    }}>
                      {config.label}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
