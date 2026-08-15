"use client";

import { CheckCircle2, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";

export function PaymentStatus({ sessionId }: { sessionId: string }) {
  const [state, setState] = useState<"checking" | "paid" | "pending">("checking");
  useEffect(() => { let attempts = 0; const check = async () => { const response = await fetch(`${API_URL}/api/stripe/session/${encodeURIComponent(sessionId)}`, { cache: "no-store" }); if (response.ok && (await response.json()).paid) { setState("paid"); return; } attempts += 1; if (attempts < 10) window.setTimeout(check, 1200); else setState("pending"); }; void check(); }, [sessionId]);
  if (state === "checking") return <div className="flex items-center gap-2 text-sm text-white/55"><Loader2 size={17} className="animate-spin" /> Verifying the signed Stripe webhook…</div>;
  if (state === "paid") return <div className="flex items-center gap-2 text-sm font-bold text-[#d8ff57]"><CheckCircle2 size={18} /> Payment verified and added to company revenue.</div>;
  return <div className="text-sm text-white/55">Checkout returned successfully. The dashboard updates only after Stripe&apos;s verified webhook arrives.</div>;
}
