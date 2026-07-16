from sqlalchemy.types import UserDefinedType


class VectorType(UserDefinedType[list[float]]):
    """SQLAlchemy bridge for PostgreSQL pgvector values."""

    cache_ok = True

    def get_col_spec(self, **kwargs: object) -> str:
        return "vector"

    def bind_processor(self, dialect: object):
        def serialize(value: object) -> str | None:
            if value is None:
                return None
            if isinstance(value, str):
                return value
            return "[" + ",".join(str(float(part)) for part in value) + "]"

        return serialize

    def result_processor(self, dialect: object, coltype: object):
        def parse(value: object) -> list[float] | None:
            if value is None:
                return None
            if isinstance(value, list):
                return [float(part) for part in value]
            return [
                float(part)
                for part in str(value).strip("[]").split(",")
                if part
            ]

        return parse
