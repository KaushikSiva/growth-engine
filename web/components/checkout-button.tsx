"use client";

import { Coffee, Loader2 } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { API_URL } from "@/lib/api";

export function CheckoutButton() {
  const params = useSearchParams(); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const checkout = async () => {
    setBusy(true); setError("");
    let attribution: Record<string, string> = {};
    try { attribution = JSON.parse(params.get("attribution") || "{}"); } catch { attribution = {}; }
    const body = { referral_code: attribution.referral_code || params.get("ref"), campaign_id: attribution.campaign_id || params.get("campaign"), creator_id: attribution.creator_id || params.get("creator"), source: params.get("source") || "company-support" };
    const response = await fetch(`${API_URL}/api/stripe/create-checkout`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const result = await response.json().catch(() => ({})); setBusy(false);
    if (!response.ok) { setError(result.detail || "Stripe Checkout is unavailable."); return; }
    window.location.assign(result.checkout_url);
  };
  return <div><button onClick={() => void checkout()} disabled={busy} className="flex h-14 w-full items-center justify-center gap-3 rounded-2xl bg-[#d8ff57] text-sm font-black text-black shadow-[0_14px_40px_rgba(216,255,87,.18)] transition hover:-translate-y-0.5 hover:bg-white disabled:opacity-50">{busy ? <Loader2 size={18} className="animate-spin" /> : <Coffee size={19} />} {busy ? "Opening secure checkout…" : "Support ReproClip — $5"}</button>{error && <p className="mt-3 rounded-xl bg-[#3b211f] p-3 text-xs leading-5 text-[#ffb9ae]">{error}</p>}</div>;
}
