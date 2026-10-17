import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import main, openalex
from app.main import app
from app.schemas import (
    AcademicAuthor,
    AcademicSource,
    ResearchRequest,
    SourceSearchRequest,
    normalize_doi,
    normalize_http_url,
    normalize_openalex_id,
    normalize_orcid,
)

api_client = TestClient(app)


def work(**overrides):
    value = {
        "id": "https://openalex.org/W1234567890",
        "title": "Fixture title",
        "authorships": [{"author": {
            "id": "https://openalex.org/A1234567890",
            "display_name": "Fixture Author",
            "orcid": "https://orcid.org/0000-0000-0000-0000",
        }}],
        "publication_date": "2024-05-06",
        "publication_year": 2024,
        "doi": "https://doi.org/10.1234/Fixture.DOI",
        "abstract_inverted_index": {"last": [2], "First": [0], "word.": [1]},
        "type": "article",
        "locations": [{
            "landing_page_url": "https://example.test/paper",
            "pdf_url": "https://example.test/paper.pdf",
        }],
        "has_fulltext": True,
    }
    value.update(overrides)
    return value


def response(payload, status=200, headers=None):
    return httpx.Response(status, json=payload, headers=headers)


def test_maps_work_abstract_authors_urls_and_fulltext_integrity():
    def handler(request):
        assert request.url.params["search"] == "fixture topic"
        assert request.url.params["per_page"] == "7"
        assert "abstract_inverted_index" in request.url.params["select"]
        return response({"meta": {"count": 19}, "results": [work()]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as mocked:
        result = openalex.search_openalex_works("fixture topic", 7, client=mocked)

    source = result.sources[0]
    assert result.status == "results"
    assert result.total_count == 19
    assert source.openalex_id == "W1234567890"
    assert source.record_url == "https://openalex.org/W1234567890"
    assert source.abstract == "First word. last"
    assert source.authors[0].name == "Fixture Author"
    assert source.publication_date.isoformat() == "2024-05-06"
    assert source.publication_year == 2024
    assert source.doi == "10.1234/fixture.doi"
    assert source.landing_page_urls == ["https://example.test/paper"]
    assert source.pdf_urls == ["https://example.test/paper.pdf"]
    assert source.full_text.reported_by_openalex is True
    assert source.full_text.retrieved_by_cracker is False
    assert source.content_status == "bibliographic_metadata_only"


def test_missing_optional_metadata_stays_missing():
    minimal = {"id": "https://openalex.org/W1234567890"}
    with httpx.Client(
        transport=httpx.MockTransport(lambda _request: response({"results": [minimal]}))
    ) as mocked:
        result = openalex.search_openalex_works("fixture topic", client=mocked)
    source = result.sources[0]
    assert source.title is None
    assert source.authors == []
    assert source.publication_date is None
    assert source.publication_year is None
    assert source.doi is None
    assert source.abstract is None
    assert source.work_type is None
    assert source.landing_page_urls == []
    assert source.pdf_urls == []
    assert source.full_text.reported_by_openalex is None
    assert source.full_text.retrieved_by_cracker is False


def test_deduplicates_by_openalex_id_and_normalized_doi_not_title():
    same_id = work(authorships=[])
    same_doi = work(id="https://openalex.org/W2222222222", doi="10.1234/fixture.doi", title=None)
    similar_title_other_doi = work(
        id="https://openalex.org/W3333333333",
        doi="10.9999/other",
        title="Fixture title",
    )
    payload = {"results": [same_id, work(), same_doi, similar_title_other_doi]}
    with httpx.Client(
        transport=httpx.MockTransport(lambda _request: response(payload))
    ) as mocked:
        result = openalex.search_openalex_works("fixture topic", client=mocked)
    assert [source.openalex_id for source in result.sources] == ["W1234567890", "W3333333333"]
    assert result.sources[0].authors[0].name == "Fixture Author"


def test_overlapping_id_and_doi_matches_do_not_merge_conflicting_records():
    records = {
        "results": [
            work(id="https://openalex.org/W111", doi="10.1234/shared"),
            work(id="https://openalex.org/W222", doi="10.5678/other"),
            work(id="https://openalex.org/W222", doi="10.1234/shared"),
        ]
    }
    with httpx.Client(transport=httpx.MockTransport(lambda _request: response(records))) as mocked:
        result = openalex.search_openalex_works("fixture topic", client=mocked)
    # The incoming row links two different IDs. Keep both rather than guessing
    # that the conflicting DOI makes them the same work.
    assert [source.openalex_id for source in result.sources] == ["W111", "W222"]
    assert [source.doi for source in result.sources] == ["10.1234/shared", "10.5678/other"]


def test_identifier_and_url_normalizers_accept_expected_forms_and_reject_invalid_values():
    assert normalize_openalex_id("https://openalex.org/W12345", "W") == "W12345"
    assert normalize_openalex_id("A12345", "A") == "A12345"
    assert normalize_openalex_id("https://openalex.org.evil/W12345", "W") is None
    assert normalize_openalex_id("https://openalex.org/A12345", "W") is None

    assert normalize_orcid("0000-0002-1825-0097") == "https://orcid.org/0000-0002-1825-0097"
    assert normalize_orcid("https://orcid.org/0000-0002-1825-0097") == "https://orcid.org/0000-0002-1825-0097"
    assert normalize_orcid("0000-0002-1825-0098") is None
    assert normalize_orcid("https://orcid.org.evil/0000-0002-1825-0097") is None

    assert normalize_doi("10.1234/AbC") == "10.1234/abc"
    assert normalize_doi("https://doi.org/10.1234/AbC") == "10.1234/abc"
    assert normalize_doi("http://dx.doi.org/10.1234/AbC") == "10.1234/abc"
    assert normalize_doi("10.12/abc") is None
    assert normalize_doi("javascript:alert(1)") is None

    assert normalize_http_url("https://example.org/a%20b") == "https://example.org/a%20b"
    assert normalize_http_url("http://example.org/path") == "http://example.org/path"
    assert normalize_http_url("javascript:alert(1)") is None
    assert normalize_http_url("https://bad host/path") is None
    assert normalize_http_url("https://example.org/%ZZ") is None


def test_invalid_optional_provider_metadata_is_omitted_without_losing_source():
    malformed_optionals = work(
        doi="not-a-doi",
        authorships=[{"author": {
            "id": "https://openalex.org.evil/A12345",
            "display_name": "Author name remains available",
            "orcid": "0000-0002-1825-0098",
        }}],
        locations=[{
            "landing_page_url": "javascript:alert(1)",
            "pdf_url": "https://bad host/file.pdf",
        }],
    )
    with httpx.Client(
        transport=httpx.MockTransport(lambda _request: response({"results": [malformed_optionals]}))
    ) as mocked:
        result = openalex.search_openalex_works("fixture topic", client=mocked)
    assert len(result.sources) == 1
    source = result.sources[0]
    assert source.doi is None
    assert source.authors[0].name == "Author name remains available"
    assert source.authors[0].openalex_id is None
    assert source.authors[0].orcid is None
    assert source.landing_page_urls == []
    assert source.pdf_urls == []


def test_source_schema_rejects_invalid_ids_urls_and_dois():
    with pytest.raises(ValidationError):
        AcademicAuthor(openalex_id="https://openalex.org.evil/A12345")
    with pytest.raises(ValidationError):
        AcademicAuthor(orcid="0000-0002-1825-0098")

    mapped = openalex._map_work(work())
    values = mapped.model_dump()
    values["landing_page_urls"] = ["javascript:alert(1)"]
    with pytest.raises(ValidationError):
        AcademicSource.model_validate(values)
    values = mapped.model_dump()
    values["doi"] = "not-a-doi"
    with pytest.raises(ValidationError):
        AcademicSource.model_validate(values)


def test_empty_results_are_distinct_from_provider_failure():
    with httpx.Client(
        transport=httpx.MockTransport(lambda _request: response({"meta": {"count": 0}, "results": []}))
    ) as mocked:
        result = openalex.search_openalex_works("fixture topic", client=mocked)
    assert result.status == "empty"
    assert result.sources == []
    assert result.total_count == 0


def test_timeout_is_reported():
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as mocked:
        with pytest.raises(openalex.OpenAlexTimeoutError):
            openalex.search_openalex_works("fixture topic", client=mocked)


def test_rate_limit_and_retry_after_are_reported():
    with httpx.Client(
        transport=httpx.MockTransport(lambda _request: response({}, 429, {"Retry-After": "3"}))
    ) as mocked:
        with pytest.raises(openalex.OpenAlexRateLimitError) as error:
            openalex.search_openalex_works("fixture topic", client=mocked)
    assert error.value.retry_after == "3"


def test_other_http_error_and_malformed_payloads_are_reported():
    for returned, expected in [
        (httpx.Response(503, text="unavailable"), "HTTP 503"),
        (httpx.Response(200, text="not json"), "invalid JSON"),
        (response({"unexpected": []}), "malformed search response"),
        (response({"results": [{"title": "no ID"}]}), "valid stable ID"),
    ]:
        with httpx.Client(
            transport=httpx.MockTransport(lambda _request, item=returned: item)
        ) as mocked:
            with pytest.raises(openalex.OpenAlexProviderError, match=expected):
                openalex.search_openalex_works("fixture topic", client=mocked)


def test_source_search_request_validation():
    assert SourceSearchRequest(query="  AI adoption  ").query == "AI adoption"
    with pytest.raises(ValidationError):
        SourceSearchRequest(query="  ")
    with pytest.raises(ValidationError):
        SourceSearchRequest(query="AI")
    with pytest.raises(ValidationError):
        SourceSearchRequest(query="valid query", limit=26)


def test_timeout_and_optional_api_key_configuration(monkeypatch):
    monkeypatch.setenv("OPENALEX_TIMEOUT_SECONDS", "4.5")
    monkeypatch.setenv("OPENALEX_API_KEY", "test-key")
    observed = {}
    real_client = httpx.Client

    def mocked_client(**kwargs):
        observed.update(kwargs)
        return real_client(
            transport=httpx.MockTransport(lambda _request: response({"results": []})),
            **kwargs,
        )

    monkeypatch.setattr(openalex.httpx, "Client", mocked_client)
    openalex.search_openalex_works("fixture topic")
    assert observed["headers"]["Authorization"] == "Bearer test-key"
    assert observed["timeout"].read == 4.5

    monkeypatch.setenv("OPENALEX_TIMEOUT_SECONDS", "not-a-number")
    with pytest.raises(openalex.OpenAlexConfigurationError):
        openalex.search_openalex_works("fixture topic")


def test_source_search_route_handles_provider_states(monkeypatch):
    def empty_result(query, limit):
        return openalex._map_response(query, {"meta": {"count": 0}, "results": []})

    monkeypatch.setattr(main, "search_openalex_works", empty_result)
    empty = main.research_sources(SourceSearchRequest(query="What affects adoption?"))
    assert empty.status == "empty"
    assert empty.sources == []

    def timeout(_query, _limit):
        raise openalex.OpenAlexTimeoutError("OpenAlex request timed out.")

    monkeypatch.setattr(main, "search_openalex_works", timeout)
    with pytest.raises(HTTPException) as timeout_error:
        main.research_sources(SourceSearchRequest(query="What affects adoption?"))
    assert timeout_error.value.status_code == 504

    def rate_limited(_query, _limit):
        raise openalex.OpenAlexRateLimitError("4")

    monkeypatch.setattr(main, "search_openalex_works", rate_limited)
    with pytest.raises(HTTPException) as rate_error:
        main.research_sources(SourceSearchRequest(query="What affects adoption?"))
    assert rate_error.value.status_code == 429
    assert rate_error.value.headers["Retry-After"] == "4"


def test_existing_research_contract_remains_simulated_and_unchanged():
    result = main.research(ResearchRequest(question="What affects small business AI adoption?"))
    brief = result.model_dump()
    assert set(brief) == {
        "id", "question", "scope", "status", "summary", "detailed_answer",
        "investigation_plan", "clarifications", "findings", "themes", "limitations", "sources",
    }
    assert brief["status"] == "simulated"
    assert len(brief["findings"]) == 3
    assert all("fictional" in item["status"].lower() for item in brief["sources"])


def test_source_search_http_endpoint_validation_and_provider_errors(monkeypatch):
    def empty_result(query, _limit):
        return openalex._map_response(query, {"meta": {"count": 0}, "results": []})

    monkeypatch.setattr(main, "search_openalex_works", empty_result)
    empty = api_client.post("/api/research/sources", json={"query": "  AI adoption  "})
    assert empty.status_code == 200
    assert empty.json()["query"] == "AI adoption"
    assert empty.json()["status"] == "empty"
    assert api_client.post("/api/research/sources", json={"query": "  "}).status_code == 422
    assert api_client.post("/api/research/sources", json={"query": "AI"}).status_code == 422
    assert api_client.post("/api/research/sources", json={"query": "valid query", "limit": 26}).status_code == 422

    def fail_with_rate_limit(_query, _limit):
        raise openalex.OpenAlexRateLimitError("5")

    monkeypatch.setattr(main, "search_openalex_works", fail_with_rate_limit)
    rate_limited = api_client.post("/api/research/sources", json={"query": "AI adoption"})
    assert rate_limited.status_code == 429
    assert rate_limited.headers["retry-after"] == "5"

