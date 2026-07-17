import { describe, expect, it } from 'vitest'
import {
  locationAreaFromLabel,
  locationAreaLabel,
  publicCategoryFromLabel,
  publicCategoryLabel,
} from '@/api/catalog'

describe('catalog', () => {
  it.each([
    ['电子产品', 'ELECTRONICS'],
    ['证件卡片', 'IDENTITY_CARD'],
    ['服饰配饰', 'CLOTHING'],
    ['学习用品', 'STATIONERY'],
    ['其他', 'OTHER_CATEGORY'],
  ] as const)('maps public category %s in both directions', (label, value) => {
    expect(publicCategoryFromLabel(label)).toBe(value)
    expect(publicCategoryLabel(value)).toBe(label)
  })

  it.each([
    ['宿舍区', 'DORMITORY'],
    ['食堂', 'CANTEEN'],
    ['教学楼', 'TEACHING_BUILDING'],
    ['科教楼', 'SCIENCE_BUILDING'],
    ['图书馆', 'LIBRARY'],
  ] as const)('maps location area %s in both directions', (label, value) => {
    expect(locationAreaFromLabel(label)).toBe(value)
    expect(locationAreaLabel(value)).toBe(label)
  })
})
