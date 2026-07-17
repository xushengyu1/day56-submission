import asyncio

from app.database import session_factory
from app.matching.embedding_factory import build_embedding_adapter
from app.matching.reembed import reembed_published_records


async def main() -> None:
    adapter = build_embedding_adapter()
    async with session_factory() as session:
        async with session.begin():
            count = await reembed_published_records(session, adapter)
    print(f"reembedded={count}")


if __name__ == "__main__":
    asyncio.run(main())
