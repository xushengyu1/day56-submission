"""Persist matching category and location area."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260717_0007"
down_revision: str | None = "20260716_0006"
branch_labels: str | None = None
depends_on: str | None = None


public_category = postgresql.ENUM(
    "ELECTRONICS",
    "IDENTITY_CARD",
    "CLOTHING",
    "STATIONERY",
    "OTHER_CATEGORY",
    name="public_category",
    create_type=False,
)
location_area = postgresql.ENUM(
    "DORMITORY",
    "CANTEEN",
    "TEACHING_BUILDING",
    "SCIENCE_BUILDING",
    "LIBRARY",
    name="location_area",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    public_category.create(bind, checkfirst=False)
    location_area.create(bind, checkfirst=False)
    op.add_column(
        "item_records", sa.Column("public_category", public_category, nullable=True)
    )
    op.add_column(
        "item_records", sa.Column("location_area", location_area, nullable=True)
    )

    op.execute(
        """
        DO $$
        DECLARE invalid_values text;
        BEGIN
          SELECT string_agg(
            DISTINCT COALESCE(location_public, '<NULL>'), ', '
          )
          INTO invalid_values
          FROM item_records
          WHERE location_public IS NULL
             OR location_public NOT IN (
               '宿舍区', '食堂', '教学楼', '科教楼', '图书馆'
             );
          IF invalid_values IS NOT NULL THEN
            RAISE EXCEPTION 'UNMAPPABLE_LOCATION_PUBLIC: %', invalid_values;
          END IF;
        END $$;
        """
    )
    op.execute(
        """
        UPDATE item_records
        SET public_category = CASE item_type::text
          WHEN 'IDENTITY_DOCUMENT' THEN 'IDENTITY_CARD'::public_category
          ELSE 'OTHER_CATEGORY'::public_category
        END,
        location_area = CASE location_public
          WHEN '宿舍区' THEN 'DORMITORY'::location_area
          WHEN '食堂' THEN 'CANTEEN'::location_area
          WHEN '教学楼' THEN 'TEACHING_BUILDING'::location_area
          WHEN '科教楼' THEN 'SCIENCE_BUILDING'::location_area
          WHEN '图书馆' THEN 'LIBRARY'::location_area
        END
        """
    )
    op.alter_column("item_records", "public_category", nullable=False)
    op.alter_column("item_records", "location_area", nullable=False)

    op.drop_index("ix_item_records_match_filter", table_name="item_records")
    op.create_index(
        "ix_item_records_match_taxonomy",
        "item_records",
        [
            "kind",
            "public_category",
            "location_area",
            "status",
            "embedding_model",
            "embedding_dimensions",
        ],
    )
    op.create_check_constraint(
        "ck_item_records_category_item_type",
        "item_records",
        "(item_type = 'IDENTITY_DOCUMENT' AND "
        "public_category = 'IDENTITY_CARD') OR "
        "(item_type = 'OTHER' AND public_category IN "
        "('ELECTRONICS', 'CLOTHING', 'STATIONERY', 'OTHER_CATEGORY'))",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_item_records_category_item_type", "item_records", type_="check"
    )
    op.drop_index("ix_item_records_match_taxonomy", table_name="item_records")
    op.create_index(
        "ix_item_records_match_filter",
        "item_records",
        ["kind", "item_type", "status", "published_at"],
    )
    op.drop_column("item_records", "location_area")
    op.drop_column("item_records", "public_category")
    location_area.drop(op.get_bind(), checkfirst=False)
    public_category.drop(op.get_bind(), checkfirst=False)
