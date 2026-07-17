import { describe, expect, it } from 'vitest'
import { z } from 'zod'
import {
  auditFixture,
  authFixture,
  candidateFixture,
  claimFixture,
  errorFixtures,
  extractionFixture,
  itemPageFixture,
  reviewFixture,
  sseFixtures,
  taxonomyFixture,
  uploadFixture,
} from './fixtures/api-contract'

const uuid = z.string().uuid()
const timestamp = z.string().datetime()
const publicCategory = z.enum(['ELECTRONICS', 'IDENTITY_CARD', 'CLOTHING', 'STATIONERY', 'OTHER_CATEGORY'])
const locationArea = z.enum(['DORMITORY', 'CANTEEN', 'TEACHING_BUILDING', 'SCIENCE_BUILDING', 'LIBRARY'])
const itemType = z.enum(['IDENTITY_DOCUMENT', 'OTHER'])
const recordStatus = z.enum(['DRAFT', 'PROCESSING', 'PUBLISHED', 'MATCHING_FAILED', 'PENDING_HANDOFF', 'CLAIMED', 'CLOSED', 'CANCELLED'])
const claimStatus = z.enum(['SUBMITTED', 'VERIFYING', 'PENDING_ADMIN_REVIEW', 'PENDING_HANDOFF', 'REJECTED', 'CLAIMED', 'LOCKED'])

const user = z.object({ id: uuid, username: z.string(), email: z.string().email(), role: z.enum(['USER', 'ADMIN']), created_at: timestamp }).strict()
const auth = z.object({
  user,
  tokens: z.object({ access_token: z.string(), refresh_token: z.string(), token_type: z.string() }).strict(),
}).strict()
const itemRecord = z.object({
  id: uuid,
  owner_user_id: uuid,
  kind: z.enum(['LOST', 'FOUND']),
  item_type: itemType,
  public_category: publicCategory,
  location_area: locationArea,
  status: recordStatus,
  name_public: z.string().nullable(),
  description_public: z.string().nullable(),
  event_time_public: z.string().nullable(),
  location_public: z.string().nullable(),
  public_image_asset_id: uuid.nullable(),
  number_masked: z.string().nullable(),
  claim_id: uuid.nullable(),
  version: z.number().int(),
  published_at: timestamp.nullable(),
  created_at: timestamp,
  updated_at: timestamp,
}).strict()
const candidate = z.object({
  id: uuid, lost_record_id: uuid, found_record_id: uuid, total_score: z.number(), level: z.string(),
  reason_codes: z.array(z.string()), conflict_codes: z.array(z.string()), found_record: itemRecord, created_at: timestamp,
}).strict()
const reviewCandidate = candidate.omit({ level: true })

describe('cross-language API fixtures', () => {
  it('locks the exact five public categories and five location areas', () => {
    expect(z.array(publicCategory).parse(taxonomyFixture.categories)).toEqual(taxonomyFixture.categories)
    expect(z.array(locationArea).parse(taxonomyFixture.locations)).toEqual(taxonomyFixture.locations)
  })

  it('parses auth and paginated item responses', () => {
    expect(auth.parse(authFixture)).toEqual(authFixture)
    const page = z.object({ items: z.array(itemRecord), total: z.number().int(), page: z.number().int(), page_size: z.number().int() }).strict()
    expect(page.parse(itemPageFixture)).toEqual(itemPageFixture)
  })

  it('parses nested candidate and extraction responses', () => {
    expect(candidate.parse(candidateFixture)).toEqual(candidateFixture)
    const extraction = z.object({
      suggested_name: z.string(), suggested_description: z.string(), suggested_item_type: itemType,
      confidence: z.number().min(0).max(1), status: z.enum(['SUCCEEDED', 'INVALID', 'TIMEOUT', 'FALLBACK']),
    }).strict()
    expect(extraction.parse(extractionFixture)).toEqual(extractionFixture)
  })

  it('parses claim and safe admin review detail responses', () => {
    const claim = z.object({
      id: uuid, candidate_id: uuid, requester_user_id: uuid, item_type: itemType, status: claimStatus,
      route_source: z.string().nullable(), result_code: z.string().nullable(), attempt_count: z.number().int(),
      attempts_remaining: z.number().int(), created_at: timestamp, updated_at: timestamp,
      timeline: z.array(z.object({ event_type: z.string(), result_code: z.string(), created_at: timestamp }).strict()),
    }).strict()
    const review = z.object({
      id: uuid, source: z.string(), item_type: itemType.nullable(), status: z.string(), route_source: z.string().nullable(),
      result_code: z.string().nullable(), requester_user_id: uuid, reason: z.string().nullable(), created_at: timestamp,
      lost_record: itemRecord.nullable(), candidate: reviewCandidate.nullable(), candidates: z.array(reviewCandidate),
      evidence: z.array(z.object({
        attempt_no: z.number().int(), result_code: z.string(), answer_summary: z.record(z.string(), z.unknown()).nullable(),
        risk_flag: z.string().nullable(), created_at: timestamp,
      }).strict()),
    }).strict()
    expect(claim.parse(claimFixture)).toEqual(claimFixture)
    expect(review.parse(reviewFixture)).toEqual(reviewFixture)
  })

  it('parses audit and upload responses without private fields', () => {
    const audit = z.object({
      event_id: uuid, event_type: z.string(), aggregate_type: z.string(), aggregate_id: uuid,
      result_code: z.string(), metadata_redacted: z.record(z.string(), z.unknown()), created_at: timestamp,
    }).strict()
    const upload = z.object({ image_asset_id: uuid, purpose: z.enum(['FINDER_ORIGINAL', 'PUBLIC_REDACTED', 'OWNER_SUPPORT']) }).strict()
    expect(audit.parse(auditFixture)).toEqual(auditFixture)
    expect(upload.parse(uploadFixture)).toEqual(uploadFixture)
    expect(JSON.stringify({ auditFixture, uploadFixture })).not.toMatch(/object_key|full_number|answer_key|access_token/)
  })

  it('parses raw matching SSE data events', () => {
    const base = z.object({ stage: z.string(), progress: z.number().min(0).max(100) }).strict()
    expect(base.parse(sseFixtures.progress)).toEqual(sseFixtures.progress)
    expect(base.parse(sseFixtures.done)).toEqual(sseFixtures.done)
    expect(base.extend({ error_code: z.string() }).parse(sseFixtures.error)).toEqual(sseFixtures.error)
  })

  it.each(errorFixtures)('parses canonical $status errors without FastAPI detail', ({ body }) => {
    const error = z.object({
      error_code: z.string(), message: z.string(), field_errors: z.record(z.string(), z.string()).optional(),
    }).strict()
    expect(error.parse(body)).toEqual(body)
    expect(body).not.toHaveProperty('detail')
  })
})
