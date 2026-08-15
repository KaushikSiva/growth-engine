export const API_URL = process.env.NEXT_PUBLIC_API_URL || process.env.COMPANY_API_URL || "http://localhost:8000";

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { ...options, cache: "no-store" });
  if (!response.ok) throw new Error((await response.text()) || `Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export interface Metrics {
  revenue: number; supporters: number; campaigns: number; human_creators: number; humans_surveyed: number;
  social_posts: number; landing_visits: number; conversion_rate: number; human_employees: number; terac_spend: number;
  infrastructure_cost: number | null; gross_contribution: number | null; roas: number | null; cac: number | null;
}

export interface CEOAction {
  id: string; summary: string; decision: string; target_audience: string; creative_style: string; platform_priority: string[];
  budget: number; reasoning_summary: string; next_actions: string[]; provider: string; model: string; created_at: string;
}

export interface CompanyEvent { id: string; actor: string; action: string; entity_type?: string; entity_id?: string; metadata: Record<string, unknown>; created_at: string }

export interface Campaign {
  id: string; name: string; objective: string; audience: string; creative_style: string; hook: string; platforms: string[]; brief: string;
  budget_usd: number; status: string; current_decision?: string; referral_code?: string; referral_url?: string; created_at: string; updated_at: string;
  performance: { visits?: number; stripe_conversions?: number; revenue?: number; conversion_rate?: number; terac_cost?: number; gross_contribution?: number; human_preference_score?: number | null };
  creators?: Array<Record<string, any>>; studies?: Array<Record<string, any>>; creatives?: Array<Record<string, any>>;
}
