import { authorizedFetch } from './client'
import { ApiError } from './errors'

async function getBlob(assetId: string, signal?: AbortSignal): Promise<Blob> {
  const response = await authorizedFetch(`/api/assets/${encodeURIComponent(assetId)}`, { signal })
  if (!response.ok) {
    throw new ApiError(response.status, `HTTP_${response.status}`, '资源加载失败')
  }
  return response.blob()
}

export const assetsApi = { getBlob }
