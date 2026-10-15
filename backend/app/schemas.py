from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    question: str = Field(min_length=12, max_length=500)
    scope: str | None = Field(default=None, max_length=1000)


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
    findings: list[Finding]
    themes: list[str]
    limitations: list[str]
    sources: list[Source]
