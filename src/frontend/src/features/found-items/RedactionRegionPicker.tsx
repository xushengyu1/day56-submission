import { useRef, useState } from 'react'
import type { PointerEvent } from 'react'
import type { RedactionRegion } from '@/api/types'

interface Point { x: number; y: number }

export function RedactionRegionPicker({ src, value, onChange }: {
  src: string
  value: RedactionRegion | null
  onChange: (region: RedactionRegion | null) => void
}) {
  const imageRef = useRef<HTMLImageElement>(null)
  const [start, setStart] = useState<Point | null>(null)

  const naturalPoint = (event: PointerEvent<HTMLDivElement>): Point | null => {
    const image = imageRef.current
    if (!image || image.naturalWidth <= 0 || image.naturalHeight <= 0) return null
    const rect = image.getBoundingClientRect()
    if (rect.width <= 0 || rect.height <= 0) return null
    return {
      x: Math.round(Math.min(Math.max(event.clientX - rect.left, 0), rect.width) * image.naturalWidth / rect.width),
      y: Math.round(Math.min(Math.max(event.clientY - rect.top, 0), rect.height) * image.naturalHeight / rect.height),
    }
  }

  const finish = (event: PointerEvent<HTMLDivElement>) => {
    if (!start) return
    const end = naturalPoint(event)
    setStart(null)
    if (!end) return
    const region = {
      x: Math.min(start.x, end.x),
      y: Math.min(start.y, end.y),
      width: Math.abs(end.x - start.x),
      height: Math.abs(end.y - start.y),
    }
    onChange(region.width > 0 && region.height > 0 ? region : null)
  }

  const image = imageRef.current
  const overlay = value && image?.naturalWidth && image?.naturalHeight ? {
    left: `${value.x / image.naturalWidth * 100}%`,
    top: `${value.y / image.naturalHeight * 100}%`,
    width: `${value.width / image.naturalWidth * 100}%`,
    height: `${value.height / image.naturalHeight * 100}%`,
  } : undefined

  return (
    <div>
      <p className="text-xs mb-2">请在原图上拖动框选需要遮挡的证件号码区域。</p>
      <div
        className="relative inline-block max-w-full touch-none cursor-crosshair"
        onPointerDown={(event) => {
          const point = naturalPoint(event)
          if (!point) return
          setStart(point)
          event.currentTarget.setPointerCapture?.(event.pointerId)
        }}
        onPointerUp={finish}
        onPointerCancel={() => setStart(null)}
        data-testid="redaction-picker"
      >
        <img ref={imageRef} src={src} alt="选择证件号码遮挡区域" className="block max-w-full max-h-80 rounded-lg" draggable={false} />
        {overlay ? <div className="absolute border-2 border-red-500 bg-black/70 pointer-events-none" style={overlay} data-testid="redaction-region" /> : null}
      </div>
      <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>{value ? `已选择区域：x=${value.x}, y=${value.y}, ${value.width}×${value.height}` : '尚未选择有效区域'}</p>
    </div>
  )
}
