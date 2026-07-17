import { apiClient, isMockMode } from './client'
import { locationAreaLabel } from './catalog'
import { mockApi } from './mock'
import type { ItemRecord, LocationArea, PaginatedResponse, RecordKind, TimelineEvent } from './types'

export const recordsApi = {
  async recent(limit = 5): Promise<ItemRecord[]> {
    return isMockMode
      ? mockApi.getRecentItems(limit)
      : (await apiClient.get<ItemRecord[]>('/api/records/recent', { params: { limit } })).data
  },

  async list(locationArea?: LocationArea, page = 1, pageSize = 20): Promise<PaginatedResponse<ItemRecord>> {
    if (isMockMode) {
      const result = await mockApi.getItemsByLocation(locationArea ? locationAreaLabel(locationArea) : '', page, pageSize)
      return { ...result, page, page_size: pageSize }
    }
    return (await apiClient.get<PaginatedResponse<ItemRecord>>('/api/records', {
      params: { location_area: locationArea, page, page_size: pageSize },
    })).data
  },

  async mine(kind?: RecordKind, page = 1, pageSize = 20): Promise<PaginatedResponse<ItemRecord>> {
    if (isMockMode) {
      const items = (await mockApi.getMyRecords()).filter((record) => !kind || record.kind === kind)
      return { items, total: items.length, page, page_size: pageSize }
    }
    return (await apiClient.get<PaginatedResponse<ItemRecord>>('/api/records/mine', {
      params: { kind, page, page_size: pageSize },
    })).data
  },

  async timeline(recordId: string): Promise<TimelineEvent[]> {
    if (isMockMode) return mockApi.unsupported('记录时间线')
    return (await apiClient.get<TimelineEvent[]>(`/api/records/${recordId}/timeline`)).data
  },
}
