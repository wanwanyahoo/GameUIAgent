export type BillingApiFetcher = (url: string, init?: RequestInit) => Promise<Response>;

export type BillingCreditPackage = {
  amount: number;
  bonus: number;
  price: number;
};

export type BillingPlan = {
  id: string;
  name: string;
  apiEnabled: boolean;
  rateLimitPerMinute: number;
  concurrentAiTasks: number;
};

export type BillingEntitlement = {
  planId: string;
  apiEnabled: boolean;
  rateLimitPerMinute: number;
  concurrentAiTasks: number;
};

export type BillingCredits = {
  dailyFree: number;
  monthly: number;
  purchased: number;
  totalAvailable: number;
  deductionOrder: string[];
};

export type BillingOrder = {
  id: string;
  credits: number;
  provider: string;
  status: "pending" | "paid";
  createdAt: string;
  paidAt: string | null;
};

export type BillingAccount = {
  plan: BillingPlan;
  entitlement: BillingEntitlement;
  credits: BillingCredits;
  rateLimit: {
    limit: number;
    windowSeconds: number;
  };
  recentOrders: BillingOrder[];
};

type BillingPlanDto = {
  id: string;
  name: string;
  api_enabled: boolean;
  rate_limit_per_minute: number;
  concurrent_ai_tasks: number;
};

type BillingEntitlementDto = {
  plan_id: string;
  api_enabled: boolean;
  rate_limit_per_minute: number;
  concurrent_ai_tasks: number;
};

type BillingCreditsDto = {
  daily_free: number;
  monthly: number;
  purchased: number;
  total_available: number;
  deduction_order: string[];
};

type BillingOrderDto = {
  id: string;
  credits: number;
  provider: string;
  status: "pending" | "paid";
  created_at: string;
  paid_at: string | null;
};

type BillingAccountDto = {
  plan: BillingPlanDto;
  entitlement: BillingEntitlementDto;
  credits: BillingCreditsDto;
  rate_limit: {
    limit: number;
    window_seconds: number;
  };
  recent_orders: BillingOrderDto[];
};

export function mapBillingAccountDto(dto: BillingAccountDto): BillingAccount {
  return {
    plan: {
      id: dto.plan.id,
      name: dto.plan.name,
      apiEnabled: dto.plan.api_enabled,
      rateLimitPerMinute: dto.plan.rate_limit_per_minute,
      concurrentAiTasks: dto.plan.concurrent_ai_tasks
    },
    entitlement: {
      planId: dto.entitlement.plan_id,
      apiEnabled: dto.entitlement.api_enabled,
      rateLimitPerMinute: dto.entitlement.rate_limit_per_minute,
      concurrentAiTasks: dto.entitlement.concurrent_ai_tasks
    },
    credits: {
      dailyFree: dto.credits.daily_free,
      monthly: dto.credits.monthly,
      purchased: dto.credits.purchased,
      totalAvailable: dto.credits.total_available,
      deductionOrder: dto.credits.deduction_order
    },
    rateLimit: {
      limit: dto.rate_limit.limit,
      windowSeconds: dto.rate_limit.window_seconds
    },
    recentOrders: dto.recent_orders.map(mapBillingOrderDto)
  };
}

function mapBillingOrderDto(dto: BillingOrderDto): BillingOrder {
  return {
    id: dto.id,
    credits: dto.credits,
    provider: dto.provider,
    status: dto.status,
    createdAt: dto.created_at,
    paidAt: dto.paid_at
  };
}

export async function fetchBillingAccount(options: {
  token: string;
  fetcher?: BillingApiFetcher;
}): Promise<BillingAccount> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher("/api/user/billing", {
    headers: { Authorization: `Bearer ${options.token}` }
  });
  if (!response.ok) {
    throw new Error("Failed to load billing");
  }
  return mapBillingAccountDto(await response.json() as BillingAccountDto);
}

export async function createBillingOrder(options: {
  token: string;
  amount: number;
  method: "stripe" | "paypal" | "alipay" | "wechat";
  externalReference?: string;
  fetcher?: BillingApiFetcher;
}): Promise<BillingOrder> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher("/api/user/billing/orders", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${options.token}`
    },
    body: JSON.stringify({
      amount: options.amount,
      method: options.method,
      external_reference: options.externalReference
    })
  });
  if (!response.ok) {
    throw new Error("Failed to create billing order");
  }
  return mapBillingOrderDto(await response.json() as BillingOrderDto);
}

export async function confirmBillingOrder(options: {
  token: string;
  orderId: string;
  providerPaymentId: string;
  fetcher?: BillingApiFetcher;
}): Promise<{ order: BillingOrder; billing: BillingAccount }> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(`/api/user/billing/orders/${options.orderId}/confirm`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${options.token}`
    },
    body: JSON.stringify({ provider_payment_id: options.providerPaymentId })
  });
  if (!response.ok) {
    throw new Error("Failed to confirm billing order");
  }
  const payload = await response.json() as { order: BillingOrderDto; billing: BillingAccountDto };
  return {
    order: mapBillingOrderDto(payload.order),
    billing: mapBillingAccountDto(payload.billing)
  };
}

export async function purchaseCreditPackage(options: {
  token: string;
  package: BillingCreditPackage;
  fetcher?: BillingApiFetcher;
  now?: () => number;
}): Promise<{ order: BillingOrder; billing: BillingAccount }> {
  const now = options.now ?? Date.now;
  const timestamp = now();
  const order = await createBillingOrder({
    token: options.token,
    amount: options.package.amount + options.package.bonus,
    method: "stripe",
    externalReference: `checkout_${timestamp}`,
    fetcher: options.fetcher
  });
  return confirmBillingOrder({
    token: options.token,
    orderId: order.id,
    providerPaymentId: `pi_${order.id}_${timestamp}`,
    fetcher: options.fetcher
  });
}
