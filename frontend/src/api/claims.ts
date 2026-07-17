import { apiClient, isMockMode } from './client'
import { mockApi } from './mock'
import type { ClaimDetail, ClaimOutcome, QuestionPublic } from './types'

export const claimsApi = {
  async get(claimId: string): Promise<ClaimDetail> {
    if (isMockMode) return mockApi.unsupported('认领详情')
    return (await apiClient.get<ClaimDetail>(`/api/claims/${claimId}`)).data
  },

  async questions(candidateId: string): Promise<QuestionPublic[]> {
    if (isMockMode) return mockApi.unsupported('认领问题')
    return (await apiClient.get<QuestionPublic[]>(`/api/candidates/${candidateId}/questions`)).data
  },

  async verifyIdentity(candidateId: string, fullNumber: string): Promise<ClaimOutcome> {
    if (isMockMode) return mockApi.unsupported('证件认领核验')
    return (await apiClient.post<ClaimOutcome>(`/api/candidates/${candidateId}/claims/identity`, { full_number: fullNumber })).data
  },

  async verifyAnswers(candidateId: string, answers: Array<{ question_id: string; answer: string }>): Promise<ClaimOutcome> {
    if (isMockMode) return mockApi.unsupported('问题认领核验')
    return (await apiClient.post<ClaimOutcome>(`/api/candidates/${candidateId}/claims/answers`, { answers })).data
  },

  async createReview(claimId: string, reason: string): Promise<{ id: string; status: string }> {
    if (isMockMode) return mockApi.unsupported('认领复核')
    return (await apiClient.post<{ id: string; status: string }>(`/api/claims/${claimId}/review-requests`, { reason })).data
  },

  async contact(claimId: string): Promise<{ finder_phone: string; finder_email: string }> {
    if (isMockMode) return mockApi.unsupported('交接联系方式')
    return (await apiClient.get<{ finder_phone: string; finder_email: string }>(`/api/claims/${claimId}/contact`)).data
  },

  async completeHandoff(claimId: string, idempotencyKey: string): Promise<{ claim_id: string; status: string }> {
    if (isMockMode) return mockApi.unsupported('完成交接')
    return (await apiClient.post<{ claim_id: string; status: string }>(`/api/claims/${claimId}/handoff-complete`, {
      confirmation: true,
    }, { headers: { 'Idempotency-Key': idempotencyKey } })).data
  },
}
