"""
生成持久化种子数据并写入数据库（一次性插入）。

用法：
    python -m scripts.seed_persistent          # 插入到数据库
    python -m scripts.seed_persistent --sql    # 仅打印 SQL（不需要数据库连接）

数据设计：
    - 2 个普通用户（张明 / 李婷）+ 1 个管理员（赵管理）
    - 场景 A：张明丢失笔记本电脑，李婷拾到 → 完整认领生命周期
    - 场景 B：李婷丢失居民身份证，张明拾到 → 身份证明文件流程
    - 每次状态变更都有完整的审计记录
    - 管理员审核记录附带证据说明
"""

from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4, uuid5

# ---------------------------------------------------------------------------
# 确定性 UUID（基于 uuid5，可复现）
# ---------------------------------------------------------------------------
NS = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _uid(label: str) -> str:
    """根据标签生成确定性 UUID 字符串。"""
    return str(uuid5(NS, label))


# ---------------------------------------------------------------------------
# 时间戳（Asia/Shanghai，存储为 UTC）
# ---------------------------------------------------------------------------
UTC = timezone.utc
CST = timezone(timedelta(hours=8))

NOW = datetime(2026, 7, 17, 10, 0, 0, tzinfo=UTC)  # 参考时间点


def _ts(days_ago: int, hour: int = 10, minute: int = 0) -> str:
    """返回距离 NOW 之前 days_ago 天的 ISO 时间戳字符串。"""
    dt = NOW - timedelta(days=days_ago, hours=NOW.hour - hour, minutes=NOW.minute - minute)
    return dt.strftime("%Y-%m-%d %H:%M:%S+00")


def _ts_cst(days_ago: int, hour: int = 10) -> str:
    """返回北京时间格式的时间字符串，用于 event_time_public 字段。"""
    dt = (NOW - timedelta(days=days_ago)).astimezone(CST).replace(hour=hour, minute=0)
    return dt.strftime("%Y年%m月%d日 %H:%M")


# ---------------------------------------------------------------------------
# 密码哈希（通过 pwdlib 生成 argon2 哈希）
# ---------------------------------------------------------------------------
def _hash_password(password: str) -> str:
    """生成与 pwdlib PasswordHash.recommended() 兼容的密码哈希。"""
    try:
        from pwdlib import PasswordHash
        return PasswordHash.recommended().hash(password)
    except ImportError:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ---------------------------------------------------------------------------
# SQL 构造辅助函数
# ---------------------------------------------------------------------------
_lines: list[str] = []


def _sql(stmt: str) -> None:
    _lines.append(stmt.strip())


def _insert(table: str, columns: list[str], rows: list[tuple]) -> None:
    """生成多行 INSERT 语句。"""
    col_str = ", ".join(columns)
    for row in rows:
        vals = ", ".join(_format(v) for v in row)
        _sql(f"INSERT INTO {table} ({col_str}) VALUES ({vals});")


def _format(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, Decimal)):
        return str(v)
    if isinstance(v, bytes):
        return "'\\x" + v.hex() + "'::bytea"
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    raise TypeError(f"不支持的类型: {type(v)}")


# ---------------------------------------------------------------------------
# 数据定义
# ---------------------------------------------------------------------------
def build_seed(password_hash: str) -> None:
    """构造所有 INSERT 语句。"""

    _sql("-- ============================================================")
    _sql("-- 持久化种子数据（一次性插入）")
    _sql("-- 由 scripts/seed_persistent.py 自动生成")
    _sql("-- ============================================================")
    _sql("")

    # ------------------------------------------------------------------
    # 1. 用户表
    # ------------------------------------------------------------------
    _sql("-- 1. 用户表")
    user_zhang_id = _uid("user-zhangming")
    user_li_id = _uid("user-liting")
    admin_id = _uid("admin-zhaoguanli")

    _insert("users", [
        "id", "username", "email", "password_hash", "role", "created_at",
    ], [
        (user_zhang_id, "张明", "zhangming@example.test", password_hash, "USER", _ts(30)),
        (user_li_id, "李婷", "liting@example.test", password_hash, "USER", _ts(28)),
        (admin_id, "赵管理", "admin@example.test", password_hash, "ADMIN", _ts(30)),
    ])
    _sql("")

    # ------------------------------------------------------------------
    # 2. 物品记录表
    # ------------------------------------------------------------------
    _sql("-- 2. 物品记录表")

    # --- 场景 A：张明丢失笔记本电脑，李婷拾到 ---
    lost_laptop_id = _uid("record-lost-laptop")
    found_laptop_id = _uid("record-found-laptop")

    # --- 场景 B：李婷丢失居民身份证，张明拾到 ---
    lost_student_id = _uid("record-lost-student-id")
    found_student_id = _uid("record-found-student-id")

    _insert("item_records", [
        "id", "owner_user_id", "kind", "item_type", "public_category",
        "location_area", "status", "name_public", "description_public",
        "event_time_exact", "event_time_public", "location_public",
        "published_at", "version", "created_at", "updated_at",
    ], [
        # 场景 A：张明丢失的笔记本电脑（完整认领生命周期）
        (lost_laptop_id, user_zhang_id, "LOST", "OTHER", "ELECTRONICS",
         "LIBRARY", "CLAIMED", "灰色华为笔记本电脑",
         "灰色华为笔记本电脑，A面中央有HUAWEI标志，内含重要毕业设计资料。",
         _ts(7, 14), _ts_cst(7, 14), "图书馆三楼自习区",
         _ts(7, 16), 3, _ts(7, 14), _ts(1, 10)),

        # 场景 A：李婷拾到的笔记本电脑（完整认领生命周期）
        (found_laptop_id, user_li_id, "FOUND", "OTHER", "ELECTRONICS",
         "LIBRARY", "CLAIMED", "灰色华为笔记本电脑",
         "拾到灰色华为笔记本电脑，合盖状态，外壳中央有HUAWEI品牌标志。",
         _ts(7, 15), _ts_cst(7, 15), "图书馆三楼自习区充电桌",
         _ts(7, 17), 3, _ts(7, 15), _ts(1, 10)),

        # 场景 B：李婷丢失的居民身份证（完整认领生命周期）
        (lost_student_id, user_li_id, "LOST", "IDENTITY_DOCUMENT", "IDENTITY_CARD",
         "CANTEEN", "CLAIMED", "居民身份证",
         "蓝色居民身份证，装在透明卡套中；姓名及号码不公开。",
         _ts(5, 12), _ts_cst(5, 12), "一食堂一楼靠窗座位",
         _ts(5, 14), 3, _ts(5, 12), _ts(2, 10)),

        # 场景 B：张明拾到的居民身份证（完整认领生命周期）
        (found_student_id, user_zhang_id, "FOUND", "IDENTITY_DOCUMENT", "IDENTITY_CARD",
         "CANTEEN", "CLAIMED", "居民身份证",
         "拾到一张装在透明卡套中的居民身份证，敏感信息已脱敏。",
         _ts(5, 13), _ts_cst(5, 13), "一食堂一楼靠窗座位下方",
         _ts(5, 15), 3, _ts(5, 13), _ts(2, 10)),
    ])
    _sql("")

    # ------------------------------------------------------------------
    # 3. AI 提取记录表
    # ------------------------------------------------------------------
    _sql("-- 3. AI 提取记录表")

    ai_ext_laptop_lost = _uid("ai-ext-lost-laptop")
    ai_ext_laptop_found = _uid("ai-ext-found-laptop")
    ai_ext_id_lost = _uid("ai-ext-lost-id")
    ai_ext_id_found = _uid("ai-ext-found-id")

    _insert("ai_extractions", [
        "id", "record_id", "provider", "model", "version",
        "raw_result_redacted", "suggested_item_type", "draft_snapshot",
        "confidence", "confirmed_snapshot", "status", "created_at",
    ], [
        (ai_ext_laptop_lost, lost_laptop_id, "xiaomi-ai", "multimodal-v2", "1.0.0",
         '{"描述": "灰色华为笔记本电脑"}', "OTHER",
         '{"name_public": "灰色华为笔记本电脑", "public_category": "ELECTRONICS"}',
         '{"置信度": 0.95}', '{"name_public": "灰色华为笔记本电脑"}', "SUCCEEDED", _ts(7, 14, 30)),

        (ai_ext_laptop_found, found_laptop_id, "xiaomi-ai", "multimodal-v2", "1.0.0",
         '{"描述": "灰色华为笔记本电脑合盖"}', "OTHER",
         '{"name_public": "灰色华为笔记本电脑", "public_category": "ELECTRONICS"}',
         '{"置信度": 0.93}', '{"name_public": "灰色华为笔记本电脑"}', "SUCCEEDED", _ts(7, 15, 30)),

        (ai_ext_id_lost, lost_student_id, "xiaomi-ai", "multimodal-v2", "1.0.0",
         '{"描述": "居民身份证卡套"}', "IDENTITY_DOCUMENT",
         '{"name_public": "居民身份证", "public_category": "IDENTITY_CARD"}',
         '{"置信度": 0.98}', '{"name_public": "居民身份证"}', "SUCCEEDED", _ts(5, 12, 30)),

        (ai_ext_id_found, found_student_id, "xiaomi-ai", "multimodal-v2", "1.0.0",
         '{"描述": "透明卡套内居民身份证"}', "IDENTITY_DOCUMENT",
         '{"name_public": "居民身份证", "public_category": "IDENTITY_CARD"}',
         '{"置信度": 0.97}', '{"name_public": "居民身份证"}', "SUCCEEDED", _ts(5, 13, 30)),
    ])
    _sql("")

    # ------------------------------------------------------------------
    # 4. 候选匹配记录表
    # ------------------------------------------------------------------
    _sql("-- 4. 候选匹配记录表")

    candidate_laptop_id = _uid("candidate-laptop")
    candidate_id_card_id = _uid("candidate-id-card")

    _insert("candidate_matches", [
        "id", "lost_record_id", "found_record_id",
        "semantic_score", "time_score", "location_score", "completeness_score",
        "total_score", "reason_codes", "conflict_codes",
        "rule_version", "model_version", "input_snapshot_hash", "created_at",
    ], [
        (candidate_laptop_id, lost_laptop_id, found_laptop_id,
         Decimal("38.00"), Decimal("19.00"), Decimal("20.00"), Decimal("18.00"),
         Decimal("95.00"),
         '["分类匹配","语义描述匹配","时间窗口匹配","同一区域"]',
         '[]',
         "v1.0.0", "multimodal-v2", hashlib.sha256(b"laptop-match").hexdigest(), _ts(6, 10)),

        (candidate_id_card_id, lost_student_id, found_student_id,
         Decimal("39.00"), Decimal("18.00"), Decimal("20.00"), Decimal("17.00"),
         Decimal("94.00"),
         '["分类匹配","语义描述匹配","时间窗口匹配","同一区域"]',
         '[]',
         "v1.0.0", "multimodal-v2", hashlib.sha256(b"id-card-match").hexdigest(), _ts(4, 10)),
    ])
    _sql("")

    # ------------------------------------------------------------------
    # 5. 验证集与验证问题（用于笔记本电脑认领）
    # ------------------------------------------------------------------
    _sql("-- 5. 验证信息（笔记本电脑认领）")

    vset_laptop_id = _uid("vset-laptop")
    vq_laptop_1_id = _uid("vq-laptop-1")
    vq_laptop_2_id = _uid("vq-laptop-2")
    vq_laptop_3_id = _uid("vq-laptop-3")

    _insert("verification_sets", [
        "id", "found_record_id", "item_type", "hidden_description",
        "confirmed_by", "confirmed_at", "created_at",
    ], [
        (vset_laptop_id, found_laptop_id, "OTHER",
         "华为MateBook 14，2024款，银灰色，A面有HUAWEI标志，屏幕14寸，内含毕业设计PPT和代码文件",
         user_li_id, _ts(6, 11), _ts(6, 10, 30)),
    ])

    _insert("verification_questions", [
        "id", "verification_set_id", "question_text", "answer_key",
        "dimension", "provider_model", "schema_version",
        "confirmed_by", "confirmed_at", "created_at",
    ], [
        (vq_laptop_1_id, vset_laptop_id, "笔记本电脑的品牌是什么？", "华为/HUAWEI",
         "品牌", "multimodal-v2", "1.0.0", user_li_id, _ts(6, 11), _ts(6, 10, 31)),
        (vq_laptop_2_id, vset_laptop_id, "笔记本电脑大约是什么颜色？", "银灰色/灰色",
         "颜色", "multimodal-v2", "1.0.0", user_li_id, _ts(6, 11), _ts(6, 10, 32)),
        (vq_laptop_3_id, vset_laptop_id, "电脑里有什么重要文件类型？", "PPT/毕业设计/代码",
         "内容", "multimodal-v2", "1.0.0", user_li_id, _ts(6, 11), _ts(6, 10, 33)),
    ])
    _sql("")

    # 身份证明文件密钥记录（用于身份证认领）
    _sql("-- 身份证明文件密钥")
    _insert("identity_document_secrets", [
        "found_record_id", "item_type", "document_type",
        "number_hmac", "number_masked", "key_version",
        "finder_confirmed_at", "created_at",
    ], [
        (found_student_id, "IDENTITY_DOCUMENT", "CN_RESIDENT_ID",
         hashlib.sha256(b"fake-id-number-hmac").digest(),
         "110***********1234", 1,
         _ts(4, 14), _ts(5, 13, 30)),
    ])
    _sql("")

    # ------------------------------------------------------------------
    # 6. 认领记录表（完整生命周期）
    # ------------------------------------------------------------------
    _sql("-- 6. 认领记录表")

    claim_laptop_id = _uid("claim-laptop")
    claim_id_card_id = _uid("claim-id-card")

    _insert("claims", [
        "id", "candidate_id", "requester_user_id", "item_type",
        "status", "route_source", "final_reason",
        "created_at", "updated_at",
    ], [
        # 张明认领笔记本电脑（李婷拾到的）
        (claim_laptop_id, candidate_laptop_id, user_zhang_id, "OTHER",
         "CLAIMED", "MATCH_SYSTEM", None,
         _ts(6, 12), _ts(1, 10)),

        # 李婷认领居民身份证（张明拾到的）
        (claim_id_card_id, candidate_id_card_id, user_li_id, "IDENTITY_DOCUMENT",
         "CLAIMED", "MATCH_SYSTEM", None,
         _ts(4, 12), _ts(2, 10)),
    ])
    _sql("")

    # ------------------------------------------------------------------
    # 7. 认领尝试记录表
    # ------------------------------------------------------------------
    _sql("-- 7. 认领尝试记录表")

    _insert("claim_attempts", [
        "id", "claim_id", "user_id", "candidate_id", "attempt_no",
        "submitted_hmac", "result_code", "answer_summary", "risk_flag",
        "created_at",
    ], [
        # 张明的笔记本电脑验证尝试
        (_uid("attempt-laptop-1"), claim_laptop_id, user_zhang_id, candidate_laptop_id, 1,
         hashlib.sha256(b"laptop-verify-1").digest(), "通过",
         '{"品牌": "匹配", "颜色": "匹配", "内容": "匹配"}', None,
         _ts(6, 13)),

        # 李婷的居民身份证验证尝试
        (_uid("attempt-id-1"), claim_id_card_id, user_li_id, candidate_id_card_id, 1,
         hashlib.sha256(b"id-verify-1").digest(), "通过",
         '{"身份提示": "匹配"}', None,
         _ts(4, 13)),
    ])
    _sql("")

    # ------------------------------------------------------------------
    # 8. 审核请求表（两个认领都需要管理员审核）
    # ------------------------------------------------------------------
    _sql("-- 8. 审核请求表")

    review_laptop_id = _uid("review-laptop")
    review_id_card_id = _uid("review-id-card")

    _insert("review_requests", [
        "id", "requester_user_id", "request_type", "lost_record_id",
        "claim_id", "reason", "status", "candidate_snapshot_id",
        "active", "created_at", "resolved_at",
    ], [
        # 笔记本电脑认领的管理员审核
        (review_laptop_id, user_zhang_id, "CLAIM_REVIEW", None,
         claim_laptop_id, "系统匹配成功，请管理员审核物证交接", "已解决",
         candidate_laptop_id, False, _ts(5, 10), _ts(3, 14)),

        # 居民身份证认领的管理员审核
        (review_id_card_id, user_li_id, "CLAIM_REVIEW", None,
         claim_id_card_id, "身份证明文件匹配，请管理员审核身份验证", "已解决",
         candidate_id_card_id, False, _ts(3, 10), _ts(2, 14)),
    ])
    _sql("")

    # ------------------------------------------------------------------
    # 9. 管理员审核记录表
    # ------------------------------------------------------------------
    _sql("-- 9. 管理员审核记录表")

    _insert("admin_reviews", [
        "id", "review_request_id", "claim_id", "reviewer_user_id",
        "decision", "reason", "evidence_data_class", "created_at",
    ], [
        # 管理员批准笔记本电脑交接
        (_uid("admin-review-laptop"), review_laptop_id, claim_laptop_id, admin_id,
         "批准交接",
         "验证问答全部通过，物品描述与图片一致，批准交接",
         "公开数据", _ts(3, 14)),

        # 管理员批准居民身份证交接
        (_uid("admin-review-id-card"), review_id_card_id, claim_id_card_id, admin_id,
         "批准交接",
         "身份证明文件匹配确认，脱敏信息一致，批准交接",
         "验证数据", _ts(2, 14)),
    ])
    _sql("")

    # ------------------------------------------------------------------
    # 10. 图片资产表
    # ------------------------------------------------------------------
    _sql("-- 10. 图片资产表")

    _insert("image_assets", [
        "id", "record_id", "uploader_user_id", "purpose", "data_class",
        "object_key", "sha256", "mime_type", "size_bytes",
        "redaction_status", "created_at",
    ], [
        # 笔记本电脑图片
        (_uid("img-laptop-found-original"), found_laptop_id, user_li_id,
         "拾到者原始照片", "私有数据",
         "private/seed/laptop-found-original.jpg",
         hashlib.sha256(b"laptop-original-image-data").hexdigest(),
         "image/jpeg", 204800, "无需脱敏", _ts(7, 15, 30)),

        (_uid("img-laptop-found-public"), found_laptop_id, user_li_id,
         "公开脱敏照片", "公开数据",
         "public/seed/laptop-found-public.jpg",
         hashlib.sha256(b"laptop-public-image-data").hexdigest(),
         "image/jpeg", 102400, "已确认脱敏", _ts(7, 16)),

        (_uid("img-laptop-lost-public"), lost_laptop_id, user_zhang_id,
         "公开脱敏照片", "公开数据",
         "public/seed/laptop-lost-public.jpg",
         hashlib.sha256(b"laptop-lost-image-data").hexdigest(),
         "image/jpeg", 102400, "已确认脱敏", _ts(7, 14, 30)),

        # 居民身份证图片
        (_uid("img-id-found-original"), found_student_id, user_zhang_id,
         "拾到者原始照片", "私有数据",
         "private/seed/id-found-original.jpeg",
         hashlib.sha256(b"id-original-image-data").hexdigest(),
         "image/jpeg", 153600, "无需脱敏", _ts(5, 13, 30)),

        (_uid("img-id-found-public"), found_student_id, user_zhang_id,
         "公开脱敏照片", "公开数据",
         "public/seed/id-found-public.png",
         hashlib.sha256(b"id-public-image-data").hexdigest(),
         "image/png", 51200, "已确认脱敏", _ts(5, 14)),

        (_uid("img-id-lost-public"), lost_student_id, user_li_id,
         "公开脱敏照片", "公开数据",
         "public/seed/id-lost-public.png",
         hashlib.sha256(b"id-lost-image-data").hexdigest(),
         "image/png", 51200, "已确认脱敏", _ts(5, 12, 30)),
    ])
    _sql("")

    # ------------------------------------------------------------------
    # 11. 审计事件表（两个场景的完整生命周期）
    # ------------------------------------------------------------------
    _sql("-- 11. 审计事件表")

    def _audit(event_type: str, aggregate_type: str, aggregate_id: str,
               actor_type: str, actor_id: str | None, result_code: str,
               metadata: str, created_at: str,
               rule_version: str | None = None,
               model_version: str | None = None) -> tuple:
        return (
            str(uuid4()), aggregate_type, aggregate_id, event_type,
            actor_type, actor_id, None,  # request_id
            rule_version, model_version,
            None,  # input_snapshot_hash
            result_code, metadata, created_at,
        )

    audit_cols = [
        "event_id", "aggregate_type", "aggregate_id", "event_type",
        "actor_type", "actor_id", "request_id",
        "rule_version", "model_version", "input_snapshot_hash",
        "result_code", "metadata_redacted", "created_at",
    ]

    audit_rows = [
        # ===== 场景 A：笔记本电脑生命周期 =====

        # 张明创建丢失记录
        _audit("RECORD_CREATED", "ItemRecord", lost_laptop_id,
               "所有者", user_zhang_id, "成功",
               '{"类型": "丢失", "公开分类": "电子设备"}', _ts(7, 14)),

        # AI 提取丢失笔记本信息
        _audit("AI_EXTRACTION_COMPLETED", "AIExtraction", ai_ext_laptop_lost,
               "AI", None, "成功",
               '{"建议物品类型": "其他", "置信度": 0.95}',
               _ts(7, 14, 30), model_version="multimodal-v2"),

        # 丢失记录发布
        _audit("RECORD_STATUS_CHANGED", "ItemRecord", lost_laptop_id,
               "系统", None, "成功",
               '{"原状态": "草稿", "新状态": "已发布"}', _ts(7, 16)),

        # 李婷创建拾到记录
        _audit("RECORD_CREATED", "ItemRecord", found_laptop_id,
               "拾到者", user_li_id, "成功",
               '{"类型": "拾到", "公开分类": "电子设备"}', _ts(7, 15)),

        # AI 提取拾到笔记本信息
        _audit("AI_EXTRACTION_COMPLETED", "AIExtraction", ai_ext_laptop_found,
               "AI", None, "成功",
               '{"建议物品类型": "其他", "置信度": 0.93}',
               _ts(7, 15, 30), model_version="multimodal-v2"),

        # 拾到记录发布
        _audit("RECORD_STATUS_CHANGED", "ItemRecord", found_laptop_id,
               "系统", None, "成功",
               '{"原状态": "草稿", "新状态": "已发布"}', _ts(7, 17)),

        # 匹配系统找到候选匹配
        _audit("CANDIDATE_MATCH_CREATED", "CandidateMatch", candidate_laptop_id,
               "系统", None, "成功",
               '{"丢失记录ID": "' + lost_laptop_id + '", "拾到记录ID": "' + found_laptop_id + '", "总分": 95.0}',
               _ts(6, 10), rule_version="v1.0.0", model_version="multimodal-v2"),

        # 验证集创建
        _audit("VERIFICATION_SET_CREATED", "VerificationSet", vset_laptop_id,
               "系统", None, "成功",
               '{"问题数量": 3}', _ts(6, 10, 30)),

        # 李婷（拾到者）确认验证问题
        _audit("VERIFICATION_CONFIRMED", "VerificationSet", vset_laptop_id,
               "拾到者", user_li_id, "成功",
               '{"已确认问题数": 3}', _ts(6, 11)),

        # 张明提交认领申请
        _audit("CLAIM_SUBMITTED", "Claim", claim_laptop_id,
               "所有者", user_zhang_id, "成功",
               '{"候选匹配ID": "' + candidate_laptop_id + '", "物品类型": "其他"}', _ts(6, 12)),

        # 张明通过验证
        _audit("CLAIM_ATTEMPT_RESULT", "ClaimAttempt", _uid("attempt-laptop-1"),
               "所有者", user_zhang_id, "通过",
               '{"答案": {"品牌": "匹配", "颜色": "匹配", "内容": "匹配"}}', _ts(6, 13)),

        # 认领进入待管理员审核状态
        _audit("CLAIM_STATUS_CHANGED", "Claim", claim_laptop_id,
               "系统", None, "成功",
               '{"原状态": "验证中", "新状态": "待管理员审核"}', _ts(6, 13, 5)),

        # 审核请求创建
        _audit("REVIEW_REQUEST_CREATED", "ReviewRequest", review_laptop_id,
               "系统", None, "成功",
               '{"请求类型": "认领审核", "认领ID": "' + claim_laptop_id + '"}', _ts(5, 10)),

        # 管理员审核并批准
        _audit("ADMIN_REVIEW_DECISION", "AdminReview", _uid("admin-review-laptop"),
               "管理员", admin_id, "批准交接",
               '{"决定": "批准交接", "原因": "验证问答全部通过，物品描述与图片一致，批准交接"}', _ts(3, 14)),

        # 认领进入待交接状态
        _audit("CLAIM_STATUS_CHANGED", "Claim", claim_laptop_id,
               "管理员", admin_id, "成功",
               '{"原状态": "待管理员审核", "新状态": "待交接"}', _ts(3, 14, 5)),

        # 两条记录都进入待交接状态
        _audit("RECORD_STATUS_CHANGED", "ItemRecord", lost_laptop_id,
               "管理员", admin_id, "成功",
               '{"原状态": "已发布", "新状态": "待交接"}', _ts(3, 15)),

        _audit("RECORD_STATUS_CHANGED", "ItemRecord", found_laptop_id,
               "管理员", admin_id, "成功",
               '{"原状态": "已发布", "新状态": "待交接"}', _ts(3, 15)),

        # 交接完成 → 已认领
        _audit("HANDOFF_COMPLETED", "Claim", claim_laptop_id,
               "管理员", admin_id, "成功",
               '{"交接地点": "失物招领中心", "见证人": "管理员"}', _ts(1, 10)),

        # 最终状态更新
        _audit("CLAIM_STATUS_CHANGED", "Claim", claim_laptop_id,
               "系统", None, "成功",
               '{"原状态": "待交接", "新状态": "已认领"}', _ts(1, 10, 5)),

        _audit("RECORD_STATUS_CHANGED", "ItemRecord", lost_laptop_id,
               "系统", None, "成功",
               '{"原状态": "待交接", "新状态": "已认领"}', _ts(1, 10, 10)),

        _audit("RECORD_STATUS_CHANGED", "ItemRecord", found_laptop_id,
               "系统", None, "成功",
               '{"原状态": "待交接", "新状态": "已认领"}', _ts(1, 10, 10)),

        # ===== 场景 B：居民身份证生命周期 =====

        # 李婷创建丢失记录
        _audit("RECORD_CREATED", "ItemRecord", lost_student_id,
               "所有者", user_li_id, "成功",
               '{"类型": "丢失", "公开分类": "身份证明"}', _ts(5, 12)),

        # AI 提取丢失身份证信息
        _audit("AI_EXTRACTION_COMPLETED", "AIExtraction", ai_ext_id_lost,
               "AI", None, "成功",
               '{"建议物品类型": "身份证明文件", "置信度": 0.98}',
               _ts(5, 12, 30), model_version="multimodal-v2"),

        # 丢失记录发布
        _audit("RECORD_STATUS_CHANGED", "ItemRecord", lost_student_id,
               "系统", None, "成功",
               '{"原状态": "草稿", "新状态": "已发布"}', _ts(5, 14)),

        # 张明创建拾到记录
        _audit("RECORD_CREATED", "ItemRecord", found_student_id,
               "拾到者", user_zhang_id, "成功",
               '{"类型": "拾到", "公开分类": "身份证明"}', _ts(5, 13)),

        # AI 提取拾到身份证信息
        _audit("AI_EXTRACTION_COMPLETED", "AIExtraction", ai_ext_id_found,
               "AI", None, "成功",
               '{"建议物品类型": "身份证明文件", "置信度": 0.97}',
               _ts(5, 13, 30), model_version="multimodal-v2"),

        # 拾到记录发布
        _audit("RECORD_STATUS_CHANGED", "ItemRecord", found_student_id,
               "系统", None, "成功",
               '{"原状态": "草稿", "新状态": "已发布"}', _ts(5, 15)),

        # 身份信息密钥存储
        _audit("IDENTITY_SECRET_STORED", "IdentityDocumentSecret", found_student_id,
               "拾到者", user_zhang_id, "成功",
               '{"证件类型": "居民身份证", "脱敏号码": "110***********1234"}', _ts(5, 14)),

        # 匹配系统找到候选匹配
        _audit("CANDIDATE_MATCH_CREATED", "CandidateMatch", candidate_id_card_id,
               "系统", None, "成功",
               '{"丢失记录ID": "' + lost_student_id + '", "拾到记录ID": "' + found_student_id + '", "总分": 94.0}',
               _ts(4, 10), rule_version="v1.0.0", model_version="multimodal-v2"),

        # 李婷提交认领申请
        _audit("CLAIM_SUBMITTED", "Claim", claim_id_card_id,
               "所有者", user_li_id, "成功",
               '{"候选匹配ID": "' + candidate_id_card_id + '", "物品类型": "身份证明文件"}', _ts(4, 12)),

        # 李婷通过身份验证
        _audit("CLAIM_ATTEMPT_RESULT", "ClaimAttempt", _uid("attempt-id-1"),
               "所有者", user_li_id, "通过",
               '{"答案": {"身份提示": "匹配"}}', _ts(4, 13)),

        # 认领进入待管理员审核状态
        _audit("CLAIM_STATUS_CHANGED", "Claim", claim_id_card_id,
               "系统", None, "成功",
               '{"原状态": "验证中", "新状态": "待管理员审核"}', _ts(4, 13, 5)),

        # 审核请求创建
        _audit("REVIEW_REQUEST_CREATED", "ReviewRequest", review_id_card_id,
               "系统", None, "成功",
               '{"请求类型": "认领审核", "认领ID": "' + claim_id_card_id + '"}', _ts(3, 10)),

        # 管理员审核并批准
        _audit("ADMIN_REVIEW_DECISION", "AdminReview", _uid("admin-review-id-card"),
               "管理员", admin_id, "批准交接",
               '{"决定": "批准交接", "原因": "身份证明文件匹配确认，脱敏信息一致，批准交接"}', _ts(2, 14)),

        # 认领进入待交接状态
        _audit("CLAIM_STATUS_CHANGED", "Claim", claim_id_card_id,
               "管理员", admin_id, "成功",
               '{"原状态": "待管理员审核", "新状态": "待交接"}', _ts(2, 14, 5)),

        # 两条记录都进入待交接状态
        _audit("RECORD_STATUS_CHANGED", "ItemRecord", lost_student_id,
               "管理员", admin_id, "成功",
               '{"原状态": "已发布", "新状态": "待交接"}', _ts(2, 15)),

        _audit("RECORD_STATUS_CHANGED", "ItemRecord", found_student_id,
               "管理员", admin_id, "成功",
               '{"原状态": "已发布", "新状态": "待交接"}', _ts(2, 15)),

        # 交接完成 → 已认领
        _audit("HANDOFF_COMPLETED", "Claim", claim_id_card_id,
               "管理员", admin_id, "成功",
               '{"交接地点": "失物招领中心", "见证人": "管理员"}', _ts(2, 16)),

        # 最终状态更新
        _audit("CLAIM_STATUS_CHANGED", "Claim", claim_id_card_id,
               "系统", None, "成功",
               '{"原状态": "待交接", "新状态": "已认领"}', _ts(2, 16, 5)),

        _audit("RECORD_STATUS_CHANGED", "ItemRecord", lost_student_id,
               "系统", None, "成功",
               '{"原状态": "待交接", "新状态": "已认领"}', _ts(2, 16, 10)),

        _audit("RECORD_STATUS_CHANGED", "ItemRecord", found_student_id,
               "系统", None, "成功",
               '{"原状态": "待交接", "新状态": "已认领"}', _ts(2, 16, 10)),
    ]

    for row in audit_rows:
        vals = ", ".join(_format(v) for v in row)
        _sql(f"INSERT INTO audit_events ({', '.join(audit_cols)}) VALUES ({vals});")

    _sql("")

    # ------------------------------------------------------------------
    # 数据汇总
    # ------------------------------------------------------------------
    _sql("-- ============================================================")
    _sql("-- 种子数据汇总")
    _sql("-- ============================================================")
    _sql("-- 用户：3 人（张明、李婷、赵管理[管理员]）")
    _sql("-- 所有用户密码：Xiaoming123!")
    _sql("--")
    _sql("-- 场景 A：张明丢失笔记本电脑 → 李婷拾到 → 系统匹配 → 认领成功")
    _sql("--   丢失记录：  " + lost_laptop_id)
    _sql("--   拾到记录：  " + found_laptop_id)
    _sql("--   认领记录：  " + claim_laptop_id)
    _sql("--")
    _sql("-- 场景 B：李婷丢失居民身份证 → 张明拾到 → 系统匹配 → 认领成功")
    _sql("--   丢失记录：  " + lost_student_id)
    _sql("--   拾到记录：  " + found_student_id)
    _sql("--   认领记录：  " + claim_id_card_id)
    _sql("--")
    _sql("-- 管理员：赵管理审核并批准了两个认领申请")
    _sql("-- ============================================================")


# ---------------------------------------------------------------------------
# 主程序入口
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="生成持久化种子数据")
    parser.add_argument("--sql", action="store_true", help="仅打印 SQL，不写入数据库")
    args = parser.parse_args()

    password = "Xiaoming123!"
    password_hash = _hash_password(password)
    build_seed(password_hash)

    sql_text = "\n".join(_lines) + "\n"

    if args.sql:
        out_path = Path(__file__).resolve().parents[1] / "scripts" / "seed_persistent.sql"
        out_path.write_text(sql_text, encoding="utf-8")
        print(f"SQL 已写入: {out_path}")
        print(f"\n登录凭据:")
        print(f"  张明（普通用户）：zhangming@example.test / {password}")
        print(f"  李婷（普通用户）：liting@example.test / {password}")
        print(f"  赵管理（管理员）：admin@example.test / {password}")
        return

    # 写入数据库
    import asyncio
    from app.database import session_factory

    async def _run() -> None:
        async with session_factory() as session:
            async with session.begin():
                for line in _lines:
                    line = line.strip()
                    if line and not line.startswith("--"):
                        await session.execute(__import__("sqlalchemy").text(line))
            await session.commit()
        print("种子数据插入成功。")
        print(f"\n登录凭据:")
        print(f"  张明（普通用户）：zhangming@example.test / {password}")
        print(f"  李婷（普通用户）：liting@example.test / {password}")
        print(f"  赵管理（管理员）：admin@example.test / {password}")

    asyncio.run(_run())


if __name__ == "__main__":
    main()
