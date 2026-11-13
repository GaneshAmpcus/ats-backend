"""Deterministic post-processing of the LLM resume extraction result.

The LLM is good at reading text but unreliable at arithmetic and at knowing today's
date, so derived values such as total experience are computed here from the dates it
extracted. Everything in this module is best-effort and never raises on odd input.
"""

import re
from datetime import date

from app.parsing.schemas import ExperienceItem, ResumeParseResult

_DATE_RE = re.compile(r"^\s*(\d{4})(?:-(\d{1,2}))?\s*$")
_PRESENT_WORDS = {"present", "current", "now", "ongoing", "till date", "to date", "today"}
_INTERN_RE = re.compile(r"\b(intern|internship|trainee|apprentice)\b", re.IGNORECASE)


def _is_present(value: str | None) -> bool:
    return bool(value) and value.strip().lower() in _PRESENT_WORDS


def _parse_start(value: str | None) -> date | None:
    match = _DATE_RE.match(value or "")
    if not match:
        return None
    month = int(match.group(2)) if match.group(2) else 1
    if not 1 <= month <= 12:
        return None
    return date(int(match.group(1)), month, 1)


def _parse_end(value: str | None) -> date | None:
    """End of a period, exclusive: a month-dated end covers that whole month."""
    match = _DATE_RE.match(value or "")
    if not match:
        return None
    year = int(match.group(1))
    if not match.group(2):
        return date(year, 1, 1)  # year-only dates count from the start of the year
    month = int(match.group(2))
    if not 1 <= month <= 12:
        return None
    return date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)


def _periods(items: list[ExperienceItem], today: date) -> list[tuple[date, date]]:
    periods: list[tuple[date, date]] = []
    for item in items:
        start = _parse_start(item.start_date)
        if start is None:
            continue
        end = today if (item.is_current or _is_present(item.end_date)) else _parse_end(item.end_date)
        if end is None or end <= start:
            continue
        periods.append((start, end))
    return periods


def compute_total_experience_years(
    experience: list[ExperienceItem], today: date
) -> float | None:
    """Years of experience from dated roles, merging overlaps.

    Internships are left out unless they are the only dated roles.
    Returns None when no role has usable dates.
    """
    regular = [item for item in experience if not _INTERN_RE.search(item.title or "")]
    periods = sorted(_periods(regular, today) or _periods(experience, today))
    if not periods:
        return None

    merged: list[list[date]] = []
    for start, end in periods:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    days = sum((end - start).days for start, end in merged)
    return round(days / 365.25, 1)


def normalize_result(result: ResumeParseResult, today: date) -> ResumeParseResult:
    """Clean up the model output in place and return it."""
    seen: set[str] = set()
    skills: list[str] = []
    for skill in result.skills:
        skill = " ".join(skill.split())
        key = skill.casefold()
        if skill and key not in seen:
            seen.add(key)
            skills.append(skill)
    result.skills = skills

    for item in result.experience:
        if _is_present(item.end_date):
            item.end_date = None
            item.is_current = True

    computed = compute_total_experience_years(result.experience, today)
    if computed is not None:
        result.total_experience_years = computed

    return result
