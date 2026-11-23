"""Advanced-search history: recent and saved searches (Table 30)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Index, String, Text, Uuid, false, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB(), "postgresql")


class ApplicantSearchHistory(BigIntPrimaryKeyMixin, Base):
    """A recent or saved advanced applicant search (``applicant_search_history``).

    ``search_name`` is used only for saved searches. ``advanced_options_json``
    holds advanced options whose structure was not captured in the source
    schema (tentative).
    """

    __tablename__ = "applicant_search_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        comment="FK to users - to be added when master exists",
    )
    search_source: Mapped[str] = mapped_column(String(20), nullable=False)
    history_type: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="RECENT or SAVED"
    )
    search_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    keywords: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    exclude_keywords: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    job_title: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment='Supports quoted phrases, e.g. "Java Developer"'
    )
    recent_job_title_only: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    location_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="FK to countries - to be added when master exists",
    )
    state_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="FK to states - to be added when master exists",
    )
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    include_without_country: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    advanced_options_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONType, nullable=True
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    __table_args__ = (
        Index("ix_applicant_search_history_user_id_history_type", "user_id", "history_type"),
    )
