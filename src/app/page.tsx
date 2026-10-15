"use client";

import { FormEvent, useState } from "react";

type Evidence = { excerpt: string; source_title: string; note: string };
type Finding = { id: string; title: string; summary: string; theme: string; evidence: Evidence[] };
type Brief = { id: string; question: string; scope?: string; status: string; summary: string; findings: Finding[]; themes: string[]; limitations: string[]; sources: { id: string; title: string; kind: string; status: string }[] };

export default function Home() {
  const [question, setQuestion] = useState("");
  const [scope, setScope] = useState("");
  const [brief, setBrief] = useState<Brief | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (question.trim().length < 12) { setError("Add a little more detail so we can shape a useful research brief."); return; }
    setBusy(true); setError(""); setBrief(null); setSelected(null);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`;
      const response = await fetch(`${apiBase}/api/research`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim(), scope: scope.trim() || null }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail?.[0]?.msg ? `Please check your input: ${body.detail[0].msg}` : "The research service could not complete this request.");
      }
      const result: Brief = await response.json(); setBrief(result); setSelected(result.findings[0]?.id ?? null);
    } catch (err) { setError(err instanceof Error && err.message === "Failed to fetch" ? "Could not reach the research service. Make sure the backend is running, then try again." : err instanceof Error ? err.message : "Something went wrong. Please try again."); }
    finally { setBusy(false); }
  }

  const activeFinding = brief?.findings.find((finding) => finding.id === selected);

  return <main className="app-shell">
    <header className="topbar"><a className="brand" href="#top" aria-label="Cracker home"><span className="brand-mark">c</span><span>cracker<span className="brand-dot">.</span></span></a><nav aria-label="Main navigation"><a className="nav-current" href="#studio">Research studio</a><a href="#about">About</a></nav><div className="top-note"><span className="status-dot"/>Your thinking space</div></header>
    <section className="hero" id="top"><div className="hero-copy"><div className="eyebrow">A clearer way to explore</div><h1>Good research<br/>starts with a <em>question.</em></h1><p>Bring your curiosity. Cracker helps you shape it into a thoughtful, evidence-oriented research brief.</p><div className="hero-foot"><span className="sparkle">✳</span> Make space for better questions.</div></div><div className="hero-art" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="orbit orbit-three"/><div className="art-center">c<span>.</span></div><span className="orbit-label label-one">wonder</span><span className="orbit-label label-two">evidence</span><span className="orbit-label label-three">insight</span><span className="art-spark">✳</span></div></section>
    <section className="studio" id="studio"><div className="section-heading"><div><div className="section-kicker">01 RESEARCH STUDIO</div><h2>What are you curious about?</h2></div><span className="step-note">A question is a good place to begin.</span></div>
      <form className="question-card" onSubmit={submit}><label htmlFor="question">Your research question</label><textarea id="question" value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={500} placeholder="What would you like to understand?" rows={3}/><div className="input-meta"><span>Be specific, or start broad — you can refine it later.</span><span>{question.length}/500</span></div><div className="form-divider"/><div className="scope-row"><label htmlFor="scope"><span className="scope-icon">↳</span> Add a little context <span className="optional">OPTIONAL</span></label><input id="scope" value={scope} onChange={(e) => setScope(e.target.value)} maxLength={1000} placeholder="Geography, audience, timeframe, or anything else we should know"/></div>{error && <div className="error-message" role="alert"><span>!</span>{error}</div>}<div className="submit-row"><span className="privacy-note"><span>✳</span> Your question stays in this local demo.</span><button type="submit" disabled={busy || question.trim().length < 12}>{busy ? <><span className="spinner"/> Exploring…</> : <>Begin exploring <span>↗</span></>}</button></div></form>
      <div className="demo-note"><span className="demo-icon">i</span><p><strong>A note about this experience</strong><br/>This is a demonstration of the research workflow. It uses fictional sample findings and sources — no real research is conducted.</p><span className="demo-tag">DEMO MODE</span></div>
    </section>
    {(busy || brief) && <section className="results" aria-live="polite"><div className="section-heading"><div><div className="section-kicker">02 YOUR RESEARCH BRIEF</div><h2>{busy ? "Preparing your brief" : "A first look at your question"}</h2></div>{brief && <span className="demo-badge"><span className="status-dot"/> SIMULATED EXPLORATION</span>}</div>
      {busy ? <div className="loading-card"><span className="spinner large"/><div><strong>Making connections…</strong><p>Organising a sample brief around your question.</p></div></div> : brief && <><div className="brief-intro"><div className="brief-label">YOUR QUESTION</div><p className="brief-question">“{brief.question}”</p><p className="brief-summary">{brief.summary}</p></div><div className="results-grid"><div className="findings-column"><div className="subhead"><h3>Emerging themes</h3><span>{brief.findings.length} SAMPLE FINDINGS</span></div><div className="findings-list">{brief.findings.map((finding, index) => <button className={`finding-card ${selected === finding.id ? "finding-active" : ""}`} key={finding.id} onClick={() => setSelected(finding.id)}><span className="finding-num">0{index + 1}</span><span className="finding-main"><span className="theme-label">{finding.theme}</span><strong>{finding.title}</strong><span className="finding-summary">{finding.summary}</span><span className="evidence-link">Inspect sample evidence <span>↗</span></span></span><span className="finding-arrow">↗</span></button>)}</div><div className="themes-row"><h3>Across the brief</h3><div>{brief.themes.map((theme) => <span className="theme-chip" key={theme}>{theme}</span>)}</div></div></div><aside className="evidence-panel"><div className="panel-top"><div><span className="section-kicker">03 <span/> EVIDENCE</span><h3>{activeFinding ? "Look closer" : "Select a finding"}</h3></div><span className="evidence-mark">⌕</span></div>{activeFinding ? <><p className="evidence-context">Sample evidence connected to <strong>{activeFinding.title.toLowerCase()}</strong></p>{activeFinding.evidence.map((item, i) => <div className="evidence-card" key={i}><span className="quote-mark">“</span><blockquote>{item.excerpt.replace(/^Example passage: /, "")}</blockquote><div className="evidence-source"><span className="source-icon">▤</span><span><strong>{item.source_title}</strong><small>{item.note}</small></span></div></div>)}</> : <p className="empty-evidence">Choose a finding to inspect the sample passage associated with it.</p>}<div className="integrity-callout"><span>✳</span><p><strong>Evidence integrity</strong><br/>Sample excerpts are fictional and do not support factual claims. No citations have been validated.</p></div></aside></div><div className="limitations"><div><span className="limitation-icon">↗</span><h3>What this brief can’t tell us</h3></div><ul>{brief.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div><div className="sources-strip"><span className="brief-label">DEMONSTRATION SOURCES</span><span>{brief.sources.length} fictional samples</span>{brief.sources.map((source) => <span className="source-pill" key={source.id}>{source.title}</span>)}</div></>}
    </section>}
    <footer id="about"><a className="brand footer-brand" href="#top"><span className="brand-mark">c</span><span>cracker<span className="brand-dot">.</span></span></a><span>Curiosity, with a little more structure.</span><span>RESEARCH STUDIO · EARLY DEMO</span></footer>
  </main>;
}
