import { apiClient, isMockMode } from './client'
import { mockApi, toCandidatePublic } from './mock'
import type { CandidatePublic } from './types'

export const candidatesApi = {
  async get(candidateId: string): Promise<CandidatePublic> {
    if (isMockMode) {
      const candidate = await mockApi.getCandidateDetail(candidateId)
      return candidate ? toCandidatePublic(candidate) : mockApi.unsupported('候选详情')
    }
    return (await apiClient.get<CandidatePublic>(`/api/candidates/${candidateId}`)).data
  },
}
