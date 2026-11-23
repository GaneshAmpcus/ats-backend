"""Enumerations for the applicants module.

Values are stored as plain strings (``String`` columns), following the jobs
module convention (``JobStatus`` etc.), and use UPPER_SNAKE_CASE. The source
schema document lists the same values in display form (e.g. ``ParseResume``).
"""

import enum


class CreationMethod(str, enum.Enum):
    """How an applicant record was created (``applicants.creation_method``)."""

    MANUAL = "MANUAL"
    PARSE_RESUME = "PARSE_RESUME"
    DROPBOX = "DROPBOX"
    BOX = "BOX"
    ONEDRIVE = "ONEDRIVE"
    BULK_PARSE = "BULK_PARSE"
    IMPORT = "IMPORT"
    CAREER_PORTAL = "CAREER_PORTAL"


class EmailType(str, enum.Enum):
    """Kind of email sent to an applicant (``applicant_emails.email_type``)."""

    GENERAL = "GENERAL"
    SHARE_JOB = "SHARE_JOB"
    SURVEY = "SURVEY"
    MACRO = "MACRO"


class SearchHistoryType(str, enum.Enum):
    """Advanced-search entry kind (``applicant_search_history.history_type``)."""

    RECENT = "RECENT"
    SAVED = "SAVED"
