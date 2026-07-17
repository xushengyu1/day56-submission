import { apiClient, isMockMode } from './client'
import { mockApi } from './mock'
import type { CreatedRecord, FoundConfirmation, FoundDraftCreate, FoundExtraction, ItemRecord } from './types'

export const foundRecordsApi = {
  async createDraft(request: FoundDraftCreate): Promise<CreatedRecord> {
    if (isMockMode) return mockApi.unsupported('招领草稿创建')
    return (await apiClient.post<CreatedRecord>('/api/found-records', request)).data
  },

  async get(recordId: string): Promise<ItemRecord> {
    if (isMockMode) return mockApi.getFoundItemDetail(recordId).then((record) => record ?? mockApi.unsupported('招领详情'))
    return (await apiClient.get<ItemRecord>(`/api/found-records/${recordId}`)).data
  },

  async extract(recordId: string, imageAssetId: string): Promise<FoundExtraction> {
    if (isMockMode) return mockApi.unsupported('图片提取')
    return (await apiClient.post<FoundExtraction>(`/api/found-records/${recordId}/extract`, { image_asset_id: imageAssetId })).data
  },

  async confirm(recordId: string, request: FoundConfirmation): Promise<{ id: string; version: number }> {
    if (isMockMode) return mockApi.unsupported('招领确认')
    return (await apiClient.put<{ id: string; version: number }>(`/api/found-records/${recordId}/confirmation`, request)).data
  },

  async confirmIdentity(recordId: string, fullNumber: string, digitsConfirmed: boolean): Promise<{ number_masked: string }> {
    if (isMockMode) return mockApi.unsupported('证件确认')
    return (await apiClient.post<{ number_masked: string }>(`/api/found-records/${recordId}/identity-confirmation`, {
      full_number: fullNumber,
      digits_confirmed: digitsConfirmed,
    })).data
  },

  async confirmQuestions(recordId: string, hiddenDescription: string): Promise<{ verification_set_id: string }> {
    if (isMockMode) return mockApi.unsupported('隐藏问题确认')
    return (await apiClient.post<{ verification_set_id: string }>(`/api/found-records/${recordId}/questions`, { hidden_description: hiddenDescription })).data
  },

  async publish(recordId: string, expectedVersion: number): Promise<CreatedRecord> {
    if (isMockMode) return mockApi.unsupported('招领发布')
    return (await apiClient.post<CreatedRecord>(`/api/found-records/${recordId}/publish`, { expected_version: expectedVersion })).data
  },
}
