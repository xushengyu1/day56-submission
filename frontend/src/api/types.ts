// API 类型定义 —— 与后端 dev.md / end-to-end-system-design.md 对齐

// ===== 枚举 =====

export type UserRole = 'USER' | 'ADMIN'

export type ItemType = 'IDENTITY_DOCUMENT' | 'OTHER'

/** 记录方向：失物 or 招领 */
export type RecordKind = 'LOST' | 'FOUND'

/** 失物/招领记录状态 */
export type RecordStatus =
  | 'DRAFT'             // 草稿
  | 'PROCESSING'        // AI 处理中
  | 'PUBLISHED'         // 已发布
  | 'MATCHING_FAILED'   // 匹配处理失败
  | 'PENDING_HANDOFF'   // 待交接
  | 'CLAIMED'           // 已认领
  | 'CLOSED'            // 已关闭
  | 'CANCELLED'         // 已取消

/** 认领申请状态 */
export type ClaimStatus =
  | 'SUBMITTED'             // 已提交
  | 'VERIFYING'             // 核验中
  | 'PENDING_ADMIN_REVIEW'  // 待管理员复核
  | 'PENDING_HANDOFF'       // 待交接
  | 'REJECTED'              // 已拒绝
  | 'CLAIMED'               // 已完成认领
  | 'LOCKED'                // 已锁定（身份证尝试次数耗尽）

/** 核验模式 */
export type VerificationMode = 'DOCUMENT_NUMBER' | 'HIDDEN_FEATURE'

/** 管理员复核来源类型 */
export type ReviewRequestType = 'MULTI_CLAIM' | 'VERIFICATION_FAILED' | 'IDENTITY_ANOMALY' | 'UNMATCHED' | 'CLAIM_REVIEW'

/** 管理员决定 */
export type AdminDecision = 'APPROVE_TO_HANDOFF' | 'REJECT'

/** OTHER 单题核验结果 */
export type QuestionResult = 'MATCH' | 'PARTIAL_MATCH' | 'UNDETERMINED' | 'CONFLICT'

/** 图片用途 */
export type ImagePurpose = 'FINDER_ORIGINAL' | 'PUBLIC_REDACTED' | 'OWNER_SUPPORT'

/** 图片脱敏状态 */
export type RedactionStatus = 'NOT_REQUIRED' | 'PENDING' | 'CONFIRMED' | 'FAILED'

/** AI 提取状态 */
export type ExtractionStatus = 'SUCCEEDED' | 'INVALID' | 'TIMEOUT' | 'FALLBACK'

// ===== 用户与认证 =====

export interface User {
  id: string
  username: string
  email: string
  role: UserRole
  phone?: string
  created_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  user: User
  tokens: AuthTokens
}

export interface RegisterRequest {
  username: string
  password: string
  email: string
  phone?: string
}

// ===== 物品记录 =====

export interface ItemRecord {
  id: string
  owner_user_id: string
  kind: RecordKind
  item_type: ItemType
  status: RecordStatus

  // PUBLIC 字段
  name_public: string
  description_public?: string
  event_time_public: string       // 模糊时间，如"7月16日上午"
  location_public: string         // 公开地点

  // MATCH_ONLY 字段（前端通常不直接展示）
  event_time_exact?: string       // 精确时间 ISO 8601
  location_normalized?: Record<string, unknown>

  // 图片
  public_image_path?: string      // PUBLIC 脱敏副本路径
  masked_document_number?: string // 掩码证件号（前3后4）

  // 元数据
  published_at?: string
  version?: number
  created_at: string
  updated_at: string
}

// ===== 候选匹配 =====

export interface MatchCandidate {
  id: string
  lost_record_id: string
  found_record_id: string

  // 总分（满分100）+ 文本解释
  total_score: number
  reason_texts: string[]      // 匹配理由文案，如 ['物品类别一致——都是折叠伞', '时间接近']
  conflict_texts: string[]    // 冲突点文案，如 ['楼层不一致——失主填写3楼，招领记录填写2楼']
  retention_reason: string    // 保留该候选的综合说明

  // 关联的招领记录 PUBLIC 投影
  found_record: ItemRecord

  created_at: string
}

// ===== 认领申请 =====

export interface ClaimApplication {
  id: string
  candidate_id: string
  claimant_id: string
  verification_mode: VerificationMode
  status: ClaimStatus
  attempt_count: number       // 身份证尝试次数（最多2次）
  created_at: string
}

// ===== OTHER 核验问题 =====

export interface VerificationQuestion {
  question_id: string
  question_text: string
  // 注意：answer_key 绝不返回前端
}

export interface VerificationQuestionSet {
  set_id: string
  found_record_id: string
  questions: VerificationQuestion[]
  hidden_description?: string // 仅拾得者/管理员可见
}

export interface ClaimAnswer {
  question_id: string
  answer_text: string
}

export interface QuestionVerificationResult {
  question_id: string
  result: QuestionResult
  confidence: number
  reason_code?: string
}

export interface ClaimVerificationResponse {
  claim_id: string
  status: ClaimStatus
  items: QuestionVerificationResult[]
  overall_confidence: number
  hard_conflict: boolean
  needs_admin_review: boolean
}

// ===== 管理员复核 =====

export interface ReviewRecord {
  id: string
  review_type: ReviewRequestType
  target_id: string
  target_name?: string       // 关联物品名称（可读）
  target_type: 'LOST' | 'CLAIM'
  applicant_id: string
  applicant_name?: string    // 申请人姓名（可读）
  reason: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  reviewer_id?: string
  review_reason?: string
  created_at: string
}

export interface AdminDecisionRequest {
  decision: AdminDecision
  reason: string
}

// ===== 审计 =====

export interface AuditEvent {
  id: string
  event_type: string
  actor_type: string
  actor_id: string
  aggregate_type: string
  aggregate_id: string
  request_id?: string
  safe_payload: Record<string, unknown>
  occurred_at: string
}

// ===== 时间线 =====

export interface TimelineEvent {
  event_id: string
  event_type: string
  actor_type: string
  detail: string
  occurred_at: string
}

// ===== 图片 =====

export interface ImageAsset {
  id: string
  record_id: string
  purpose: ImagePurpose
  data_class: 'PRIVATE' | 'PUBLIC'
  redaction_status: RedactionStatus
  mime_type: string
  size_bytes: number
  created_at: string
}

export interface UploadResponse {
  image_asset_id: string
  purpose: ImagePurpose
}

// ===== 交接 =====

export interface ContactInfo {
  finder_phone?: string
  finder_email?: string
  authorized_at: string
}

// ===== 通用 =====

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
