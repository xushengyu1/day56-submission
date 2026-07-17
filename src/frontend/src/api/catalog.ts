import type { LocationArea, PublicCategory } from './types'

const publicCategoryLabels: Record<PublicCategory, string> = {
  ELECTRONICS: '电子产品',
  IDENTITY_CARD: '证件卡片',
  CLOTHING: '服饰配饰',
  STATIONERY: '学习用品',
  OTHER_CATEGORY: '其他',
}

const locationAreaLabels: Record<LocationArea, string> = {
  DORMITORY: '宿舍区',
  CANTEEN: '食堂',
  TEACHING_BUILDING: '教学楼',
  SCIENCE_BUILDING: '科教楼',
  LIBRARY: '图书馆',
}

function reverse<T extends string>(labels: Record<T, string>) {
  return Object.fromEntries(Object.entries(labels).map(([value, label]) => [label, value])) as Record<string, T>
}

const publicCategoriesByLabel = reverse(publicCategoryLabels)
const locationAreasByLabel = reverse(locationAreaLabels)

export const publicCategoryLabel = (category: PublicCategory) => publicCategoryLabels[category]
export const publicCategoryFromLabel = (label: string) => publicCategoriesByLabel[label]
export const locationAreaLabel = (area: LocationArea) => locationAreaLabels[area]
export const locationAreaFromLabel = (label: string) => locationAreasByLabel[label]

export const publicCategoryOptions = Object.entries(publicCategoryLabels).map(([value, label]) => ({ value: value as PublicCategory, label }))
export const locationAreaOptions = Object.entries(locationAreaLabels).map(([value, label]) => ({ value: value as LocationArea, label }))
