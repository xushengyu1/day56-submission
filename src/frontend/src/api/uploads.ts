import { apiClient, isMockMode } from './client'
import { mockApi } from './mock'
import type { ImagePurpose, UploadResponse } from './types'

export const uploadsApi = {
  async upload(recordId: string, purpose: ImagePurpose, file: File): Promise<UploadResponse> {
    if (isMockMode) return mockApi.unsupported('图片上传')
    const form = new FormData()
    form.append('record_id', recordId)
    form.append('purpose', purpose)
    form.append('file', file)
    return (await apiClient.post<UploadResponse>('/api/uploads', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })).data
  },
}
