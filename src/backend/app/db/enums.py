from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class ItemType(str, Enum):
    IDENTITY_DOCUMENT = "IDENTITY_DOCUMENT"
    OTHER = "OTHER"


class RecordKind(str, Enum):
    LOST = "LOST"
    FOUND = "FOUND"


class RecordStatus(str, Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    PUBLISHED = "PUBLISHED"
    MATCHING_FAILED = "MATCHING_FAILED"
    PENDING_HANDOFF = "PENDING_HANDOFF"
    CLAIMED = "CLAIMED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class ClaimStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    VERIFYING = "VERIFYING"
    PENDING_ADMIN_REVIEW = "PENDING_ADMIN_REVIEW"
    PENDING_HANDOFF = "PENDING_HANDOFF"
    REJECTED = "REJECTED"
    CLAIMED = "CLAIMED"
    LOCKED = "LOCKED"


class DataClass(str, Enum):
    PUBLIC = "PUBLIC"
    MATCH_ONLY = "MATCH_ONLY"
    VERIFICATION = "VERIFICATION"
    PRIVATE = "PRIVATE"


class ActorType(str, Enum):
    OWNER = "OWNER"
    FINDER = "FINDER"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"
    AI = "AI"


class ImagePurpose(str, Enum):
    FINDER_ORIGINAL = "FINDER_ORIGINAL"
    PUBLIC_REDACTED = "PUBLIC_REDACTED"
    OWNER_SUPPORT = "OWNER_SUPPORT"


class RedactionStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class ExtractionStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    INVALID = "INVALID"
    TIMEOUT = "TIMEOUT"
    FALLBACK = "FALLBACK"


class QuestionResult(str, Enum):
    MATCH = "MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    UNDETERMINED = "UNDETERMINED"
    CONFLICT = "CONFLICT"


class DocumentType(str, Enum):
    CN_RESIDENT_ID = "CN_RESIDENT_ID"


class AdminDecision(str, Enum):
    APPROVE_TO_HANDOFF = "APPROVE_TO_HANDOFF"
    REJECT = "REJECT"


class ReviewRequestType(str, Enum):
    UNMATCHED = "UNMATCHED"
    CLAIM_REVIEW = "CLAIM_REVIEW"
