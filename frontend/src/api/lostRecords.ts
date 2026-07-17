import { apiClient, isMockMode } from './client'
import { mockApi } from './mock'
import type { CreatedRecord, ItemRecord, LostRecordCreate, MatchCandidate } from './types'

export const lostRecordsApi = {
  async create(request: LostRecordCreate): Promise<CreatedRecord> {
    if (isMockMode) return mockApi.unsupported('寻物发布')
    return (await apiClient.post<CreatedRecord>('/api/lost-records', request)).data
  },

  async get(recordId: string): Promise<ItemRecord> {
    if (isMockMode) return mockApi.getItemDetail(recordId).then((record) => record ?? mockApi.unsupported('寻物详情'))
    return (await apiClient.get<ItemRecord>(`/api/lost-records/${recordId}`)).data
  },

  async candidates(recordId: string): Promise<MatchCandidate[]> {
    if (isMockMode) return mockApi.getCandidates(recordId)
    return (await apiClient.get<MatchCandidate[]>(`/api/lost-records/${recordId}/candidates`)).data
  },

  async createReview(recordId: string, reason: string): Promise<{ id: string; status: string }> {
    if (isMockMode) return mockApi.unsupported('寻物复核')
    return (await apiClient.post<{ id: string; status: string }>(`/api/lost-records/${recordId}/review-requests`, { reason })).data
  },
}
