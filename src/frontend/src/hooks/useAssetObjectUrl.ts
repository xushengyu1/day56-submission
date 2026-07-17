import { useEffect, useState } from 'react'
import { assetsApi } from '@/api/assets'

export interface AssetObjectUrlState {
  url: string | null
  loading: boolean
  error: Error | null
}

export function useAssetObjectUrl(assetId?: string | null): AssetObjectUrlState {
  const [state, setState] = useState<AssetObjectUrlState>({ url: null, loading: false, error: null })

  useEffect(() => {
    if (!assetId) {
      setState({ url: null, loading: false, error: null })
      return
    }

    const controller = new AbortController()
    let active = true
    let objectUrl: string | null = null
    setState({ url: null, loading: true, error: null })

    void assetsApi.getBlob(assetId, controller.signal)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob)
        if (!active) {
          URL.revokeObjectURL(objectUrl)
          return
        }
        setState({ url: objectUrl, loading: false, error: null })
      })
      .catch((error: unknown) => {
        if (!active || controller.signal.aborted) return
        setState({ url: null, loading: false, error: error instanceof Error ? error : new Error('资源加载失败') })
      })

    return () => {
      active = false
      controller.abort()
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [assetId])

  return state
}
