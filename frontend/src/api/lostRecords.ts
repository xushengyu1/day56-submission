import { apiClient, isMockMode } from './client'
import { mockApi, toCandidatePublic, toItemRecordPublic } from './mock'
import type { CandidatePublic, CreatedRecord, ItemRecordPublic, LostRecordCreate } from './types'

export const lostRecordsApi = {
  async create(request: LostRecordCreate): Promise<CreatedRecord> {
    if (isMockMode) return mockApi.unsupported('寻物发布')
    return (await apiClient.post<CreatedRecord>('/api/lost-records', request)).data
  },

  async get(recordId: string): Promise<ItemRecordPublic> {
    if (isMockMode) return mockApi.getItemDetail(recordId).then((record) => record ? toItemRecordPublic(record) : mockApi.unsupported('寻物详情'))
    return (await apiClient.get<ItemRecordPublic>(`/api/lost-records/${recordId}`)).data
  },

  async candidates(recordId: string): Promise<CandidatePublic[]> {
    if (isMockMode) return (await mockApi.getCandidates(recordId)).map(toCandidatePublic)
    return (await apiClient.get<CandidatePublic[]>(`/api/lost-records/${recordId}/candidates`)).data
  },

  async createReview(recordId: string, reason: string): Promise<{ id: string; status: string }> {
    if (isMockMode) return mockApi.unsupported('寻物复核')
    return (await apiClient.post<{ id: string; status: string }>(`/api/lost-records/${recordId}/review-requests`, { reason })).data
  },
}
