"""Core applicant model (Table 01 of the Applicant tentative schema)."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    Uuid,
    false,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    BigIntType,
    SoftDeleteMixin,
    TimestampMixin,
)
from app.modules.applicants.enums import CreationMethod
from app.modules.applicants.security import EncryptedIdentityNumber

if TYPE_CHECKING:
    from app.modules.applicants.models.skill import ApplicantSkill


def _master_ref(table: str, *, nullable: bool = True) -> Mapped[uuid.UUID | None]:
    """Plain UUID column standing in for a FK to a master table that does not exist yet.

    Follows the jobs module pattern: the ForeignKey is added once the master exists.
    """
    return mapped_column(
        Uuid,
        nullable=nullable,
        comment=f"FK to {table} - to be added when master exists",
    )


class Applicant(BigIntPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A candidate/applicant record (``applicants``).

    The ``id`` is a BIGINT identity (see ``BigIntPrimaryKeyMixin``); it is the
    applicant number shown in lists and snapshots.

    Notes:
        * Age is never stored; it is computed from ``date_of_birth``.
        * ``email`` is deliberately NOT unique: the import flow offers
          Skip / Overwrite / Add New Record, so duplicates are checked in
          application logic using the ``(business_unit_id, lower(email))`` index.
        * ``city`` is mandatory only on the manual Add Applicant form; the
          database allows NULL because imported and resume-parsed applicants can
          have a blank city. Enforce on the manual form in schema validation.
        * ``country_id``, ``applicant_status_id`` and ``owner_user_id`` have
          business defaults (India, New lead, current user) that must be applied
          by the service layer; they cannot be database defaults while the
          master tables do not exist.
        * ``pan_number``, ``aadhaar_number`` and ``passport_number`` are
          sensitive and stored encrypted. The encryption helper is not yet
          implemented (see ``app.modules.applicants.security``).
        * Master references are plain UUID columns until the master tables exist.
    """

    __tablename__ = "applicants"

    # Identity & system
    business_unit_id: Mapped[uuid.UUID] = _master_ref("business_units", nullable=False)
    salutation: Mapped[str | None] = mapped_column(String(10), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(
        String(310),
        Computed(
            "first_name || COALESCE(' ' || middle_name, '') || ' ' || last_name",
            persisted=True,
        ),
        comment="Generated: first + middle + last. Maintained by the database.",
    )
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    maiden_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    profile_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    # Contact
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    alternate_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mobile_number: Mapped[str] = mapped_column(String(25), nullable=False)
    mobile_number_e164: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Normalised E.164 copy of mobile_number for duplicate detection and SMS",
    )
    home_phone: Mapped[str | None] = mapped_column(String(25), nullable=True)
    work_phone: Mapped[str | None] = mapped_column(String(25), nullable=True)
    other_phone: Mapped[str | None] = mapped_column(String(25), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    twitter_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_reference_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Location & authorization
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    country_id: Mapped[uuid.UUID | None] = _master_ref("countries")
    state_id: Mapped[uuid.UUID | None] = _master_ref("states")
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    work_authorization_id: Mapped[uuid.UUID | None] = _master_ref("work_authorizations")
    relocation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    # Source & ownership
    source_id: Mapped[uuid.UUID] = _master_ref("applicant_sources", nullable=False)
    referred_by: Mapped[str | None] = mapped_column(String(150), nullable=True)
    applicant_status_id: Mapped[uuid.UUID] = _master_ref(
        "applicant_statuses", nullable=False
    )
    applicant_group_id: Mapped[int | None] = mapped_column(
        BigIntType, ForeignKey("applicant_groups.id"), nullable=True
    )
    owner_user_id: Mapped[uuid.UUID | None] = _master_ref("users")

    # Profession
    current_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    current_company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    experience_years: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    experience_months: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    relevant_experience: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_ctc_currency: Mapped[str | None] = mapped_column(
        String(3), nullable=True, default="INR", server_default="INR"
    )
    current_ctc_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    current_ctc_period: Mapped[str | None] = mapped_column(String(15), nullable=True)
    expected_ctc_currency: Mapped[str | None] = mapped_column(
        String(3), nullable=True, default="INR", server_default="INR"
    )
    expected_ctc_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    expected_ctc_period: Mapped[str | None] = mapped_column(String(15), nullable=True)
    notice_period_id: Mapped[uuid.UUID | None] = _master_ref("notice_periods")
    preferred_shift_id: Mapped[uuid.UUID | None] = _master_ref("preferred_shifts")
    industry_id: Mapped[uuid.UUID | None] = _master_ref("industries")
    technology: Mapped[str | None] = mapped_column(String(255), nullable=True)
    applicant_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Legacy reference. The value 0 is treated as empty.",
    )

    # Identity documents (SENSITIVE - encrypted; helper implementation pending)
    pan_number: Mapped[str | None] = mapped_column(
        EncryptedIdentityNumber(), nullable=True, comment="Encrypted. Format AAAAA9999A."
    )
    aadhaar_number: Mapped[str | None] = mapped_column(
        EncryptedIdentityNumber(), nullable=True, comment="Encrypted. 12 digits."
    )
    passport_number: Mapped[str | None] = mapped_column(
        EncryptedIdentityNumber(), nullable=True, comment="Encrypted. Max 20 chars."
    )
    marital_status_id: Mapped[uuid.UUID | None] = _master_ref("marital_statuses")
    nationality_id: Mapped[uuid.UUID | None] = _master_ref("nationalities")

    # EEO details
    gender_id: Mapped[uuid.UUID | None] = _master_ref("eeo_genders")
    race_ethnicity_id: Mapped[uuid.UUID | None] = _master_ref("eeo_races")
    veteran_status_id: Mapped[uuid.UUID | None] = _master_ref("eeo_veteran_statuses")
    disability_id: Mapped[uuid.UUID | None] = _master_ref("eeo_disabilities")

    # Flags & audit
    is_email_merge_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    is_portal_account_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    creation_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CreationMethod.MANUAL.value,
        server_default=CreationMethod.MANUAL.value,
    )
    is_sms_blocked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    gdpr_consent_approved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    gdpr_consent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Audit fields. Plain UUID columns, no ForeignKey (same as jobs).
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    modified_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    skills: Mapped[list["ApplicantSkill"]] = relationship(
        "ApplicantSkill", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint(
            "experience_years IS NULL OR experience_years BETWEEN 0 AND 60",
            name="ck_applicants_experience_years_range",
        ),
        CheckConstraint(
            "experience_months IS NULL OR experience_months BETWEEN 0 AND 11",
            name="ck_applicants_experience_months_range",
        ),
        # Duplicate-check key (case-insensitive). Not UNIQUE by design.
        Index(
            "ix_applicants_business_unit_id_email_lower",
            "business_unit_id",
            text("lower(email)"),
        ),
        Index("ix_applicants_mobile_number_e164", "mobile_number_e164"),
        Index("ix_applicants_full_name", "full_name"),
        # Contains-search on names. Requires the pg_trgm extension.
        Index(
            "ix_applicants_full_name_trgm",
            "full_name",
            postgresql_using="gin",
            postgresql_ops={"full_name": "gin_trgm_ops"},
        ).ddl_if(dialect="postgresql"),
        # Keyset-paginated list screen, skipping soft-deleted rows.
        Index(
            "ix_applicants_business_unit_id_created_at_active",
            "business_unit_id",
            text("created_at DESC"),
            "id",
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index("ix_applicants_owner_user_id", "owner_user_id"),
        Index("ix_applicants_applicant_status_id", "applicant_status_id"),
        Index("ix_applicants_applicant_group_id", "applicant_group_id"),
    )
