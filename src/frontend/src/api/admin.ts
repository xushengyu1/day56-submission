import { apiClient, isMockMode } from './client'
import { mockApi } from './mock'
import type {
  AdminDecisionRequest,
  AuditEvent,
  ReviewDecisionResult,
  ReviewDetail,
  ReviewQueueItem,
} from './types'

export interface PaginatedAuditResponse {
  items: AuditEvent[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const adminApi = {
  async reviews(): Promise<ReviewQueueItem[]> {
    if (isMockMode) return mockApi.unsupported('管理员复核队列')
    return (await apiClient.get<ReviewQueueItem[]>('/api/admin/reviews')).data
  },

  async review(reviewId: string): Promise<ReviewDetail> {
    if (isMockMode) return mockApi.unsupported('管理员复核详情')
    return (await apiClient.get<ReviewDetail>(`/api/admin/reviews/${reviewId}`)).data
  },

  async decide(
    reviewId: string,
    request: AdminDecisionRequest,
    idempotencyKey: string,
  ): Promise<ReviewDecisionResult> {
    if (isMockMode) return mockApi.unsupported('管理员复核决定')
    return (await apiClient.post<ReviewDecisionResult>(`/api/admin/reviews/${reviewId}/decision`, request, {
      headers: { 'Idempotency-Key': idempotencyKey },
    })).data
  },

  async audit(page: number = 1, pageSize: number = 5): Promise<PaginatedAuditResponse> {
    if (isMockMode) return mockApi.unsupported('审计事件')
    return (await apiClient.get<PaginatedAuditResponse>('/api/admin/audit-events', {
      params: { page, page_size: pageSize },
    })).data
  },
}
