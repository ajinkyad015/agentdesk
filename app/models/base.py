from datetime import  datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
# from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.types import UUIDPrimaryKey

from app.db.types import UUIDPrimaryKey
from app.db.types import UUIDPrimaryKey


class BaseModel(Base):
    """
    Base model inherited by all ORM models.
    """

    __abstract__ = True


    id: Mapped[UUID] = UUIDPrimaryKey



    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )