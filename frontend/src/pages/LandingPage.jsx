import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Sparkles,
  Shield,
  Brain,
  FileSearch,
  MessageSquare,
  Layers,
  Zap,
  ArrowRight,
  Play,
  Upload,
  Search,
  Scale,
  Heart,
  Users,
} from 'lucide-react'
import './LandingPage.css'

export default function LandingPage() {
  useEffect(() => {
    const observerCallback = (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed')
        }
      })
    }

    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -40px 0px',
    }

    const observer = new IntersectionObserver(observerCallback, observerOptions)
    const targets = document.querySelectorAll(
      '.scroll-reveal, .scroll-reveal-left, .scroll-reveal-right, .scroll-reveal-scale'
    )
    targets.forEach((el) => observer.observe(el))

    return () => observer.disconnect()
  }, [])

  return (
    <div className="landing">
      {/* ── Navbar ── */}
      <nav className="landing-nav" id="landing-navbar">
        <Link to="/" className="landing-nav-logo">
          <div className="landing-nav-logo-icon">
            <Sparkles size={18} />
          </div>
          <span className="landing-nav-logo-text">Doc Clarity</span>
        </Link>
        <ul className="landing-nav-links">
          <li><a href="#features">Key Features</a></li>
          <li><a href="#how-it-works">How It Works</a></li>
          <li><a href="#domains">Domains</a></li>
        </ul>
        <div className="landing-nav-actions">
          <Link to="/dashboard" className="btn btn-primary" id="nav-get-started">
            Get Started <ArrowRight size={16} />
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="hero" id="hero-section">
        <h1 className="hero-title scroll-reveal">
          <span className="hero-title-line">
            Transform Your{' '}
            <span className="text-gradient">Document Intelligence</span>
          </span>
          <span className="hero-title-line">
            — Smarter, Faster and{' '}
            <span className="text-accent">Secure</span>
          </span>
        </h1>

        <p className="hero-subtitle scroll-reveal stagger-1">
          Upload complex legal, insurance, and medical documents.
          Get AI-powered analysis, grounded Q&A with citations,
          and actionable insights in seconds.
        </p>

        <div className="hero-actions scroll-reveal stagger-2">
          <Link to="/dashboard" className="btn btn-primary btn-lg" id="hero-start-btn">
            Start Analyzing Free <ArrowRight size={18} />
          </Link>
          <a href="#how-it-works" className="btn btn-secondary btn-lg" id="hero-demo-btn">
            <Play size={16} /> See How It Works
          </a>
        </div>

        <div className="hero-stats scroll-reveal stagger-3">
          <div className="hero-stat">
            <div className="hero-stat-value">3</div>
            <div className="hero-stat-label">Domains Supported</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">3</div>
            <div className="hero-stat-label">Persona Modes</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">AI</div>
            <div className="hero-stat-label">Grounded Answers</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">100%</div>
            <div className="hero-stat-label">Citation Traceability</div>
          </div>
        </div>

        {/* Mock Dashboard Preview */}
        <div className="hero-preview scroll-reveal-scale stagger-4">
          <div className="hero-preview-window">
            <div className="hero-preview-titlebar">
              <span className="hero-preview-dot red" />
              <span className="hero-preview-dot yellow" />
              <span className="hero-preview-dot green" />
            </div>
            <div className="hero-preview-body">
              <div className="hero-preview-card">
                <div className="hero-preview-card-title">Document Analysis</div>
                <div className="hero-preview-metric">5 Key Findings</div>
                <div className="hero-preview-bars">
                  {[60, 85, 45, 70, 90, 55, 75].map((h, i) => (
                    <div
                      key={i}
                      className="hero-preview-bar"
                      style={{
                        height: `${h}%`,
                        animationDelay: `${0.6 + i * 0.1}s`,
                      }}
                    />
                  ))}
                </div>
              </div>
              <div className="hero-preview-card">
                <div className="hero-preview-card-title">AI Conversation</div>
                <div className="hero-preview-chat">
                  <div className="hero-preview-msg user">
                    What are the main exclusions in this policy?
                  </div>
                  <div className="hero-preview-msg ai">
                    Based on Section 4.2, the policy excludes pre-existing conditions,
                    cosmetic procedures, and acts of war. Citations: [Page 12, §4.2]
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="features-section" id="features">
        <div className="features-header scroll-reveal">
          <div className="features-label">Key Features</div>
          <h2 className="features-title">
            Why Choose <span className="text-gradient">Doc Clarity</span>?
          </h2>
          <p className="features-subtitle">
            Enterprise-grade document intelligence with AI that understands context,
            cites sources, and adapts to your expertise level.
          </p>
        </div>

        <div className="features-grid">
          {[
            {
              icon: Brain,
              title: 'Intelligent Q&A',
              desc: 'Ask natural language questions about your documents. Answers are grounded in actual document content with full citation traceability.',
            },
            {
              icon: FileSearch,
              title: 'Automatic Analysis',
              desc: 'Get instant executive summaries, key findings, important dates, financial terms, obligations, exclusions, and risk attention items.',
            },
            {
              icon: Users,
              title: 'Multi-Persona Modes',
              desc: 'Consumer mode for plain English, Professional mode for precise legal terms, Business mode for operational and financial focus.',
            },
            {
              icon: Shield,
              title: 'Enterprise-Grade Security',
              desc: 'Built-in protection ensures all answers are strictly grounded in your uploaded document content. Your data stays safe and private.',
            },
            {
              icon: MessageSquare,
              title: 'Multi-Turn Conversations',
              desc: 'Have follow-up conversations about your documents with full context awareness and conversation history.',
            },
            {
              icon: Layers,
              title: 'Semantic Search',
              desc: 'Go beyond keyword matching. Find relevant sections using natural language queries ranked by contextual similarity.',
            },
          ].map((f, i) => (
            <div className={`feature-card scroll-reveal stagger-${(i % 3) + 1}`} key={i}>
              <div className="feature-icon">
                <f.icon size={24} />
              </div>
              <h3 className="feature-title">{f.title}</h3>
              <p className="feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="how-section" id="how-it-works">
        <div className="features-header scroll-reveal">
          <div className="features-label">How It Works</div>
          <h2 className="features-title">
            Get Started in 4 <span className="text-accent">Simple Steps</span>
          </h2>
        </div>

        <div className="how-steps">
          {[
            {
              num: 1,
              icon: Upload,
              title: 'Upload Document',
              desc: 'Upload your legal contract, insurance policy, or medical report in PDF format.',
            },
            {
              num: 2,
              icon: Zap,
              title: 'AI Processing',
              desc: 'Text extraction, OCR, and intelligent content analysis happen automatically behind the scenes.',
            },
            {
              num: 3,
              icon: Search,
              title: 'Explore & Analyze',
              desc: 'Get automatic analysis with key findings, dates, financials, obligations, and risk flags.',
            },
            {
              num: 4,
              icon: MessageSquare,
              title: 'Ask & Converse',
              desc: 'Ask grounded questions and have multi-turn conversations with cited AI responses.',
            },
          ].map((s, i) => (
            <div className={`how-step scroll-reveal stagger-${i + 1}`} key={i}>
              <div className="how-step-number">{s.num}</div>
              {i < 3 && <div className="how-step-connector" />}
              <h3 className="how-step-title">{s.title}</h3>
              <p className="how-step-desc">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Domains ── */}
      <section className="domains-section" id="domains">
        <div className="features-header scroll-reveal">
          <div className="features-label">Domains</div>
          <h2 className="features-title">
            Built for <span className="text-gradient">High-Stakes Documents</span>
          </h2>
          <p className="features-subtitle">
            Purpose-built intelligence for the three most critical document domains.
          </p>
        </div>

        <div className="domains-grid">
          {[
            {
              icon: Scale,
              title: 'Legal',
              desc: 'Contracts, NDAs, compliance documents. Extract clauses, obligations, termination provisions, and liability terms.',
              tags: ['Contracts', 'NDA', 'Compliance', 'Clauses'],
            },
            {
              icon: Shield,
              title: 'Insurance',
              desc: 'Policies, claims documents. Identify coverage limits, exclusions, deductibles, waiting periods, and premium terms.',
              tags: ['Policies', 'Claims', 'Coverage', 'Exclusions'],
            },
            {
              icon: Heart,
              title: 'Medical',
              desc: 'Medical reports, patient records. Understand diagnoses, treatment plans, medication details, and follow-up requirements.',
              tags: ['Reports', 'Records', 'Diagnoses', 'Treatment'],
            },
          ].map((d, i) => (
            <div className={`domain-card scroll-reveal stagger-${i + 1}`} key={i}>
              <div className="domain-icon-wrap">
                <d.icon size={32} />
              </div>
              <h3 className="domain-title">{d.title}</h3>
              <p className="domain-desc">{d.desc}</p>
              <div className="domain-tags">
                {d.tags.map((t, j) => (
                  <span className="badge badge-success" key={j}>{t}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="cta-section">
        <div className="cta-box scroll-reveal-scale">
          <h2 className="cta-title">
            Ready to <span className="text-gradient">Understand</span> Your Documents?
          </h2>
          <p className="cta-subtitle">
            Upload your first document and experience AI-powered document intelligence.
          </p>
          <Link to="/dashboard" className="btn btn-primary btn-lg" id="cta-start-btn">
            Get Started Now <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <p>© 2026 Doc Clarity — AI Document Intelligence Platform.</p>
      </footer>
    </div>
  )
}
