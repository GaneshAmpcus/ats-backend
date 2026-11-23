import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    BigInteger,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    CheckConstraint,
    Index,
    text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CustomFieldDefinition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "custom_field_definitions"

    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    field_label: Mapped[str] = mapped_column(String(150), nullable=False)
    field_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    options: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    business_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True,
        comment="Optional tenant scope; NULL means shared across business units",
    )

    __table_args__ = (
        Index("uq_custom_field_definitions_entity_field_key", "entity_type", "field_key", unique=True),
    )


class CustomFieldValue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "custom_field_values"

    definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("custom_field_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Applicants use BIGINT identities. Other entities currently use UUID keys.
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    entity_id_bigint: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_number: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    value_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    value_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "(entity_id IS NOT NULL AND entity_id_bigint IS NULL) OR "
            "(entity_id IS NULL AND entity_id_bigint IS NOT NULL)",
            name="ck_custom_field_values_one_entity_id",
        ),
        Index(
            "uq_custom_field_values_definition_entity_uuid", "definition_id", "entity_id",
            unique=True, postgresql_where=text("entity_id IS NOT NULL"),
            sqlite_where=text("entity_id IS NOT NULL"),
        ),
        Index(
            "uq_custom_field_values_definition_entity_bigint", "definition_id", "entity_id_bigint",
            unique=True, postgresql_where=text("entity_id_bigint IS NOT NULL"),
            sqlite_where=text("entity_id_bigint IS NOT NULL"),
        ),
    )
