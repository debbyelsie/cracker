from uuid import uuid4
from .schemas import Evidence, Finding, ResearchBrief, ResearchRequest, Source


def run_demo_research(request: ResearchRequest) -> ResearchBrief:
    """Return explicitly fictional demonstration material for the research workflow."""
    source_names = ["Illustrative interview notes (demonstration)", "Sample sector overview (demonstration)", "Example policy extract (demonstration)"]
    sources = [Source(id=f"demo-{i + 1}", title=name, kind="Demonstration source", status="Fictional sample — not a real publication") for i, name in enumerate(source_names)]
    findings = [
        Finding(id="f1", title="Practical value shapes early interest", summary="In this illustrative scenario, owners respond to clear time savings and a visible fit with everyday work.", theme="Perceived usefulness", evidence=[Evidence(excerpt="Example passage: ‘If it gives our team an hour back each day, we will try it.’", source_title=source_names[0], note="Fictional interview excerpt created for this demo.")]),
        Finding(id="f2", title="Confidence and support affect adoption", summary="The sample materials suggest that confidence, training, and access to ongoing help can influence whether a trial becomes routine.", theme="Capability and support", evidence=[Evidence(excerpt="Example passage: ‘We need someone to show us how to use it safely.’", source_title=source_names[1], note="Fictional sample text; no real study is represented.")]),
        Finding(id="f3", title="Trust and cost remain open questions", summary="Concerns about data handling, affordability, and reliable connectivity could shape decisions across different business contexts.", theme="Trust and access", evidence=[Evidence(excerpt="Example passage: ‘The monthly cost and where the data goes both matter.’", source_title=source_names[2], note="Fictional policy-style extract created for this demo.")]),
    ]
    return ResearchBrief(id=str(uuid4()), question=request.question.strip(), scope=request.scope, status="simulated", summary="This is a workflow demonstration, not a real literature search. The sample findings below are fictional and should not be used as research evidence.", findings=findings, themes=["Perceived usefulness", "Capability and support", "Trust and access"], limitations=["No web, academic, or other external sources were searched.", "All source titles and evidence excerpts are fictional demonstration data.", "The examples do not establish prevalence, causality, or applicability to any region or population."], sources=sources)
