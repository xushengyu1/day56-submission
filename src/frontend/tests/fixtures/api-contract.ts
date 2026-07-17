import type {
  AuditEvent,
  CandidatePublic,
  ClaimDetail,
  FoundExtraction,
  ItemRecordPublic,
  LoginResponse,
  LocationArea,
  PaginatedResponse,
  PublicCategory,
  ReviewCandidatePublic,
  ReviewDetail,
  UploadResponse,
} from '@/api/types'
import type { MatchDoneDto, MatchErrorDto, MatchProgressDto } from '@/api/sse'

const USER_ID = '00000000-0000-4000-8000-000000000001'
const LOST_ID = '00000000-0000-4000-8000-000000000002'
const FOUND_ID = '00000000-0000-4000-8000-000000000003'
const CANDIDATE_ID = '00000000-0000-4000-8000-000000000004'
const CLAIM_ID = '00000000-0000-4000-8000-000000000005'
const REVIEW_ID = '00000000-0000-4000-8000-000000000006'
const ASSET_ID = '00000000-0000-4000-8000-000000000007'
const EVENT_ID = '00000000-0000-4000-8000-000000000008'
const NOW = '2026-07-17T02:30:00Z'

export const taxonomyFixture: { categories: PublicCategory[]; locations: LocationArea[] } = {
  categories: ['ELECTRONICS', 'IDENTITY_CARD', 'CLOTHING', 'STATIONERY', 'OTHER_CATEGORY'],
  locations: ['DORMITORY', 'CANTEEN', 'TEACHING_BUILDING', 'SCIENCE_BUILDING', 'LIBRARY'],
}

export const authFixture = {
  user: { id: USER_ID, username: 'contract-user', email: 'contract@example.test', role: 'USER', created_at: NOW },
  tokens: { access_token: 'access-token', refresh_token: 'refresh-token', token_type: 'bearer' },
} satisfies LoginResponse

export const foundRecordFixture = {
  id: FOUND_ID,
  owner_user_id: USER_ID,
  kind: 'FOUND',
  item_type: 'OTHER',
  public_category: 'ELECTRONICS',
  location_area: 'TEACHING_BUILDING',
  status: 'PUBLISHED',
  name_public: '黑色耳机',
  description_public: '教学楼 B 区 302 教室拾得',
  event_time_public: '2026-07-17 10:30',
  location_public: '教学楼',
  public_image_asset_id: ASSET_ID,
  number_masked: null,
  claim_id: null,
  version: 3,
  published_at: NOW,
  created_at: NOW,
  updated_at: NOW,
} satisfies ItemRecordPublic

export const itemPageFixture = {
  items: [foundRecordFixture], total: 1, page: 1, page_size: 5,
} satisfies PaginatedResponse<ItemRecordPublic>

export const candidateFixture = {
  id: CANDIDATE_ID,
  lost_record_id: LOST_ID,
  found_record_id: FOUND_ID,
  total_score: 86.5,
  level: 'HIGH',
  reason_codes: ['SEMANTIC_MATCH', 'TYPE_MATCH'],
  conflict_codes: [],
  found_record: foundRecordFixture,
  created_at: NOW,
} satisfies CandidatePublic

export const extractionFixture = {
  suggested_name: '黑色耳机',
  suggested_description: '黑色入耳式耳机',
  suggested_item_type: 'OTHER',
  confidence: 0.91,
  status: 'SUCCEEDED',
} satisfies FoundExtraction

export const claimFixture = {
  id: CLAIM_ID,
  candidate_id: CANDIDATE_ID,
  requester_user_id: USER_ID,
  item_type: 'OTHER',
  status: 'PENDING_HANDOFF',
  route_source: 'QUESTION_VERIFICATION',
  result_code: 'MATCH',
  attempt_count: 1,
  attempts_remaining: 1,
  created_at: NOW,
  updated_at: NOW,
  timeline: [{ event_type: 'CLAIM_SUBMITTED', result_code: 'MATCH', created_at: NOW }],
} satisfies ClaimDetail

const reviewCandidateFixture = {
  id: CANDIDATE_ID,
  lost_record_id: LOST_ID,
  found_record_id: FOUND_ID,
  total_score: 86.5,
  reason_codes: ['SEMANTIC_MATCH'],
  conflict_codes: [],
  found_record: foundRecordFixture,
  created_at: NOW,
} satisfies ReviewCandidatePublic

export const reviewFixture: ReviewDetail & { candidates: ReviewCandidatePublic[] } = {
  id: REVIEW_ID,
  source: 'UNMATCHED',
  item_type: 'OTHER',
  status: 'PENDING',
  route_source: 'OWNER_REQUEST',
  result_code: null,
  requester_user_id: USER_ID,
  reason: '未找到合适候选',
  created_at: NOW,
  lost_record: { ...foundRecordFixture, id: LOST_ID, kind: 'LOST', public_image_asset_id: null },
  candidate: null,
  candidates: [reviewCandidateFixture],
  evidence: [],
}

export const auditFixture = {
  event_id: EVENT_ID,
  event_type: 'ADMIN_REVIEW_DECIDED',
  aggregate_type: 'review_request',
  aggregate_id: REVIEW_ID,
  result_code: 'RECOMMEND_CANDIDATE',
  metadata_redacted: { candidate_id: CANDIDATE_ID },
  created_at: NOW,
} satisfies AuditEvent

export const uploadFixture = {
  image_asset_id: ASSET_ID,
  purpose: 'FINDER_ORIGINAL',
} satisfies UploadResponse

export const sseFixtures: {
  progress: MatchProgressDto
  done: MatchDoneDto
  error: MatchErrorDto
} = {
  progress: { stage: 'embedding', progress: 50 },
  done: { stage: 'done', progress: 100 },
  error: { stage: 'failed', progress: 100, error_code: 'MATCHING_FAILED' },
}

export const errorFixtures = [
  { status: 401, body: { error_code: 'UNAUTHENTICATED', message: '请先登录' } },
  { status: 403, body: { error_code: 'FORBIDDEN', message: '无权执行此操作' } },
  { status: 404, body: { error_code: 'NOT_FOUND', message: '资源不存在' } },
  { status: 409, body: { error_code: 'VERSION_CONFLICT', message: '记录已被更新，请重新加载' } },
  { status: 422, body: { error_code: 'VALIDATION_ERROR', message: '请求参数不正确', field_errors: { email: '请输入有效邮箱' } } },
  { status: 423, body: { error_code: 'ATTEMPT_LOCKED', message: '尝试次数已用尽，请联系管理员' } },
]
