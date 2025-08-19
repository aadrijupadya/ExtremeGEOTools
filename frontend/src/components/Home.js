import React from 'react';
import BrandIcon from './BrandIcon';
import { Link } from 'react-router-dom';

function Home() {
	return (
		<div>
			{/* Hero */}
			<section
				className="hero"
				style={{
					background:
						'radial-gradient(900px 500px at 20% 0%, rgba(79,70,229,0.25), rgba(0,0,0,0) 60%),' +
						'radial-gradient(1200px 600px at 80% 10%, rgba(124,58,237,0.2), rgba(0,0,0,0) 60%)',
					padding: '4.5rem 1.25rem',
					borderRadius: 0,
					border: 'none',
					textAlign: 'center'
				}}
			>
				<h1 className="hero-title" style={{ marginBottom: 18 }}>
					<span className="grad-anim">Competitive Intelligence</span>, live and reliable
				</h1>
				<p className="hero-sub muted" style={{ maxWidth: 1100, margin: '0 auto 22px' }}>
					ExtremeGEOTools helps you research markets across AI engines, extract citations and entities,
					and track costs and performance over time. Designed for speed, accuracy, and explainability.
				</p>
				<div className="hero-cta" style={{ display: 'flex', gap: 14, flexWrap: 'wrap', justifyContent: 'center' }}>
					<Link to="/query" className="btn btn-primary">Run a Query</Link>
					<Link to="/results" className="btn btn-secondary">View Results</Link>
				</div>
				<div className="hero-chips" style={{ display: 'flex', gap: 10, marginTop: 18, flexWrap: 'wrap', justifyContent: 'center' }}>
					<span className="chip">Live streaming</span>
					<span className="chip">Citations & Entities</span>
					<span className="chip">Cost visibility</span>
				</div>
			</section>

			{/* Features */}
			<section className="section" style={{ marginTop: 24 }}>
				<h2 className="section-title grad-anim" style={{ textAlign: 'center' }}>Why use GEO Dashboard</h2>
				<div className="features-grid" style={{
					display: 'flex',
					gap: 20,
					flexWrap: 'nowrap',
					overflowX: 'auto'
				}}>
					<div className="feature-card">
						<div className="pill">🔎 Research quality</div>
						<h3>Trust the answer</h3>
						<p className="muted">Normalize outputs, avoid fabrication, and always show sources with full URLs.</p>
					</div>
					<div className="feature-card">
						<div className="pill">🌐 Multi‑engine</div>
						<h3>Compare engines</h3>
						<p className="muted">Run across OpenAI and Perplexity. Capture tokens, latency, and costs consistently.</p>
					</div>
					<div className="feature-card">
						<div className="pill">📈 Visibility</div>
						<h3>See trends</h3>
						<p className="muted">Roll up spend and performance. Export CSV and share results with your team.</p>
					</div>
					<div className="feature-card">
						<div className="pill">🧩 Extensible</div>
						<h3>Pluggable pipeline</h3>
						<p className="muted">Post‑process answers: entities, citations, domains, and brand/competitor tagging.</p>
					</div>
				</div>
			</section>

			{/* How it works */}
			<section className="section" style={{ marginTop: 24 }}>
				<h2 className="section-title grad-anim" style={{ textAlign: 'center' }}>How it works</h2>
				<div className="features-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
					<div className="feature-card">
						<div className="pill">🚀 Submit</div>
						<h3>Pick engine & model</h3>
						<p className="muted">Stream tokens live while we track tokens, latency, and cost signals.</p>
					</div>
					<div className="feature-card" style={{ outline: '1px solid rgba(99,102,241,0.25)' }}>
						<div className="pill">🧭 Extract</div>
						<h3>Normalize & enrich</h3>
						<p className="muted">Detect links and entities, normalize citations, and enrich domains.</p>
					</div>
					<div className="feature-card">
						<div className="pill">📊 Analyze</div>
						<h3>Explore results</h3>
						<p className="muted">Persist output, compute costs, and explore in Results and Costs.</p>
					</div>
				</div>
			</section>

			{/* Engines */}
			<section className="section" style={{ marginTop: 24 }}>
				<h2 className="section-title grad-anim" style={{ textAlign: 'center' }}>Engines</h2>
				<div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center' }}>
					<span className="chip"><BrandIcon name="chatgpt" size={16} style={{ marginRight: 6 }} /> OpenAI · gpt‑4o‑search‑preview</span>
					<span className="chip"><BrandIcon name="chatgpt" size={16} style={{ marginRight: 6 }} /> OpenAI · gpt‑5‑mini</span>
					<span className="chip"><BrandIcon name="perplexity" size={16} style={{ marginRight: 6 }} /> Perplexity · sonar</span>
				</div>
			</section>

            {/* Removed bottom CTA section per request */}
		</div>
	);
}

export default Home;


