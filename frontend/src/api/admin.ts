import { apiClient, isMockMode } from './client'
import { mockApi } from './mock'
import type { AdminDecision, AuditEvent, ReviewDetail, ReviewQueueItem } from './types'

export const adminApi = {
  async reviews(): Promise<ReviewQueueItem[]> {
    if (isMockMode) return mockApi.unsupported('管理员复核队列')
    return (await apiClient.get<ReviewQueueItem[]>('/api/admin/reviews')).data
  },

  async review(reviewId: string): Promise<ReviewDetail> {
    if (isMockMode) return mockApi.unsupported('管理员复核详情')
    return (await apiClient.get<ReviewDetail>(`/api/admin/reviews/${reviewId}`)).data
  },

  async decide(reviewId: string, request: { decision: AdminDecision; reason: string; candidate_id?: string }, idempotencyKey: string) {
    if (isMockMode) return mockApi.unsupported('管理员复核决定')
    return (await apiClient.post(`/api/admin/reviews/${reviewId}/decision`, request, {
      headers: { 'Idempotency-Key': idempotencyKey },
    })).data
  },

  async audit(): Promise<AuditEvent[]> {
    if (isMockMode) return mockApi.unsupported('审计事件')
    return (await apiClient.get<AuditEvent[]>('/api/admin/audit-events')).data
  },
}
