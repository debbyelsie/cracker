"""OpenAlex work search and bibliographic response mapping."""

import os
from datetime import date
from typing import Any

import httpx

from .schemas import (
    AcademicAuthor,
    AcademicSource,
    FullTextAvailability,
    SourceSearchResponse,
    normalize_doi,
    normalize_http_url,
    normalize_openalex_id,
    normalize_orcid,
)

OPENALEX_WORKS_URL = "https://api.openalex.org/works"
DEFAULT_TIMEOUT_SECONDS = 10.0


class OpenAlexError(Exception):
    """Base error for failed OpenAlex searches."""


class OpenAlexTimeoutError(OpenAlexError):
    pass


class OpenAlexRateLimitError(OpenAlexError):
    def __init__(self, retry_after: str | None = None):
        super().__init__("OpenAlex rate limit reached.")
        self.retry_after = retry_after


class OpenAlexProviderError(OpenAlexError):
    pass


class OpenAlexConfigurationError(OpenAlexError):
    pass


def _configured_timeout() -> float:
    raw = os.getenv("OPENALEX_TIMEOUT_SECONDS")
    if raw is None:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise OpenAlexConfigurationError("OPENALEX_TIMEOUT_SECONDS must be a positive number.") from exc
    if not 0 < timeout <= 120:
        raise OpenAlexConfigurationError("OPENALEX_TIMEOUT_SECONDS must be greater than 0 and at most 120.")
    return timeout


def _abstract_from_inverted_index(index: Any) -> str | None:
    if not isinstance(index, dict) or not index:
        return None
    positioned_words: dict[int, str] = {}
    try:
        for word, positions in index.items():
            if not isinstance(word, str) or not isinstance(positions, list):
                return None
            for position in positions:
                if isinstance(position, bool) or not isinstance(position, int) or position < 0:
                    return None
                if position in positioned_words and positioned_words[position] != word:
                    return None
                positioned_words[position] = word
    except (AttributeError, TypeError):
        return None
    if not positioned_words:
        return None
    return " ".join(positioned_words[position] for position in sorted(positioned_words))


def _normalize_doi(value: Any) -> str | None:
    return normalize_doi(value)


def _optional_string(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _publication_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _publication_year(value: Any, published_date: date | None) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and 1000 <= value <= 9999:
        return value
    return published_date.year if published_date else None


def _authors(authorships: Any) -> list[AcademicAuthor]:
    if not isinstance(authorships, list):
        return []
    authors: list[AcademicAuthor] = []
    for authorship in authorships:
        author = authorship.get("author") if isinstance(authorship, dict) else None
        if not isinstance(author, dict):
            continue
        authors.append(AcademicAuthor(
            name=_optional_string(author.get("display_name")),
            openalex_id=normalize_openalex_id(author.get("id"), "A"),
            orcid=normalize_orcid(author.get("orcid")),
        ))
    return authors


def _location_urls(work: dict[str, Any], field: str) -> list[str]:
    locations = work.get("locations")
    if not isinstance(locations, list):
        locations = []
    best = work.get("best_oa_location")
    if isinstance(best, dict):
        locations = [*locations, best]
    urls: list[str] = []
    for location in locations:
        if not isinstance(location, dict):
            continue
        url = normalize_http_url(location.get(field))
        if url and url not in urls:
            urls.append(url)
    return urls


def _map_work(work: Any) -> AcademicSource:
    if not isinstance(work, dict):
        raise OpenAlexProviderError("OpenAlex returned a malformed work record.")
    stable_id = normalize_openalex_id(work.get("id"), "W")
    if stable_id is None:
        raise OpenAlexProviderError("OpenAlex returned a work without a valid stable ID.")
    record_url = f"https://openalex.org/{stable_id}"
    published_date = _publication_date(work.get("publication_date"))
    doi = _normalize_doi(work.get("doi"))
    has_fulltext = work.get("has_fulltext")
    return AcademicSource(
        openalex_id=stable_id,
        record_url=record_url,
        title=_optional_string(work.get("title")) or _optional_string(work.get("display_name")),
        authors=_authors(work.get("authorships")),
        publication_date=published_date,
        publication_year=_publication_year(work.get("publication_year"), published_date),
        doi=doi,
        abstract=_abstract_from_inverted_index(work.get("abstract_inverted_index")),
        work_type=_optional_string(work.get("type")),
        landing_page_urls=_location_urls(work, "landing_page_url"),
        pdf_urls=_location_urls(work, "pdf_url"),
        full_text=FullTextAvailability(
            reported_by_openalex=has_fulltext if isinstance(has_fulltext, bool) else None,
            retrieved_by_cracker=False,
        ),
    )


def _merge_missing_fields(existing: AcademicSource, duplicate: AcademicSource) -> AcademicSource:
    """Keep the first stable record while filling only absent metadata from a DOI duplicate."""
    values = existing.model_dump()
    for key in ("title", "publication_date", "publication_year", "doi", "abstract", "work_type"):
        if values[key] is None:
            values[key] = getattr(duplicate, key)
    if not values["authors"]:
        values["authors"] = [author.model_dump() for author in duplicate.authors]
    if not values["landing_page_urls"]:
        values["landing_page_urls"] = duplicate.landing_page_urls
    if values["full_text"]["reported_by_openalex"] is None:
        values["full_text"]["reported_by_openalex"] = duplicate.full_text.reported_by_openalex
    return AcademicSource.model_validate(values)


def _deduplicate(sources: list[AcademicSource]) -> list[AcademicSource]:
    by_id: dict[str, AcademicSource] = {}
    doi_to_id: dict[str, str] = {}
    ordered_ids: list[str] = []
    for source in sources:
        existing_id = source.openalex_id if source.openalex_id in by_id else None
        doi_id = doi_to_id.get(source.doi) if source.doi else None
        # If ID and DOI point at different accumulated records, trust the exact
        # OpenAlex ID. Merging the groups would combine contradictory identities.
        target_id = existing_id or doi_id
        if target_id:
            by_id[target_id] = _merge_missing_fields(by_id[target_id], source)
            if source.doi:
                doi_to_id[source.doi] = target_id
            continue
        by_id[source.openalex_id] = source
        ordered_ids.append(source.openalex_id)
        if source.doi:
            doi_to_id[source.doi] = source.openalex_id
    return [by_id[source_id] for source_id in ordered_ids]


def _map_response(query: str, payload: Any) -> SourceSearchResponse:
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise OpenAlexProviderError("OpenAlex returned a malformed search response.")
    mapped = _deduplicate([_map_work(item) for item in payload["results"]])
    meta = payload.get("meta")
    count = meta.get("count") if isinstance(meta, dict) else None
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        count = None
    return SourceSearchResponse(
        query=query,
        status="results" if mapped else "empty",
        total_count=count,
        sources=mapped,
    )


def search_openalex_works(
    query: str,
    limit: int = 10,
    *,
    client: httpx.Client | None = None,
) -> SourceSearchResponse:
    """Fetch one bounded page of works. A client can be injected for offline tests."""
    timeout = _configured_timeout()
    owns_client = client is None
    if client is None:
        headers: dict[str, str] = {}
        api_key = os.getenv("OPENALEX_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        client = httpx.Client(timeout=httpx.Timeout(timeout), headers=headers)
    try:
        try:
            response = client.get(
                OPENALEX_WORKS_URL,
                params={
                    "search": query,
                    "per_page": limit,
                    "select": "id,title,display_name,authorships,publication_date,publication_year,doi,abstract_inverted_index,type,locations,best_oa_location,has_fulltext",
                },
            )
        except httpx.TimeoutException as exc:
            raise OpenAlexTimeoutError("OpenAlex request timed out.") from exc
        except httpx.RequestError as exc:
            raise OpenAlexProviderError("Could not connect to OpenAlex.") from exc

        if response.status_code == 429:
            raise OpenAlexRateLimitError(response.headers.get("Retry-After"))
        if not response.is_success:
            raise OpenAlexProviderError(f"OpenAlex returned HTTP {response.status_code}.")
        try:
            payload = response.json()
        except (ValueError, TypeError) as exc:
            raise OpenAlexProviderError("OpenAlex returned invalid JSON.") from exc
        return _map_response(query=query, payload=payload)
    finally:
        if owns_client:
            client.close()
