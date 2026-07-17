const reasonLabels: Record<string, string> = {
  SEMANTIC_MATCH: '公开描述相似',
  TYPE_MATCH: '物品类型一致',
}

const conflictLabels: Record<string, string> = {
  TIME_CONFLICT: '时间信息存在差异',
  LOCATION_WEAK_CONFLICT: '地点信息有轻微差异',
  LOCATION_CONFLICT: '地点信息存在差异',
  RECORD_KIND_MISMATCH: '记录类型不匹配',
  ITEM_TYPE_MISMATCH: '物品类型不匹配',
  CATEGORY_MISMATCH: '物品类别不匹配',
}

export function reasonCodeLabel(code: string): string {
  return reasonLabels[code] ?? '其他匹配因素'
}

export function conflictCodeLabel(code: string): string {
  return conflictLabels[code] ?? '其他信息差异'
}

export function formatCandidateScore(score: number): string {
  return String(Number(score.toFixed(2)))
}
