from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

UUIDPrimaryKey = mapped_column(
    PG_UUID(as_uuid=True),
    primary_key=True,
    default=uuid4,
)

UUIDForeignKey = lambda target, **kwargs: mapped_column(  # noqa: E731
    PG_UUID(as_uuid=True),
    target,
    **kwargs,
)