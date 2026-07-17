import { apiClient, isMockMode } from './client'
import { locationAreaLabel } from './catalog'
import { mockApi, toItemRecordPublic } from './mock'
import type { ItemRecordPublic, LocationArea, PaginatedResponse, RecordKind, RecordSummary, TimelineEvent } from './types'

export const recordsApi = {
  async recent(limit = 5): Promise<ItemRecordPublic[]> {
    return isMockMode
      ? (await mockApi.getRecentItems(limit)).map(toItemRecordPublic)
      : (await apiClient.get<ItemRecordPublic[]>('/api/records/recent', { params: { limit } })).data
  },

  async list(locationArea?: LocationArea, page = 1, pageSize = 20): Promise<PaginatedResponse<ItemRecordPublic>> {
    if (isMockMode) {
      const result = await mockApi.getItemsByLocation(locationArea ? locationAreaLabel(locationArea) : '', page, pageSize)
      return { items: result.items.map(toItemRecordPublic), total: result.total, page, page_size: pageSize }
    }
    return (await apiClient.get<PaginatedResponse<ItemRecordPublic>>('/api/records', {
      params: { location_area: locationArea, page, page_size: pageSize },
    })).data
  },

  async mine(kind?: RecordKind, page = 1, pageSize = 20): Promise<PaginatedResponse<ItemRecordPublic>> {
    if (isMockMode) {
      const items = (await mockApi.getMyRecords()).filter((record) => !kind || record.kind === kind)
      return { items: items.map(toItemRecordPublic), total: items.length, page, page_size: pageSize }
    }
    return (await apiClient.get<PaginatedResponse<ItemRecordPublic>>('/api/records/mine', {
      params: { kind, page, page_size: pageSize },
    })).data
  },

  async summary(): Promise<RecordSummary> {
    if (isMockMode) {
      const items = await mockApi.getMyRecords()
      return {
        lost_count: items.filter((record) => record.kind === 'LOST').length,
        found_count: items.filter((record) => record.kind === 'FOUND').length,
        matched_count: items.filter((record) => ['PENDING_HANDOFF', 'CLAIMED', 'CLOSED'].includes(record.status)).length,
        total_count: items.length,
      }
    }
    return (await apiClient.get<RecordSummary>('/api/records/mine/summary')).data
  },

  async timeline(recordId: string): Promise<TimelineEvent[]> {
    if (isMockMode) return mockApi.unsupported('记录时间线')
    return (await apiClient.get<TimelineEvent[]>(`/api/records/${recordId}/timeline`)).data
  },
}
