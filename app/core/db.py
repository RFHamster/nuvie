from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator


async_engine = create_async_engine(
    settings.sqlalchemy_db_uri, echo=False, future=True
)

async_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Gera uma sessão assíncrona para usar com Depends em APIs ou em outras funções."""
    async with async_session() as session:
        yield session
