from uuid import uuid4
from .schemas import (
    ClarifyingQuestion,
    Evidence,
    Finding,
    ResearchBrief,
    ResearchIntake,
    ResearchRequest,
    Source,
)


def prepare_research_intake(question: str, scope: str | None = None) -> ResearchIntake:
    """Reflect the question and ask for useful scope before the demo investigation."""
    cleaned_question = question.strip()
    interpretation = f"I understand that you want to investigate: “{cleaned_question}”"
    if scope:
        interpretation += f" I’ll also keep this context in view: “{scope}”"
    return ResearchIntake(
        question=cleaned_question,
        interpretation=interpretation,
        questions=[
            ClarifyingQuestion(
                id="audience",
                prompt="Who should this research help, and what decision should it support?",
                hint="For example: a small-business owner deciding whether to adopt a tool.",
            ),
            ClarifyingQuestion(
                id="focus",
                prompt="Which part of the question matters most to you?",
                hint="For example: costs, access, staff readiness, risks, or business outcomes.",
            ),
            ClarifyingQuestion(
                id="boundaries",
                prompt="Are there boundaries or source preferences I should respect?",
                hint="For example: a country, industry, time period, or preferred source type.",
            ),
        ],
        investigation_plan=[
            "Break the question into smaller research subquestions.",
            "Compare themes and disagreements across relevant sources.",
            "Connect each conclusion to inspectable evidence and state its limits.",
        ],
        notice=(
            "This first version uses a fixed demonstration workflow. It does not use an AI model "
            "or search real sources; your answers help show how an investigator would scope the work."
        ),
    )


def run_demo_research(request: ResearchRequest) -> ResearchBrief:
    """Return explicitly fictional demonstration material for the research workflow."""
    source_names = ["Illustrative interview notes (demonstration)", "Sample sector overview (demonstration)", "Example policy extract (demonstration)"]
    sources = [Source(id=f"demo-{i + 1}", title=name, kind="Demonstration source", status="Fictional sample — not a real publication") for i, name in enumerate(source_names)]
    findings = [
        Finding(id="f1", title="Practical value shapes early interest", summary="In this illustrative scenario, owners respond to clear time savings and a visible fit with everyday work.", theme="Perceived usefulness", evidence=[Evidence(excerpt="Example passage: ‘If it gives our team an hour back each day, we will try it.’", source_title=source_names[0], note="Fictional interview excerpt created for this demo.")]),
        Finding(id="f2", title="Confidence and support affect adoption", summary="The sample materials suggest that confidence, training, and access to ongoing help can influence whether a trial becomes routine.", theme="Capability and support", evidence=[Evidence(excerpt="Example passage: ‘We need someone to show us how to use it safely.’", source_title=source_names[1], note="Fictional sample text; no real study is represented.")]),
        Finding(id="f3", title="Trust and cost remain open questions", summary="Concerns about data handling, affordability, and reliable connectivity could shape decisions across different business contexts.", theme="Trust and access", evidence=[Evidence(excerpt="Example passage: ‘The monthly cost and where the data goes both matter.’", source_title=source_names[2], note="Fictional policy-style extract created for this demo.")]),
    ]
    return ResearchBrief(
        id=str(uuid4()),
        question=request.question.strip(),
        scope=request.scope,
        status="simulated",
        summary=(
            "This is a workflow demonstration, not a real literature search. The sample findings "
            "below are fictional and should not be used as research evidence."
        ),
        detailed_answer=(
            "This demo shows how a researcher could turn several evidence strands into a synthesis: "
            "compare potential benefits, practical capability and support, and trust or access "
            "constraints, then examine how they might interact. The illustrative examples in this "
            "response are fictional and are not evidence about your specific question: “"
            f"{request.question.strip()}”. They cannot establish what is true for the population "
            "you have in mind. Answering that requires finding and assessing real sources."
        ),
        investigation_plan=[
            "Clarify the population, location, timeframe, and meaning of adoption.",
            "Look for evidence about expected value, capability and support, and trust and access.",
            "Compare findings across sources and check where context or results disagree.",
            "Trace each claim to evidence and describe uncertainty and research gaps.",
        ],
        clarifications={
            key: value.strip()
            for key, value in request.clarifications.items()
            if value.strip()
        },
        findings=findings,
        themes=["Perceived usefulness", "Capability and support", "Trust and access"],
        limitations=[
            "No web, academic, or other external sources were searched.",
            "All source titles and evidence excerpts are fictional demonstration data.",
            "The examples do not establish prevalence, causality, or applicability to any region or population.",
        ],
        sources=sources,
    )
