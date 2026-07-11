export type PolicyName = "fifo_routine" | "always_expedite" | "never_inspect" | "random" | "risk_tier";

export type ScenarioRequest = {
  snapshotDate: string;
  dailyCapacity: number;
  accessProbability: number;
  policy: PolicyName;
  seed: number;
};

export type PolicyResult = {
  policy: PolicyName;
  snapshotDate: string;
  isCounterfactual: true;
  totalReward: number;
  inspected: number;
  actionableFound: number;
  actionableMissed: number;
  meanDelayDays: number;
  maxQueueDepth: number;
  groupMetrics: Record<string, { arrivals: number; inspected: number; serviceRate: number; meanDelayDays: number }>;
  limitations: string[];
};

export async function runPolicyScenario(request: ScenarioRequest): Promise<PolicyResult> {
  const baseUrl = process.env.NEXT_PUBLIC_POLICY_API_BASE_URL;
  if (!baseUrl) {
    throw new Error("Policy API is not configured. Use the local simulated preview instead.");
  }
  const response = await fetch(`${baseUrl}/v1/policy-runs`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Policy API request failed: ${response.status}`);
  }
  return (await response.json()) as PolicyResult;
}
