# pyrefly: ignore[missing-import]
from datetime import date
import re
from typing import Literal
from urllib.parse import unquote, urlsplit

from pydantic import BaseModel, Field, ValidationInfo, field_validator


_DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")
_ORCID_PATTERN = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", re.IGNORECASE)


def normalize_openalex_id(value: object, entity_prefix: str) -> str | None:
    """Accept canonical OpenAlex URLs or bare IDs and return the compact ID."""
    if not isinstance(value, str):
        return None
    identifier = value.strip()
    if not identifier:
        return None
    if "://" in identifier:
        try:
            parsed = urlsplit(identifier)
            if (
                parsed.scheme.lower() not in {"http", "https"}
                or parsed.hostname != "openalex.org"
                or parsed.username is not None
                or parsed.password is not None
                or parsed.port is not None
                or parsed.query
                or parsed.fragment
            ):
                return None
        except ValueError:
            return None
        if not parsed.path.startswith("/") or parsed.path.startswith("//"):
            return None
        identifier = parsed.path[1:]
    if not re.fullmatch(rf"{re.escape(entity_prefix)}\d+", identifier, re.IGNORECASE):
        return None
    return f"{entity_prefix.upper()}{identifier[1:]}"


def normalize_doi(value: object) -> str | None:
    """Normalize OpenAlex DOI short forms and doi.org URLs for comparison."""
    if not isinstance(value, str):
        return None
    doi = value.strip()
    if doi.lower().startswith("doi:"):
        doi = doi[4:].strip()
    elif "://" in doi:
        try:
            parsed = urlsplit(doi)
            if (
                parsed.scheme.lower() not in {"http", "https"}
                or parsed.hostname not in {"doi.org", "dx.doi.org"}
                or parsed.username is not None
                or parsed.password is not None
                or parsed.port is not None
                or parsed.query
                or parsed.fragment
            ):
                return None
        except ValueError:
            return None
        if not parsed.path.startswith("/") or parsed.path.startswith("//"):
            return None
        doi = unquote(parsed.path[1:])
    if not _DOI_PATTERN.fullmatch(doi):
        return None
    return doi.casefold()


def normalize_orcid(value: object) -> str | None:
    """Validate an ORCID checksum and return its canonical HTTPS URI."""
    if not isinstance(value, str):
        return None
    identifier = value.strip()
    if "://" in identifier:
        try:
            parsed = urlsplit(identifier)
            if (
                parsed.scheme.lower() not in {"http", "https"}
                or parsed.hostname != "orcid.org"
                or parsed.username is not None
                or parsed.password is not None
                or parsed.port is not None
                or parsed.query
                or parsed.fragment
            ):
                return None
        except ValueError:
            return None
        if not parsed.path.startswith("/") or parsed.path.startswith("//"):
            return None
        identifier = parsed.path[1:]
    if not _ORCID_PATTERN.fullmatch(identifier):
        return None
    compact = identifier.replace("-", "").upper()
    checksum = 0
    for digit in compact[:15]:
        checksum = (checksum + int(digit)) * 2
    check_digit = (12 - checksum % 11) % 11
    expected = "X" if check_digit == 10 else str(check_digit)
    if compact[-1] != expected:
        return None
    grouped = f"{compact[:4]}-{compact[4:8]}-{compact[8:12]}-{compact[12:]}"
    return f"https://orcid.org/{grouped}"


def normalize_http_url(value: object) -> str | None:
    """Accept absolute HTTP(S) URLs without whitespace or malformed escapes."""
    if not isinstance(value, str):
        return None
    url = value.strip()
    if not url or any(char.isspace() or ord(char) < 32 for char in url):
        return None
    if re.search(r"%(?![0-9A-Fa-f]{2})", url):
        return None
    try:
        parsed = urlsplit(url)
        _ = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.netloc
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.netloc.endswith(":")
    ):
        return None
    return url


class ResearchRequest(BaseModel):
    question: str = Field(min_length=12, max_length=500)
    scope: str | None = Field(default=None, max_length=1000)
    clarifications: dict[str, str] = Field(default_factory=dict)

    @field_validator("question", mode="before")
    @classmethod
    def trim_question(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("scope", mode="before")
    @classmethod
    def normalize_scope(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class ClarifyingQuestion(BaseModel):
    id: str
    prompt: str
    hint: str


class ResearchIntake(BaseModel):
    question: str
    interpretation: str
    questions: list[ClarifyingQuestion]
    investigation_plan: list[str]
    notice: str


class Evidence(BaseModel):
    excerpt: str
    source_title: str
    note: str


class Source(BaseModel):
    id: str
    title: str
    kind: str
    status: str


class Finding(BaseModel):
    id: str
    title: str
    summary: str
    theme: str
    evidence: list[Evidence]


class ResearchBrief(BaseModel):
    id: str
    question: str
    scope: str | None
    status: str
    summary: str
    detailed_answer: str
    investigation_plan: list[str]
    clarifications: dict[str, str]
    findings: list[Finding]
    themes: list[str]
    limitations: list[str]
    sources: list[Source]


class SourceSearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    limit: int = Field(default=10, ge=1, le=25)

    @field_validator("query", mode="before")
    @classmethod
    def trim_query(cls, value):
        return value.strip() if isinstance(value, str) else value


class AcademicAuthor(BaseModel):
    name: str | None = None
    openalex_id: str | None = None
    orcid: str | None = None

    @field_validator("openalex_id")
    @classmethod
    def validate_openalex_author_id(cls, value):
        if value is None:
            return None
        normalized = normalize_openalex_id(value, "A")
        if normalized is None:
            raise ValueError("Invalid OpenAlex author ID")
        return normalized

    @field_validator("orcid")
    @classmethod
    def validate_orcid(cls, value):
        if value is None:
            return None
        normalized = normalize_orcid(value)
        if normalized is None:
            raise ValueError("Invalid ORCID")
        return normalized


class FullTextAvailability(BaseModel):
    reported_by_openalex: bool | None
    retrieved_by_cracker: Literal[False] = False


class AcademicSource(BaseModel):
    openalex_id: str
    record_url: str
    title: str | None
    authors: list[AcademicAuthor]
    publication_date: date | None
    publication_year: int | None
    doi: str | None
    abstract: str | None
    work_type: str | None
    landing_page_urls: list[str]
    pdf_urls: list[str] = Field(default_factory=list)
    full_text: FullTextAvailability
    metadata_source: Literal["OpenAlex"] = "OpenAlex"
    content_status: Literal["bibliographic_metadata_only"] = "bibliographic_metadata_only"

    @field_validator("openalex_id")
    @classmethod
    def validate_work_id(cls, value):
        normalized = normalize_openalex_id(value, "W")
        if normalized is None:
            raise ValueError("Invalid OpenAlex work ID")
        return normalized

    @field_validator("record_url")
    @classmethod
    def validate_record_url(cls, value, info: ValidationInfo):
        normalized = normalize_http_url(value)
        expected = f"https://openalex.org/{info.data.get('openalex_id')}"
        if normalized != expected:
            raise ValueError("Record URL must be the canonical URL for the validated OpenAlex work ID")
        return normalized

    @field_validator("doi")
    @classmethod
    def validate_doi(cls, value):
        if value is None:
            return None
        normalized = normalize_doi(value)
        if normalized is None:
            raise ValueError("Invalid DOI")
        return normalized

    @field_validator("landing_page_urls", "pdf_urls")
    @classmethod
    def validate_external_urls(cls, values):
        validated = []
        for value in values:
            normalized = normalize_http_url(value)
            if normalized is None:
                raise ValueError("External source URLs must use HTTP or HTTPS")
            validated.append(normalized)
        return validated


class SourceSearchResponse(BaseModel):
    provider: Literal["OpenAlex"] = "OpenAlex"
    query: str
    status: Literal["results", "empty"]
    total_count: int | None
    sources: list[AcademicSource]
