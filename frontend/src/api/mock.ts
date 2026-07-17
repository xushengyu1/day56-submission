import type { User, AuthTokens, ItemRecord, MatchCandidate, ReviewRecord } from './types'

const MOCK_USER: User = {
  id: 'u-001',
  username: 'zhangsan',
  email: 'zhangsan@campus.edu.cn',
  role: 'USER',
  phone: '138****1234',
  created_at: '2026-07-14T08:00:00Z',
}

const MOCK_ADMIN: User = {
  id: 'u-admin',
  username: 'admin',
  email: 'admin@campus.edu.cn',
  role: 'ADMIN',
  created_at: '2026-07-10T08:00:00Z',
}

const MOCK_TOKENS: AuthTokens = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
}

// ===== 当前用户(u-001)的寻物记录 =====
export const MOCK_LOST_ITEMS: ItemRecord[] = [
  // --- 自己的 ---
  {
    id: 'lr-001',
    owner_user_id: 'u-001',
    kind: 'LOST',
    item_type: 'OTHER',
    name_public: '黑色折叠伞',
    description_public: '黑色短柄折叠伞，普通款，无明显品牌标识',
    event_time_public: '7月16日上午',
    location_public: '教学楼',
    status: 'PUBLISHED',
    created_at: '2026-07-16T09:00:00Z',
    updated_at: '2026-07-16T14:05:00Z',
  },
  {
    id: 'lr-002',
    owner_user_id: 'u-001',
    kind: 'LOST',
    item_type: 'OTHER',
    name_public: '白色AirPods Pro',
    description_public: '白色AirPods Pro二代，充电仓有轻微划痕',
    event_time_public: '7月14日下午',
    location_public: '图书馆',
    status: 'PUBLISHED',
    created_at: '2026-07-14T15:00:00Z',
    updated_at: '2026-07-14T15:00:00Z',
  },
  {
    id: 'lr-008',
    owner_user_id: 'u-001',
    kind: 'LOST',
    item_type: 'IDENTITY_DOCUMENT',
    name_public: '校园卡',
    description_public: '校园一卡通，卡面有姓名拼音 ZHANG',
    event_time_public: '7月16日中午',
    location_public: '食堂',
    status: 'PENDING_HANDOFF',
    created_at: '2026-07-16T12:00:00Z',
    updated_at: '2026-07-16T18:30:00Z',
  },
  {
    id: 'lr-009',
    owner_user_id: 'u-001',
    kind: 'LOST',
    item_type: 'OTHER',
    name_public: '灰色运动外套',
    description_public: 'Nike灰色拉链外套，L码，左口袋有钥匙',
    event_time_public: '7月13日下午',
    location_public: '宿舍区',
    status: 'CLAIMED',
    created_at: '2026-07-13T15:00:00Z',
    updated_at: '2026-07-15T10:00:00Z',
  },
  // --- 他人的 ---
  {
    id: 'lr-003',
    owner_user_id: 'u-010',
    kind: 'LOST',
    item_type: 'OTHER',
    name_public: '蓝色水杯',
    description_public: '膳魔师蓝色保温杯，杯身有贴纸',
    event_time_public: '7月15日上午',
    location_public: '食堂',
    status: 'PUBLISHED',
    created_at: '2026-07-15T10:00:00Z',
    updated_at: '2026-07-15T10:00:00Z',
  },
  {
    id: 'lr-004',
    owner_user_id: 'u-011',
    kind: 'LOST',
    item_type: 'OTHER',
    name_public: '灰色书包',
    description_public: '耐克灰色双肩包，侧袋有钥匙扣',
    event_time_public: '7月16日下午',
    location_public: '科教楼',
    status: 'PUBLISHED',
    created_at: '2026-07-16T14:00:00Z',
    updated_at: '2026-07-16T14:00:00Z',
  },
  {
    id: 'lr-005',
    owner_user_id: 'u-012',
    kind: 'LOST',
    item_type: 'OTHER',
    name_public: '黑色有线耳机',
    description_public: 'Sony有线耳机，黑色，线控部分有磨损',
    event_time_public: '7月13日晚上',
    location_public: '宿舍区',
    status: 'PUBLISHED',
    created_at: '2026-07-13T21:00:00Z',
    updated_at: '2026-07-13T21:00:00Z',
  },
  {
    id: 'lr-006',
    owner_user_id: 'u-020',
    kind: 'LOST',
    item_type: 'OTHER',
    name_public: '银色手表',
    description_public: '卡西欧银色电子手表，表带有划痕',
    event_time_public: '7月15日下午',
    location_public: '教学楼',
    status: 'PUBLISHED',
    created_at: '2026-07-15T16:00:00Z',
    updated_at: '2026-07-15T16:00:00Z',
  },
  {
    id: 'lr-007',
    owner_user_id: 'u-021',
    kind: 'LOST',
    item_type: 'IDENTITY_DOCUMENT',
    name_public: '学生证',
    description_public: '红色学生证，姓名部分被遮挡',
    event_time_public: '7月14日中午',
    location_public: '食堂',
    status: 'PUBLISHED',
    created_at: '2026-07-14T12:00:00Z',
    updated_at: '2026-07-14T12:00:00Z',
  },
  {
    id: 'lr-010',
    owner_user_id: 'u-022',
    kind: 'LOST',
    item_type: 'OTHER',
    name_public: 'iPad mini',
    description_public: 'iPad mini 6，深空灰，有蓝色保护壳',
    event_time_public: '7月16日上午',
    location_public: '图书馆',
    status: 'PUBLISHED',
    created_at: '2026-07-16T10:00:00Z',
    updated_at: '2026-07-16T10:00:00Z',
  },
  {
    id: 'lr-011',
    owner_user_id: 'u-023',
    kind: 'LOST',
    item_type: 'OTHER',
    name_public: '钥匙串',
    description_public: '银色钥匙3把，带蓝色挂绳',
    event_time_public: '7月15日晚上',
    location_public: '教学楼',
    status: 'PUBLISHED',
    created_at: '2026-07-15T19:00:00Z',
    updated_at: '2026-07-15T19:00:00Z',
  },
  {
    id: 'lr-012',
    owner_user_id: 'u-024',
    kind: 'LOST',
    item_type: 'OTHER',
    name_public: '黑色双肩包',
    description_public: '新秀丽黑色双肩包，内有笔记本电脑',
    event_time_public: '7月14日下午',
    location_public: '科教楼',
    status: 'PUBLISHED',
    created_at: '2026-07-14T14:00:00Z',
    updated_at: '2026-07-14T14:00:00Z',
  },
]

// ===== 当前用户(u-001)的招领记录 =====
export const MOCK_FOUND_ITEMS: ItemRecord[] = [
  // --- 自己的 ---
  {
    id: 'fr-001',
    owner_user_id: 'u-001',
    kind: 'FOUND',
    item_type: 'OTHER',
    name_public: '深色折叠伞',
    description_public: '深灰色折叠伞，伞面完好，手柄无磨损',
    event_time_public: '7月16日上午',
    location_public: '教学楼',
    status: 'PUBLISHED',
    created_at: '2026-07-16T11:00:00Z',
    updated_at: '2026-07-16T11:00:00Z',
  },
  {
    id: 'fr-006',
    owner_user_id: 'u-001',
    kind: 'FOUND',
    item_type: 'OTHER',
    name_public: '黑色笔记本',
    description_public: '黑色皮面笔记本，内有手写笔记',
    event_time_public: '7月16日下午',
    location_public: '教学楼',
    status: 'PENDING_HANDOFF',
    created_at: '2026-07-16T15:00:00Z',
    updated_at: '2026-07-16T17:00:00Z',
  },
  {
    id: 'fr-008',
    owner_user_id: 'u-001',
    kind: 'FOUND',
    item_type: 'OTHER',
    name_public: '红色水杯',
    description_public: '象印红色保温杯，杯底有划痕',
    event_time_public: '7月13日中午',
    location_public: '食堂',
    status: 'CLAIMED',
    created_at: '2026-07-13T12:30:00Z',
    updated_at: '2026-07-14T09:00:00Z',
  },
  // --- 他人的 ---
  {
    id: 'fr-002',
    owner_user_id: 'u-003',
    kind: 'FOUND',
    item_type: 'IDENTITY_DOCUMENT',
    name_public: '居民身份证',
    description_public: '证件外有透明卡套',
    event_time_public: '7月15日中午',
    location_public: '食堂',
    masked_document_number: '110***********1234',
    status: 'PUBLISHED',
    created_at: '2026-07-15T12:30:00Z',
    updated_at: '2026-07-15T12:30:00Z',
  },
  {
    id: 'fr-003',
    owner_user_id: 'u-013',
    kind: 'FOUND',
    item_type: 'OTHER',
    name_public: 'U盘一个',
    description_public: '金士顿32G U盘，银色金属外壳',
    event_time_public: '7月16日中午',
    location_public: '图书馆',
    status: 'PUBLISHED',
    created_at: '2026-07-16T12:30:00Z',
    updated_at: '2026-07-16T12:30:00Z',
  },
  {
    id: 'fr-004',
    owner_user_id: 'u-014',
    kind: 'FOUND',
    item_type: 'OTHER',
    name_public: '一串钥匙',
    description_public: '银色钥匙3把，带蓝色钥匙扣',
    event_time_public: '7月15日下午',
    location_public: '科教楼',
    status: 'PUBLISHED',
    created_at: '2026-07-15T15:00:00Z',
    updated_at: '2026-07-15T15:00:00Z',
  },
  {
    id: 'fr-005',
    owner_user_id: 'u-015',
    kind: 'FOUND',
    item_type: 'OTHER',
    name_public: '运动水壶',
    description_public: '红色运动水壶，品牌不详',
    event_time_public: '7月14日上午',
    location_public: '宿舍区',
    status: 'PUBLISHED',
    created_at: '2026-07-14T10:00:00Z',
    updated_at: '2026-07-14T10:00:00Z',
  },
  {
    id: 'fr-007',
    owner_user_id: 'u-017',
    kind: 'FOUND',
    item_type: 'OTHER',
    name_public: '白色充电宝',
    description_public: '小米白色充电宝，10000mAh',
    event_time_public: '7月15日晚上',
    location_public: '图书馆',
    status: 'PUBLISHED',
    created_at: '2026-07-15T20:00:00Z',
    updated_at: '2026-07-15T20:00:00Z',
  },
  {
    id: 'fr-009',
    owner_user_id: 'u-018',
    kind: 'FOUND',
    item_type: 'IDENTITY_DOCUMENT',
    name_public: '校园卡',
    description_public: '校园一卡通，卡面有照片',
    event_time_public: '7月16日上午',
    location_public: '教学楼',
    status: 'PUBLISHED',
    created_at: '2026-07-16T09:30:00Z',
    updated_at: '2026-07-16T09:30:00Z',
  },
  {
    id: 'fr-010',
    owner_user_id: 'u-019',
    kind: 'FOUND',
    item_type: 'OTHER',
    name_public: '蓝牙鼠标',
    description_public: '罗技白色蓝牙鼠标',
    event_time_public: '7月15日下午',
    location_public: '科教楼',
    status: 'PUBLISHED',
    created_at: '2026-07-15T16:00:00Z',
    updated_at: '2026-07-15T16:00:00Z',
  },
  {
    id: 'fr-011',
    owner_user_id: 'u-025',
    kind: 'FOUND',
    item_type: 'OTHER',
    name_public: '眼镜盒',
    description_public: '黑色硬壳眼镜盒，内有眼镜布',
    event_time_public: '7月14日下午',
    location_public: '宿舍区',
    status: 'PUBLISHED',
    created_at: '2026-07-14T15:00:00Z',
    updated_at: '2026-07-14T15:00:00Z',
  },
  {
    id: 'fr-012',
    owner_user_id: 'u-026',
    kind: 'FOUND',
    item_type: 'OTHER',
    name_public: '黑色钱包',
    description_public: '男士黑色皮质钱包，内有若干卡片',
    event_time_public: '7月16日中午',
    location_public: '食堂',
    status: 'PUBLISHED',
    created_at: '2026-07-16T12:00:00Z',
    updated_at: '2026-07-16T12:00:00Z',
  },
]

// ===== 候选匹配 =====
export const MOCK_CANDIDATES: MatchCandidate[] = [
  {
    id: 'c-001',
    lost_record_id: 'lr-001',
    found_record_id: 'fr-001',
    total_score: 82,
    reason_texts: ['物品类别一致——都是折叠伞', '时间相差约20分钟——在合理偏差范围内', '位于同一栋教学楼', '公开描述语义相似——都描述为黑色短柄折叠伞'],
    conflict_texts: ['描述颜色略有差异——黑色vs深灰色'],
    retention_reason: '物品外观描述接近，时间在同一天同一地点，可作为高匹配候选。',
    found_record: MOCK_FOUND_ITEMS.find((i) => i.id === 'fr-001')!,
    created_at: '2026-07-16T14:05:00Z',
  },
  {
    id: 'c-002',
    lost_record_id: 'lr-001',
    found_record_id: 'fr-009',
    total_score: 48,
    reason_texts: ['颜色一致——黑色', '同在教学楼区域'],
    conflict_texts: ['物品类型不同——折叠伞vs校园卡', '时间有差异'],
    retention_reason: '颜色和地点一致，但物品类型差异较大，匹配度较低。',
    found_record: MOCK_FOUND_ITEMS.find((i) => i.id === 'fr-009')!,
    created_at: '2026-07-16T14:05:00Z',
  },
]

// ===== 管理员复核 =====
export const MOCK_REVIEWS: ReviewRecord[] = [
  {
    id: 'rv-001',
    review_type: 'MULTI_CLAIM',
    target_id: 'fr-002',
    target_name: '居民身份证',
    target_type: 'CLAIM',
    applicant_id: 'u-001',
    applicant_name: '张同学',
    reason: '同一物品有2人认领，需人工判断',
    status: 'PENDING',
    created_at: '2026-07-16T15:00:00Z',
  },
  {
    id: 'rv-002',
    review_type: 'VERIFICATION_FAILED',
    target_id: 'fr-005',
    target_name: '运动水壶',
    target_type: 'CLAIM',
    applicant_id: 'u-006',
    applicant_name: '刘同学',
    reason: '隐藏特征回答存在冲突',
    status: 'PENDING',
    created_at: '2026-07-16T13:45:00Z',
  },
  {
    id: 'rv-003',
    review_type: 'UNMATCHED',
    target_id: 'lr-003',
    target_name: '蓝色水杯',
    target_type: 'LOST',
    applicant_id: 'u-010',
    applicant_name: '赵同学',
    reason: 'Top5无合适候选，申请管理员重新检查',
    status: 'PENDING',
    created_at: '2026-07-16T12:30:00Z',
  },
  {
    id: 'rv-004',
    review_type: 'CLAIM_REVIEW',
    target_id: 'cl-003',
    target_name: '校园一卡通',
    target_type: 'CLAIM',
    applicant_id: 'u-008',
    applicant_name: '陈同学',
    reason: '证件核验异常，申请复核',
    status: 'PENDING',
    created_at: '2026-07-16T11:15:00Z',
  },
  {
    id: 'rv-005',
    review_type: 'MULTI_CLAIM',
    target_id: 'fr-006',
    target_name: '黑色笔记本',
    target_type: 'CLAIM',
    applicant_id: 'u-009',
    applicant_name: '周同学',
    reason: '同一物品有3人认领',
    status: 'PENDING',
    created_at: '2026-07-16T14:20:00Z',
  },
]

// ===== 工具函数 =====
function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

let currentUser: User = MOCK_USER

// ===== Mock API =====
export const mockApi = {
  async login(email: string, _password: string): Promise<{ user: User; tokens: AuthTokens }> {
    await delay(500)
    currentUser = email === 'admin@campus.edu.cn' ? MOCK_ADMIN : { ...MOCK_USER, email }
    return { user: currentUser, tokens: MOCK_TOKENS }
  },

  async register(data: { username: string; email: string }): Promise<{ user: User; tokens: AuthTokens }> {
    await delay(500)
    currentUser = { ...MOCK_USER, username: data.username, email: data.email }
    return { user: currentUser, tokens: MOCK_TOKENS }
  },

  async getMe(): Promise<User> {
    await delay(200)
    return currentUser
  },

  async getMyLostItems(): Promise<ItemRecord[]> {
    await delay(300)
    return MOCK_LOST_ITEMS.filter((i) => i.owner_user_id === currentUser.id)
  },

  async getMyFoundItems(): Promise<ItemRecord[]> {
    await delay(300)
    return MOCK_FOUND_ITEMS.filter((i) => i.owner_user_id === currentUser.id)
  },

  /** 获取我的所有记录（寻物+招领），按更新时间倒序 */
  /** 获取全系统最新动态（寻物+招领），按创建时间倒序 */
  async getRecentItems(limit: number = 5): Promise<ItemRecord[]> {
    await delay(300)
    const all = [...MOCK_LOST_ITEMS, ...MOCK_FOUND_ITEMS]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    return all.slice(0, limit)
  },

  async getMyRecords(): Promise<ItemRecord[]> {
    await delay(300)
    const lost = MOCK_LOST_ITEMS.filter((i) => i.owner_user_id === currentUser.id)
    const found = MOCK_FOUND_ITEMS.filter((i) => i.owner_user_id === currentUser.id)
    return [...lost, ...found].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
  },

  async getCandidates(_lostId: string): Promise<MatchCandidate[]> {
    await delay(400)
    return MOCK_CANDIDATES.filter((c) => c.lost_record_id === _lostId)
  },

  async getCandidateDetail(id: string): Promise<MatchCandidate | undefined> {
    await delay(200)
    return MOCK_CANDIDATES.find((c) => c.id === id)
  },

  async getReviewQueue(): Promise<ReviewRecord[]> {
    await delay(300)
    return MOCK_REVIEWS
  },

  async getReviewDetail(id: string): Promise<ReviewRecord | undefined> {
    await delay(200)
    return MOCK_REVIEWS.find((r) => r.id === id)
  },

  async getItemsByLocation(location: string, page: number = 1, pageSize: number = 5): Promise<{ items: ItemRecord[]; total: number }> {
    await delay(300)
    const lost = MOCK_LOST_ITEMS.filter((i) => i.location_public === location)
    const found = MOCK_FOUND_ITEMS.filter((i) => i.location_public === location)
    const all = [...lost, ...found].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    const start = (page - 1) * pageSize
    return { items: all.slice(start, start + pageSize), total: all.length }
  },

  async getFoundItemDetail(id: string): Promise<ItemRecord | undefined> {
    await delay(200)
    return MOCK_FOUND_ITEMS.find((i) => i.id === id)
  },

  async getItemDetail(id: string): Promise<ItemRecord | undefined> {
    await delay(200)
    return [...MOCK_LOST_ITEMS, ...MOCK_FOUND_ITEMS].find((i) => i.id === id)
  },

  /** 拾得者确认物品已被取走 */
  async confirmPickup(foundItemId: string): Promise<ItemRecord> {
    await delay(500)
    const item = MOCK_FOUND_ITEMS.find((i) => i.id === foundItemId)
    if (!item) throw new Error('Item not found')
    item.status = 'CLAIMED'
    item.updated_at = new Date().toISOString()
    return item
  },

  unsupported(operation: string): never {
    throw new Error(`Mock 演示模式暂不支持 ${operation}`)
  },
}
