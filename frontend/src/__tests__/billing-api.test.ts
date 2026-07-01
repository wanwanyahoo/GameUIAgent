import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  createBillingOrder,
  confirmBillingOrder,
  fetchBillingAccount,
  purchaseCreditPackage
} from "../lib/billing-api";

describe("billing API client", () => {
  it("loads order-aware billing accounts from the backend", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return jsonResponse({
        plan: {
          id: "pro_trial",
          name: "PRO Trial",
          api_enabled: true,
          rate_limit_per_minute: 60,
          concurrent_ai_tasks: 8
        },
        entitlement: {
          plan_id: "pro_trial",
          api_enabled: true,
          rate_limit_per_minute: 60,
          concurrent_ai_tasks: 8
        },
        credits: {
          daily_free: 20,
          monthly: 100,
          purchased: 250,
          total_available: 370,
          deduction_order: ["daily_free", "monthly", "purchased"]
        },
        rate_limit: { limit: 60, window_seconds: 60 },
        recent_orders: [
          {
            id: "ord_1",
            credits: 250,
            provider: "stripe",
            status: "paid",
            created_at: "2026-07-01T00:00:00Z",
            paid_at: "2026-07-01T00:00:01Z"
          }
        ]
      });
    };

    const account = await fetchBillingAccount({ token: "tok_1", fetcher });

    assert.equal(calls[0]?.url, "/api/user/billing");
    assert.equal(calls[0]?.init?.headers?.["Authorization" as keyof HeadersInit], "Bearer tok_1");
    assert.equal(account.plan.name, "PRO Trial");
    assert.equal(account.entitlement.apiEnabled, true);
    assert.equal(account.credits.totalAvailable, 370);
    assert.equal(account.recentOrders[0]?.status, "paid");
  });

  it("creates and confirms credit orders without calling legacy recharge", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      if (url === "/api/user/billing/orders") {
        return jsonResponse({
          id: "ord_1",
          credits: 700,
          provider: "stripe",
          status: "pending",
          created_at: "2026-07-01T00:00:00Z",
          paid_at: null
        });
      }
      return jsonResponse({
        order: {
          id: "ord_1",
          credits: 700,
          provider: "stripe",
          status: "paid",
          created_at: "2026-07-01T00:00:00Z",
          paid_at: "2026-07-01T00:00:01Z"
        },
        billing: {
          plan: {
            id: "pro_trial",
            name: "PRO Trial",
            api_enabled: true,
            rate_limit_per_minute: 60,
            concurrent_ai_tasks: 8
          },
          entitlement: {
            plan_id: "pro_trial",
            api_enabled: true,
            rate_limit_per_minute: 60,
            concurrent_ai_tasks: 8
          },
          credits: {
            daily_free: 20,
            monthly: 100,
            purchased: 700,
            total_available: 820,
            deduction_order: ["daily_free", "monthly", "purchased"]
          },
          rate_limit: { limit: 60, window_seconds: 60 },
          recent_orders: []
        }
      });
    };

    const order = await createBillingOrder({
      token: "tok_1",
      amount: 700,
      method: "stripe",
      externalReference: "checkout_1",
      fetcher
    });
    const confirmed = await confirmBillingOrder({
      token: "tok_1",
      orderId: order.id,
      providerPaymentId: "pi_1",
      fetcher
    });

    assert.deepEqual(calls.map((call) => call.url), [
      "/api/user/billing/orders",
      "/api/user/billing/orders/ord_1/confirm"
    ]);
    assert.ok(calls.every((call) => !call.url.includes("/billing/recharge")));
    assert.equal(calls[0]?.init?.body, JSON.stringify({
      amount: 700,
      method: "stripe",
      external_reference: "checkout_1"
    }));
    assert.equal(calls[1]?.init?.body, JSON.stringify({ provider_payment_id: "pi_1" }));
    assert.equal(confirmed.order.status, "paid");
    assert.equal(confirmed.billing.credits.purchased, 700);
  });

  it("purchases a selected package through order creation and confirmation", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      if (url === "/api/user/billing/orders") {
        return jsonResponse({
          id: "ord_pkg",
          credits: 2200,
          provider: "stripe",
          status: "pending",
          created_at: "2026-07-01T00:00:00Z",
          paid_at: null
        });
      }
      return jsonResponse({
        order: {
          id: "ord_pkg",
          credits: 2200,
          provider: "stripe",
          status: "paid",
          created_at: "2026-07-01T00:00:00Z",
          paid_at: "2026-07-01T00:00:01Z"
        },
        billing: {
          plan: {
            id: "pro_trial",
            name: "PRO Trial",
            api_enabled: true,
            rate_limit_per_minute: 60,
            concurrent_ai_tasks: 8
          },
          entitlement: {
            plan_id: "pro_trial",
            api_enabled: true,
            rate_limit_per_minute: 60,
            concurrent_ai_tasks: 8
          },
          credits: {
            daily_free: 20,
            monthly: 100,
            purchased: 2200,
            total_available: 2320,
            deduction_order: ["daily_free", "monthly", "purchased"]
          },
          rate_limit: { limit: 60, window_seconds: 60 },
          recent_orders: []
        }
      });
    };

    const result = await purchaseCreditPackage({
      token: "tok_1",
      package: { amount: 2000, bonus: 200, price: 29 },
      fetcher,
      now: () => 1782864000000
    });

    assert.deepEqual(calls.map((call) => call.url), [
      "/api/user/billing/orders",
      "/api/user/billing/orders/ord_pkg/confirm"
    ]);
    assert.equal(result.billing.credits.purchased, 2200);
    assert.equal(calls[0]?.init?.body, JSON.stringify({
      amount: 2200,
      method: "stripe",
      external_reference: "checkout_1782864000000"
    }));
    assert.equal(calls[1]?.init?.body, JSON.stringify({
      provider_payment_id: "pi_ord_pkg_1782864000000"
    }));
  });
});

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body
  } as Response;
}
