# pyrefly: ignore[missing-import]
from pydantic import BaseModel, Field, field_validator


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
