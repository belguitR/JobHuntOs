"""Explainable deterministic matching. The LLM never assigns a score."""

from __future__ import annotations

import re

from .profile import normalized_terms

ROLE_TERMS = ("software engineer", "backend", "platform", "infrastructure", "cloud", "sre")
SENIOR_TERMS = ("senior", "staff", "principal", "lead", "manager", "director", "architect")


def _contains(haystack: str, needle: str) -> bool:
    return needle in haystack.casefold()


def _experience_penalty(text: str) -> tuple[int, str | None]:
    if any(_contains(text, term) for term in SENIOR_TERMS):
        return -30, "senior-level title or requirement (-30)"
    years = [int(value) for value in re.findall(r"\b(\d+)\s*\+?\s*years?", text.casefold())]
    if years and min(years) >= 5:
        return -25, "5+ years requested (-25)"
    if years and min(years) >= 3:
        return -8, "3+ years requested (-8)"
    if years:
        return 15, "early-career experience range (+15)"
    return 8, "experience requirement not restrictive (+8)"


def score(job: dict, profile: dict) -> tuple[int, list[str]]:
    title = job["job_title"].casefold()
    text = f"{job['job_title']} {job['description']}".casefold()
    reasons: list[str] = []
    points = 0

    target_roles = normalized_terms(profile["target_roles"])
    role_matches = [term for term in target_roles if term in title]
    general_match = any(term in title for term in ROLE_TERMS)
    if role_matches:
        points += 20
        reasons.append(f"target role: {', '.join(sorted(role_matches))} (+20)")
    elif general_match:
        points += 14
        reasons.append("relevant engineering role (+14)")
    else:
        reasons.append("role is outside target categories (+0)")

    skills = normalized_terms(profile["skills"])
    matched_skills = sorted(skill for skill in skills if skill in text)
    skill_points = min(25, len(matched_skills) * 5)
    points += skill_points
    if matched_skills:
        reasons.append(f"skills: {', '.join(matched_skills)} (+{skill_points})")
    else:
        reasons.append("no saved skill keywords found (+0)")

    experience_points, experience_reason = _experience_penalty(text)
    points += experience_points
    reasons.append(experience_reason)

    location = f"{job['location']} {job['country']}".casefold()
    locations = normalized_terms(profile["target_locations"])
    countries = normalized_terms(profile["target_countries"])
    if any(term in location for term in locations | countries):
        points += 10
        reasons.append("target location (+10)")
    elif "remote" in location or "remote" in job["workplace_type"].casefold():
        points += 7
        reasons.append("remote role (+7)")

    language_text = f"{job['language_requirements']} {job['description']}".casefold()
    preferred_languages = normalized_terms(profile["preferred_languages"])
    if any(language in language_text for language in preferred_languages):
        points += 5
        reasons.append("preferred working language mentioned (+5)")

    salary = job["salary_text"].casefold()
    minimum = int(profile.get("minimum_salary_eur", 0) or 0)
    numeric_salary = [int(value.replace(",", "")) for value in re.findall(r"\b\d{2}[\d,]{3}\b", salary)]
    if numeric_salary and min(numeric_salary) >= minimum:
        points += 10
        reasons.append("salary meets configured floor (+10)")
    elif salary:
        reasons.append("salary listed but below/unclear against configured floor (+0)")

    if job["company_name"].casefold() in normalized_terms(profile["blocked_companies"]):
        points -= 100
        reasons.append("blocked company (-100)")

    return max(0, min(100, points)), reasons
