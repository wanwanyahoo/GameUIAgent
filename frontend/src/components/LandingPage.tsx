import { useState } from "react";
import { navigateTo } from "../lib/hash-router";

export function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const onGetStarted = () => navigateTo("/register");

  const features = [
    {
      icon: "🎨",
      title: "AI-Powered UI Generation",
      description: "Generate stunning game UI assets from text prompts. Cyberpunk, fantasy, sci-fi, pixel art, and more styles supported.",
    },
    {
      icon: "✂️",
      title: "Auto Layered Slicing",
      description: "Qwen Layered Slice technology automatically slices generated art into production-ready UI layers with perfect edges.",
    },
    {
      icon: "🔄",
      title: "Style Transfer",
      description: "Transform any existing UI into a completely new art style while preserving layout and functionality.",
    },
    {
      icon: "📐",
      title: "Professional Import",
      description: "Import PSD, PSB, and Figma files with full layer preservation. Your design workflow stays intact.",
    },
    {
      icon: "🎮",
      title: "Multi-Engine Export",
      description: "One-click export to Unity, Cocos Creator, Godot, and Unreal Engine. Prefabs, atlases, and sprite sheets ready to use.",
    },
    {
      icon: "⚡",
      title: "API & Webhooks",
      description: "Integrate AI generation into your pipeline with REST API, SDKs, and real-time webhook notifications.",
    },
  ];

  const engines = [
    { name: "Unity", icon: "🎯", desc: "2D/3D UI Prefabs" },
    { name: "Cocos Creator", icon: "🥥", desc: "2D/3.x Full Support" },
    { name: "Godot", icon: "⚙️", desc: "Control Scenes" },
    { name: "Unreal Engine", icon: "🎭", desc: "UMG Widgets" },
    { name: "Figma", icon: "🎨", desc: "Design Import" },
    { name: "Photoshop", icon: "📷", desc: "PSD/PSB Layers" },
  ];

  const workflowSteps = [
    { step: "01", title: "Describe", description: "Enter your UI concept as text or upload reference images." },
    { step: "02", title: "Generate", description: "AI creates high-quality game UI artwork in your chosen style." },
    { step: "03", title: "Slice & Layer", description: "Auto-slice into layers with intelligent segmentation." },
    { step: "04", title: "Export", description: "Export directly to your game engine, ready to implement." },
  ];

  const pricingPlans = [
    {
      name: "Free",
      price: 0,
      period: "month",
      credits: "100 credits/mo",
      features: [
        "Text-to-image generation",
        "Basic style transfer",
        "3 engine exports",
        "Community support",
        "5 API calls/min",
      ],
      cta: "Get Started Free",
      highlight: false,
    },
    {
      name: "Pro",
      price: 29,
      period: "month",
      credits: "5,000 credits/mo",
      features: [
        "All Free features",
        "Priority generation queue",
        "Layered auto-slicing",
        "Figma & PSD import",
        "All engine exports",
        "60 API calls/min",
        "Email support",
      ],
      cta: "Start Pro Trial",
      highlight: true,
    },
    {
      name: "Enterprise",
      price: 199,
      period: "month",
      credits: "50,000 credits/mo",
      features: [
        "All Pro features",
        "Dedicated GPU workers",
        "Custom model training",
        "On-premise deployment",
        "SSO & SAML",
        "500 API calls/min",
        "24/7 priority support",
        "SLA guarantee",
      ],
      cta: "Contact Sales",
      highlight: false,
    },
  ];

  return (
    <div className="landing-page">
      <nav className="landing-nav">
        <div className="nav-container">
          <div className="nav-brand">
            <span className="brand-mark">G</span>
            <span>GameUIAgent</span>
          </div>

          <div className={`nav-links ${mobileMenuOpen ? "open" : ""}`}>
            <a href="#features">Features</a>
            <a href="#engines">Engines</a>
            <a href="#workflow">Workflow</a>
            <a href="#pricing">Pricing</a>
            <a href="#docs">Docs</a>
          </div>

          <div className="nav-actions">
            <button type="button" className="nav-signin" onClick={() => navigateTo("/login")}>
              Sign In
            </button>
            <button type="button" className="btn-primary nav-started" onClick={() => navigateTo("/register")}>
              Get Started
            </button>
          </div>

          <button
            type="button"
            className="mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <span /><span /><span />
          </button>
        </div>
      </nav>

      <section className="hero-section">
        <div className="hero-bg">
          <div className="hero-glow glow-1" />
          <div className="hero-glow glow-2" />
          <div className="hero-grid" />
        </div>
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-dot" />
            AI-Powered Game UI Production
          </div>
          <h1 className="hero-title">
            Generate <span className="gradient-text">Production-Ready</span><br />
            Game UI Assets with AI
          </h1>
          <p className="hero-subtitle">
            From concept to engine-ready assets in minutes. Generate, auto-slice,
            and export game UI directly to Unity, Cocos, Godot, and Unreal.
          </p>
          <div className="hero-actions">
            <button type="button" className="btn-primary btn-lg" onClick={() => navigateTo("/register")}>
              Start Creating Free
            </button>
            <button type="button" className="btn-outline btn-lg">
              Watch Demo
            </button>
          </div>
          <div className="hero-trust">
            <div className="trust-item">
              <strong>10K+</strong>
              <span>Assets Generated</span>
            </div>
            <div className="trust-divider" />
            <div className="trust-item">
              <strong>4</strong>
              <span>Game Engines</span>
            </div>
            <div className="trust-divider" />
            <div className="trust-item">
              <strong>99.9%</strong>
              <span>Uptime</span>
            </div>
          </div>
        </div>

        <div className="hero-preview">
          <div className="preview-card">
            <div className="preview-header">
              <div className="preview-dots">
                <span /><span /><span />
              </div>
              <span className="preview-title">AI Studio — Cyberpunk Menu</span>
            </div>
            <div className="preview-body">
              <div className="preview-ui">
                <div className="ui-panel">
                  <div className="ui-title">NEW GAME</div>
                  <div className="ui-subtitle">START YOUR ADVENTURE</div>
                </div>
                <div className="ui-buttons">
                  <div className="ui-btn ui-btn-primary">CONTINUE</div>
                  <div className="ui-btn">OPTIONS</div>
                  <div className="ui-btn">CREDITS</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="features-section">
        <div className="section-header">
          <span className="section-tag">Features</span>
          <h2>Everything You Need for Game UI Production</h2>
          <p>Complete AI-powered workflow from concept to implementation in your game engine.</p>
        </div>
        <div className="features-grid">
          {features.map((feature, i) => (
            <div key={i} className="feature-card">
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="engines" className="engines-section">
        <div className="section-header">
          <span className="section-tag">Integrations</span>
          <h2>Works With Your Favorite Tools</h2>
          <p>Seamless import from design tools and export to all major game engines.</p>
        </div>
        <div className="engines-grid">
          {engines.map((engine, i) => (
            <div key={i} className="engine-card">
              <div className="engine-icon">{engine.icon}</div>
              <h3>{engine.name}</h3>
              <p>{engine.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="workflow" className="workflow-section">
        <div className="section-header">
          <span className="section-tag">How It Works</span>
          <h2>From Idea to Game in 4 Steps</h2>
          <p>Our AI pipeline handles the heavy lifting so you can focus on creativity.</p>
        </div>
        <div className="workflow-grid">
          {workflowSteps.map((step, i) => (
            <div key={i} className="workflow-card">
              <div className="workflow-step">{step.step}</div>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
              {i < workflowSteps.length - 1 && <div className="workflow-arrow" />}
            </div>
          ))}
        </div>
      </section>

      <section id="pricing" className="pricing-section">
        <div className="section-header">
          <span className="section-tag">Pricing</span>
          <h2>Simple, Transparent Pricing</h2>
          <p>Start free and scale as you grow. No hidden fees, cancel anytime.</p>
        </div>
        <div className="pricing-grid">
          {pricingPlans.map((plan, i) => (
            <div key={i} className={`pricing-card ${plan.highlight ? "highlight" : ""}`}>
              {plan.highlight && <div className="pricing-badge">Most Popular</div>}
              <h3>{plan.name}</h3>
              <div className="pricing-price">
                <span className="price-currency">$</span>
                <span className="price-amount">{plan.price}</span>
                <span className="price-period">/{plan.period}</span>
              </div>
              <div className="pricing-credits">{plan.credits}</div>
              <ul className="pricing-features">
                {plan.features.map((f, j) => (
                  <li key={j}>{f}</li>
                ))}
              </ul>
              <button
                type="button"
                className={plan.highlight ? "btn-primary btn-block" : "btn-outline btn-block"}
                onClick={() => navigateTo("/register")}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="cta-section">
        <div className="cta-bg">
          <div className="cta-glow" />
        </div>
        <div className="cta-content">
          <h2>Ready to Revolutionize Your Game UI Workflow?</h2>
          <p>Join thousands of game developers creating stunning UI faster than ever before.</p>
          <div className="cta-actions">
            <button type="button" className="btn-primary btn-lg" onClick={onGetStarted}>
              Start for Free
            </button>
            <button type="button" className="btn-outline btn-lg">
              Talk to Sales
            </button>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="footer-container">
          <div className="footer-brand">
            <div className="nav-brand">
              <span className="brand-mark">G</span>
              <span>GameUIAgent</span>
            </div>
            <p>AI-powered game UI asset generation and production pipeline.</p>
          </div>
          <div className="footer-links">
            <div className="footer-column">
              <h4>Product</h4>
              <a href="#features">Features</a>
              <a href="#pricing">Pricing</a>
              <a href="#engines">Engines</a>
              <a href="#workflow">How It Works</a>
            </div>
            <div className="footer-column">
              <h4>Developers</h4>
              <a href="#docs">Documentation</a>
              <a href="#api">API Reference</a>
              <a href="#sdks">SDKs</a>
              <a href="#status">Status</a>
            </div>
            <div className="footer-column">
              <h4>Company</h4>
              <a href="#about">About</a>
              <a href="#blog">Blog</a>
              <a href="#careers">Careers</a>
              <a href="#contact">Contact</a>
            </div>
            <div className="footer-column">
              <h4>Legal</h4>
              <a href="#privacy">Privacy Policy</a>
              <a href="#terms">Terms of Service</a>
              <a href="#security">Security</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2025 GameUIAgent. All rights reserved.</p>
          <div className="footer-social">
            <a href="#twitter" aria-label="Twitter">𝕏</a>
            <a href="#github" aria-label="GitHub">⌘</a>
            <a href="#discord" aria-label="Discord">◉</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
