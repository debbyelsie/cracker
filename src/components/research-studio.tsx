"use client";

import { FormEvent, useState } from "react";

type Evidence = { excerpt: string; source_title: string; note: string };
type Finding = { id: string; title: string; summary: string; theme: string; evidence: Evidence[] };
type IntakeQuestion = { id: string; prompt: string; hint: string };
type Intake = {
  question: string;
  interpretation: string;
  questions: IntakeQuestion[];
  investigation_plan: string[];
  notice: string;
};
type Brief = {
  id: string;
  question: string;
  scope?: string;
  status: string;
  summary: string;
  detailed_answer: string;
  investigation_plan: string[];
  clarifications: Record<string, string>;
  findings: Finding[];
  themes: string[];
  limitations: string[];
  sources: { id: string; title: string; kind: string; status: string }[];
};

type BusyStage = "intake" | "research" | null;

function apiUrl(path: string) {
  const base = process.env.NEXT_PUBLIC_API_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`;
  return `${base}${path}`;
}

async function postJSON<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail?.[0]?.msg ?? body?.detail ?? "The research service could not complete this request.";
    throw new Error(typeof message === "string" ? message : "Please check your question and try again.");
  }
  return response.json() as Promise<T>;
}

export default function ResearchStudio() {
  const [question, setQuestion] = useState("");
  const [scope, setScope] = useState("");
  const [intake, setIntake] = useState<Intake | null>(null);
  const [clarifications, setClarifications] = useState<Record<string, string>>({});
  const [brief, setBrief] = useState<Brief | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState<BusyStage>(null);
  const [error, setError] = useState("");

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (cleanQuestion.length < 12) {
      setError("Add a little more detail so I can check the question with you.");
      return;
    }

    setBusy("intake");
    setError("");
    setIntake(null);
    setBrief(null);
    setClarifications({});
    setSelected(null);
    try {
      const result = await postJSON<Intake>("/api/research/intake", {
        question: cleanQuestion,
        scope: scope.trim() || null,
      });
      setIntake(result);
    } catch (cause) {
      setError(cause instanceof Error && cause.message === "Failed to fetch"
        ? "Could not reach the research service. Make sure the backend is running, then try again."
        : cause instanceof Error ? cause.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  async function beginInvestigation() {
    setBusy("research");
    setError("");
    setBrief(null);
    setSelected(null);
    try {
      const result = await postJSON<Brief>("/api/research", {
        question: question.trim(),
        scope: scope.trim() || null,
        clarifications,
      });
      setBrief(result);
      setSelected(result.findings[0]?.id ?? null);
    } catch (cause) {
      setError(cause instanceof Error && cause.message === "Failed to fetch"
        ? "Could not reach the research service. Make sure the backend is running, then try again."
        : cause instanceof Error ? cause.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  const activeFinding = brief?.findings.find((finding) => finding.id === selected);
  const answeredClarifications = brief
    ? Object.entries(brief.clarifications).filter(([, answer]) => answer.trim())
    : [];

  return <main className="research-workspace">
    <section className="studio" id="studio">
      <div className="section-heading">
        <div><div className="section-kicker">01 RESEARCH STUDIO</div><h2>What are you curious about?</h2></div>
        <span className="step-note">An investigator starts by understanding the question.</span>
      </div>
      <form className="question-card" onSubmit={submitQuestion}>
        <label htmlFor="question">Your research question</label>
        <textarea id="question" value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={500} placeholder="What would you like to understand?" rows={3}/>
        <div className="input-meta"><span>Be specific, or start broad — you can refine it later.</span><span>{question.length}/500</span></div>
        <div className="form-divider"/>
        <div className="scope-row">
          <label htmlFor="scope"><span className="scope-icon">↳</span> Add a little context <span className="optional">OPTIONAL</span></label>
          <input id="scope" value={scope} onChange={(event) => setScope(event.target.value)} maxLength={1000} placeholder="Geography, audience, timeframe, or anything else we should know"/>
        </div>
        {error && <div className="error-message" role="alert"><span>!</span>{error}</div>}
        <div className="submit-row">
          <span className="privacy-note"><span>✳</span> Your question stays in this local demo.</span>
          <button type="submit" disabled={busy !== null || question.trim().length < 12}>
            {busy === "intake" ? <><span className="spinner"/> Thinking it through…</> : <>Begin exploring <span>↗</span></>}
          </button>
        </div>
      </form>

      <div className="demo-note">
        <span className="demo-icon">i</span>
        <p><strong>A note about this experience</strong><br/>This is a demonstration of the research workflow. Its findings and sources are fictional; no real research is conducted.</p>
        <span className="demo-tag">DEMO MODE</span>
      </div>
    </section>

    {(busy === "intake" || intake) && <section className="intake-section" aria-live="polite">
      <div className="section-heading">
        <div><div className="section-kicker">02 QUESTION SCOPE</div><h2>Let me check I understand</h2></div>
      </div>
      {busy === "intake" && <div className="loading-card"><span className="spinner large"/><div><strong>Preparing a scope check…</strong><p>Organising a few questions to shape the investigation.</p></div></div>}
      {intake && <>
        <div className="interpretation-card"><span className="brief-label">HOW I UNDERSTAND YOUR QUESTION</span><p>{intake.interpretation}</p></div>
        <div className="clarification-card">
          <div className="clarification-heading"><div><h3>What should I keep in mind?</h3><p>Your answers help set the investigation’s boundaries. You can leave any blank.</p></div><span className="step-count">OPTIONAL</span></div>
          <div className="clarification-fields">{intake.questions.map((item, index) => <div className="clarification-field" key={item.id}>
            <label htmlFor={`clarification-${item.id}`}><span>0{index + 1}</span>{item.prompt}</label>
            <textarea id={`clarification-${item.id}`} value={clarifications[item.id] ?? ""} onChange={(event) => setClarifications((current) => ({ ...current, [item.id]: event.target.value }))} placeholder={item.hint} rows={2}/>
          </div>)}</div>
          <div className="plan-preview"><strong>How a full investigation would proceed</strong><ol>{intake.investigation_plan.map((step) => <li key={step}>{step}</li>)}</ol></div>
          {error && <div className="error-message" role="alert"><span>!</span>{error}</div>}
          <div className="clarification-actions">
            <span className="intake-notice">{intake.notice}</span>
            <button type="button" onClick={beginInvestigation} disabled={busy !== null}>
              {busy === "research" ? <><span className="spinner"/> Building your brief…</> : <>Build my research brief <span>↗</span></>}
            </button>
            <button className="text-button" type="button" onClick={beginInvestigation} disabled={busy !== null}>Continue without adding answers</button>
          </div>
        </div>
      </>}
    </section>}

    {(busy === "research" || brief) && <section className="results" aria-live="polite">
      <div className="section-heading">
        <div><div className="section-kicker">03 RESEARCH BRIEF</div><h2>{busy === "research" ? "Preparing your brief" : "A first look at your question"}</h2></div>
        {brief && <span className="demo-badge"><span className="status-dot"/> SIMULATED EXPLORATION</span>}
      </div>
      {busy === "research" && <div className="loading-card"><span className="spinner large"/><div><strong>Organising the investigation…</strong><p>Preparing a structured demonstration brief.</p></div></div>}
      {brief && <>
        <div className="brief-intro">
          <div className="brief-label">YOUR QUESTION</div>
          <p className="brief-question">“{brief.question}”</p>
          {brief.scope && <p className="brief-summary"><strong>Context:</strong> {brief.scope}</p>}
          <p className="brief-summary">{brief.summary}</p>
        </div>
        <div className="detailed-answer"><div className="section-kicker">DEMO SYNTHESIS</div><h3>A more detailed look</h3><p>{brief.detailed_answer}</p></div>
        {answeredClarifications.length > 0 && <div className="scope-recap"><strong>Context you gave the investigator</strong><dl>{answeredClarifications.map(([key, answer]) => <div key={key}><dt>{intake?.questions.find((item) => item.id === key)?.prompt ?? key}</dt><dd>{answer}</dd></div>)}</dl></div>}
        <div className="plan-preview brief-plan"><strong>Investigation plan</strong><ol>{brief.investigation_plan.map((step) => <li key={step}>{step}</li>)}</ol></div>
        <div className="results-grid">
          <div className="findings-column">
            <div className="subhead"><h3>Emerging themes</h3><span>{brief.findings.length} SAMPLE FINDINGS</span></div>
            <div className="findings-list">{brief.findings.map((finding, index) => <button className={`finding-card ${selected === finding.id ? "finding-active" : ""}`} key={finding.id} onClick={() => setSelected(finding.id)}>
              <span className="finding-num">0{index + 1}</span><span className="finding-main"><span className="theme-label">{finding.theme}</span><strong>{finding.title}</strong><span className="finding-summary">{finding.summary}</span><span className="evidence-link">Inspect sample evidence <span>↗</span></span></span><span className="finding-arrow">↗</span>
            </button>)}</div>
            <div className="themes-row"><h3>Across the brief</h3><div>{brief.themes.map((theme) => <span className="theme-chip" key={theme}>{theme}</span>)}</div></div>
          </div>
          <aside className="evidence-panel">
            <div className="panel-top"><div><span className="section-kicker">04 EVIDENCE</span><h3>{activeFinding ? "Look closer" : "Select a finding"}</h3></div><span className="evidence-mark">⌕</span></div>
            {activeFinding ? <><p className="evidence-context">Sample evidence connected to <strong>{activeFinding.title.toLowerCase()}</strong></p>{activeFinding.evidence.map((item, index) => <div className="evidence-card" key={index}><span className="quote-mark">“</span><blockquote>{item.excerpt.replace(/^Example passage: /, "")}</blockquote><div className="evidence-source"><span className="source-icon">▤</span><span><strong>{item.source_title}</strong><small>{item.note}</small></span></div></div>)}</> : <p className="empty-evidence">Choose a finding to inspect the sample passage associated with it.</p>}
            <div className="integrity-callout"><span>✳</span><p><strong>Evidence integrity</strong><br/>Sample excerpts are fictional and do not support factual claims. No citations have been validated.</p></div>
          </aside>
        </div>
        <div className="limitations"><div><span className="limitation-icon">↗</span><h3>What this brief can’t tell us</h3></div><ul>{brief.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div>
        <div className="sources-strip"><span className="brief-label">DEMONSTRATION SOURCES</span><span>{brief.sources.length} fictional samples</span>{brief.sources.map((source) => <span className="source-pill" key={source.id}>{source.title}</span>)}</div>
      </>}
    </section>}

  </main>;
}
