from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing common CRUD operations.
    """

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
    ) -> None:
        self.session = session
        self.model = model

    async def create(self, **kwargs: Any) -> ModelType:
        instance = self.model(**kwargs)

        self.session.add(instance)

        await self.session.flush()
        await self.session.refresh(instance)

        return instance

    async def get(self, id: UUID) -> ModelType | None:
        stmt = select(self.model).where(
            self.model.id == id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        stmt = (
            select(self.model)
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def update(
        self,
        instance: ModelType,
        **kwargs: Any,
    ) -> ModelType:
        for key, value in kwargs.items():
            setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)

        return instance

    async def delete(
        self,
        instance: ModelType,
    ) -> None:
        await self.session.delete(instance)

    async def delete_by_id(
        self,
        id: UUID,
    ) -> bool:
        stmt = (
            delete(self.model)
            .where(self.model.id == id)
        )

        result = await self.session.execute(stmt)

        return result.rowcount > 0

    async def exists(
        self,
        id: UUID,
    ) -> bool:
        return await self.get(id) is not None