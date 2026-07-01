import { useState, useEffect } from "react";
import { useAuth } from "../lib/auth-context";
import { type BillingAccount, purchaseCreditPackage, fetchBillingAccount } from "../lib/billing-api";

export function BillingPage() {
  const { token } = useAuth();
  const [billing, setBilling] = useState<BillingAccount | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rechargeOpen, setRechargeOpen] = useState(false);
  const [rechargeAmount, setRechargeAmount] = useState(500);

  const plans = [
    {
      id: "free",
      name: "Free",
      price: 0,
      period: "month",
      credits: 100,
      features: ["100 monthly credits", "Standard quality", "5 API calls/min", "Community support"],
      highlight: false,
    },
    {
      id: "pro",
      name: "Pro",
      price: 29,
      period: "month",
      credits: 5000,
      features: ["5,000 monthly credits", "Priority generation", "60 API calls/min", "Email support", "Figma import", "All engine exports"],
      highlight: true,
    },
    {
      id: "enterprise",
      name: "Enterprise",
      price: 199,
      period: "month",
      credits: 50000,
      features: ["50,000 monthly credits", "Dedicated GPU workers", "500 API calls/min", "24/7 priority support", "Custom models", "SLA guarantees", "SSO/SAML"],
      highlight: false,
    },
  ];

  const rechargePackages = [
    { amount: 500, price: 9, bonus: 0 },
    { amount: 2000, price: 29, bonus: 200 },
    { amount: 5000, price: 69, bonus: 750 },
    { amount: 20000, price: 249, bonus: 4000 },
  ];

  useEffect(() => {
    let cancelled = false;
    if (!token) return;
    const authToken = token;

    async function loadBilling() {
      try {
        setLoading(true);
        const data = await fetchBillingAccount({ token: authToken });
        if (!cancelled) {
          setBilling(data);
          setError(null);
        }
      } catch (err: any) {
        if (!cancelled) setError(err.message || "Failed to load billing info");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadBilling();
    return () => { cancelled = true; };
  }, [token]);

  const handleRecharge = async (pkg: typeof rechargePackages[0]) => {
    if (!token || !billing) return;
    try {
      setError(null);
      const result = await purchaseCreditPackage({
        token,
        package: pkg,
      });
      setBilling(result.billing);
      setRechargeOpen(false);
    } catch (err: any) {
      setError(err.message || "Purchase failed");
    }
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  return (
    <div className="billing-page">
      <div className="page-header">
        <h1>Billing &amp; Credits</h1>
        <p className="page-subtitle">Manage your subscription, credits, and billing info</p>
      </div>

      {loading && <div className="loading">Loading billing info...</div>}
      {error && <div className="error-banner">{error}</div>}

      {billing && (
        <>
          <section className="credits-overview">
            <div className="credit-card primary">
              <div className="credit-label">Total Available Credits</div>
              <div className="credit-value">{billing.credits.totalAvailable.toLocaleString()}</div>
              <div className="credit-breakdown">
                <span>Free: {billing.credits.dailyFree.toLocaleString()}</span>
                <span>Monthly: {billing.credits.monthly.toLocaleString()}</span>
                <span>Purchased: {billing.credits.purchased.toLocaleString()}</span>
              </div>
            </div>
            <div className="credit-card">
              <div className="credit-label">Current Plan</div>
              <div className="credit-value small">{billing.plan.name}</div>
              <div className="credit-meta">API: <strong>{billing.entitlement.apiEnabled ? "Enabled" : "Disabled"}</strong></div>
              <div className="credit-meta">Rate limit: {billing.rateLimit.limit}/min</div>
            </div>
            <div className="credit-card action">
              <div className="credit-label">Buy More Credits</div>
              <div className="credit-value small">Top up anytime</div>
              <button type="button" className="btn-primary" onClick={() => setRechargeOpen(true)}>
                Add Credits
              </button>
            </div>
          </section>

          <section className="plan-section">
            <h2>Your Plan</h2>
            <div className="plans-grid">
              {plans.map((plan) => (
                <div key={plan.id} className={`plan-card ${plan.highlight ? "highlight" : ""} ${billing.plan.id === plan.id ? "current" : ""}`}>
                  {plan.highlight && <div className="plan-badge">Most Popular</div>}
                  {billing.plan.id === plan.id && <div className="plan-current-badge">Current Plan</div>}
                  <div className="plan-name">{plan.name}</div>
                  <div className="plan-price">
                    <span className="price-currency">$</span>
                    <span className="price-amount">{plan.price}</span>
                    <span className="price-period">/{plan.period}</span>
                  </div>
                  <div className="plan-credits">{plan.credits.toLocaleString()} credits/mo</div>
                  <ul className="plan-features">
                    {plan.features.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                  <button
                    type="button"
                    className={billing.plan.id === plan.id ? "btn-secondary" : plan.highlight ? "btn-primary" : "btn-outline"}
                    disabled={billing.plan.id === plan.id}
                  >
                    {billing.plan.id === plan.id ? "Current Plan" : "Upgrade"}
                  </button>
                </div>
              ))}
            </div>
          </section>

          <section className="usage-section">
            <h2>Usage This Month</h2>
            <div className="usage-bar">
              <div
                className="usage-fill"
                style={{ width: `${Math.min(100, ((billing.credits.monthly + billing.credits.dailyFree) / (billing.credits.totalAvailable || 1)) * 100)}%` }}
              />
            </div>
            <div className="usage-meta">
              <span>{billing.credits.deductionOrder.join(" -> ")}</span>
              <span>{billing.credits.totalAvailable.toLocaleString()} remaining</span>
            </div>
            {billing.recentOrders.length > 0 && (
              <div className="usage-meta">
                <span>Latest order: {billing.recentOrders[0].id}</span>
                <span>{billing.recentOrders[0].status} · {formatDate(billing.recentOrders[0].createdAt)}</span>
              </div>
            )}
          </section>
        </>
      )}

      {rechargeOpen && (
        <div className="modal-overlay" onClick={() => setRechargeOpen(false)}>
          <div className="modal recharge-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Add Credits</h2>
            <p className="modal-subtitle">Select a credit package. Credits never expire.</p>
            <div className="recharge-packages">
              {rechargePackages.map((pkg) => (
                <button
                  key={pkg.amount}
                  type="button"
                  className={`recharge-pkg ${rechargeAmount === pkg.amount ? "selected" : ""}`}
                  onClick={() => setRechargeAmount(pkg.amount)}
                >
                  <div className="pkg-amount">
                    {pkg.amount.toLocaleString()} credits
                    {pkg.bonus > 0 && <span className="pkg-bonus">+{pkg.bonus.toLocaleString()} bonus</span>}
                  </div>
                  <div className="pkg-price">${pkg.price}</div>
                </button>
              ))}
            </div>
            <div className="modal-actions">
              <button type="button" className="btn-outline" onClick={() => setRechargeOpen(false)}>
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={() => {
                  const pkg = rechargePackages.find((p) => p.amount === rechargeAmount) || rechargePackages[0];
                  handleRecharge(pkg);
                }}
              >
                Purchase
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
