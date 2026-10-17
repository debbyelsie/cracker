import Link from "next/link";

export default function Home() {
  return <main>
    <section className="hero home-hero">
      <div className="hero-copy">
        <div className="eyebrow">A clearer way to explore</div>
        <h1>Good research<br/>starts with a <em>question.</em></h1>
        <p>Bring your curiosity. Cracker helps you shape it into a thoughtful, evidence-oriented research brief.</p>
        <div className="hero-foot"><span className="sparkle">✳</span> Make space for better questions.</div>
        <Link className="primary-link" href="/chat/new">Start a research session <span>↗</span></Link>
      </div>
      <div className="hero-art" aria-hidden="true">
        <div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="orbit orbit-three"/>
        <div className="art-center">c<span>.</span></div>
        <span className="orbit-label label-one">wonder</span><span className="orbit-label label-two">evidence</span><span className="orbit-label label-three">insight</span><span className="art-spark">✳</span>
      </div>
    </section>
    <section className="home-note">
      <div className="section-kicker">RESEARCH WITH INTENTION</div>
      <h2>Turn a question into a considered investigation.</h2>
      <p>Start by shaping what you want to understand. Cracker is being developed to help investigate questions with care, traceable evidence, and clear limits.</p>
      <Link className="text-link" href="/about">Learn about Cracker <span>↗</span></Link>
    </section>
  </main>;
}
