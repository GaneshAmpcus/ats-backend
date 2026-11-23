"""Applicant group (Table 15, parent table only).

The child ``applicant_group_members`` table (bulk "Add to Group") is not part of
this delivery; its column definitions are still pending.
"""

import uuid

from sqlalchemy import Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntPrimaryKeyMixin


class ApplicantGroup(BigIntPrimaryKeyMixin, Base):
    """A named group of applicants (``applicant_groups``).

    ``applicants.applicant_group_id`` points here (single group on the form).
    """

    __tablename__ = "applicant_groups"

    business_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="FK to business_units - to be added when master exists",
    )
    group_name: Mapped[str] = mapped_column(String(150), nullable=False)

    __table_args__ = (Index("ix_applicant_groups_business_unit_id", "business_unit_id"),)
