export default function AboutPage() {
  return <main className="simple-page about-page">
    <div className="section-kicker">ABOUT CRACKER</div>
    <h1>Research that starts with a better question.</h1>
    <p>Cracker is being built as an autonomous research investigator: a system that can help turn an open question into a careful, evidence-led investigation.</p>
    <section>
      <h2>A thoughtful workflow</h2>
      <p>The intended workflow is to understand the question, clarify its scope, plan an investigation, examine relevant sources, and present findings with their supporting evidence and limits.</p>
    </section>
    <section>
      <h2>Principles we are building toward</h2>
      <ul>
        <li><strong>Traceable evidence:</strong> conclusions should connect to inspectable sources.</li>
        <li><strong>Source verification:</strong> sources need to be checked before they support a claim.</li>
        <li><strong>Honest limitations:</strong> uncertainty and gaps should be stated clearly.</li>
      </ul>
    </section>
    <p className="about-note">The current research flow is a demonstration. It does not retrieve or verify real sources, and autonomous investigation is not implemented yet.</p>
  </main>;
}
