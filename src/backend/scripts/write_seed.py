"""
将 seed_persistent.sql 写入数据库（修正枚举值后）。
用法：python -m scripts.write_seed
"""
import asyncio
import re
from pathlib import Path

# 中文 → 英文枚举映射
ENUM_MAP = {
    # actor_type
    "'所有者'": "'OWNER'",
    "'拾到者'": "'FINDER'",
    "'管理员'": "'ADMIN'",
    "'系统'": "'SYSTEM'",
    # admin_decision
    "'批准交接'": "'APPROVE_TO_HANDOFF'",
    # claim_status
    "'已认领'": "'CLAIMED'",
    "'待管理员审核'": "'PENDING_ADMIN_REVIEW'",
    "'待交接'": "'PENDING_HANDOFF'",
    "'验证中'": "'VERIFYING'",
    # data_class
    "'私有数据'": "'PRIVATE'",
    "'公开数据'": "'PUBLIC'",
    "'验证数据'": "'VERIFICATION'",
    # extraction_status
    "'SUCCEEDED'": "'SUCCEEDED'",  # already English
    # image_purpose
    "'拾到者原始照片'": "'FINDER_ORIGINAL'",
    "'公开脱敏照片'": "'PUBLIC_REDACTED'",
    # item_type
    "'身份证明文件'": "'IDENTITY_DOCUMENT'",
    # location_area
    "'图书馆'": "'LIBRARY'",
    "'一食堂'": "'CANTEEN'",
    # public_category
    "'电子设备'": "'ELECTRONICS'",
    "'身份证明'": "'IDENTITY_CARD'",
    # record_kind
    "'丢失'": "'LOST'",
    "'拾到'": "'FOUND'",
    # record_status
    "'草稿'": "'DRAFT'",
    "'已发布'": "'PUBLISHED'",
    # redaction_status
    "'无需脱敏'": "'NOT_REQUIRED'",
    "'已确认脱敏'": "'CONFIRMED'",
    # review_request_type
    "'认领审核'": "'CLAIM_REVIEW'",
    # review status
    "'已解决'": "'RESOLVED'",
    # result_code / misc string fields (not enums, but Chinese)
    "'成功'": "'OK'",
    "'通过'": "'PASS'",
    # status in review_requests
}

# JSON 值中的中文键值对（保持原样，这些是 metadata 不是枚举）
# reason_codes 中文标签保持原样（是 JSON 字符串，不是枚举列）


def fix_sql(sql: str) -> str:
    """修正 SQL 中的中文枚举值为英文。"""
    for cn, en in ENUM_MAP.items():
        sql = sql.replace(cn, en)
    return sql


# 需要按外键依赖顺序清理的表
CLEANUP_ORDER = [
    "audit_events",
    "admin_reviews",
    "review_requests",
    "claim_attempts",
    "claims",
    "identity_document_secrets",
    "verification_questions",
    "verification_sets",
    "image_assets",
    "candidate_matches",
    "ai_extractions",
    "item_records",
    "users",
]


async def main():
    from app.database import session_factory
    from sqlalchemy import text

    # 读取 SQL 文件
    sql_path = Path(__file__).resolve().parent / "seed_persistent.sql"
    raw_sql = sql_path.read_text(encoding="utf-8")

    # 修正枚举值
    fixed_sql = fix_sql(raw_sql)

    # 提取所有 INSERT 语句
    statements = []
    for line in fixed_sql.splitlines():
        line = line.strip()
        if line and not line.startswith("--"):
            statements.append(line)

    async with session_factory() as session:
        async with session.begin():
            # 1. 清理旧数据（按外键依赖顺序）
            print("清理旧数据...")
            for table in CLEANUP_ORDER:
                await session.execute(text(f"DELETE FROM {table}"))
            # 也清理可能残留的表
            for extra in ["refresh_tokens"]:
                try:
                    await session.execute(text(f"DELETE FROM {extra}"))
                except Exception:
                    pass

            # 2. 插入新数据
            print(f"插入 {len(statements)} 条 SQL...")
            for i, stmt in enumerate(statements, 1):
                try:
                    await session.execute(text(stmt))
                except Exception as e:
                    print(f"  ❌ 第 {i} 条失败: {e}")
                    print(f"     SQL: {stmt[:120]}...")
                    raise

        await session.commit()
        print(f"\n✅ 成功写入 {len(statements)} 条记录！")
        print("\n登录凭据:")
        print("  张明（普通用户）：zhangming@example.test / Xiaoming123!")
        print("  李婷（普通用户）：liting@example.test / Xiaoming123!")
        print("  赵管理（管理员）：admin@example.test / Xiaoming123!")


if __name__ == "__main__":
    asyncio.run(main())
