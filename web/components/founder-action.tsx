"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { API_URL } from "@/lib/api";

export function FounderAction({ path, label, body, className = "" }: { path: string; label: string; body?: object; className?: string }) {
  const router = useRouter(); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const run = async () => {
    let token = sessionStorage.getItem("reproclip_founder_token") || "";
    if (!token) token = window.prompt("Financial Human Approval Required\nEnter the founder approval token:") || "";
    if (!token) return;
    sessionStorage.setItem("reproclip_founder_token", token); setBusy(true); setError("");
    const response = await fetch(`${API_URL}${path}`, { method: "POST", headers: { "Content-Type": "application/json", "X-Founder-Token": token }, body: JSON.stringify(body || {}) });
    const payload = await response.json().catch(() => ({})); setBusy(false);
    if (!response.ok) { setError(payload.detail || payload.error || "Action failed"); return; }
    router.refresh();
  };
  return <div><button onClick={() => void run()} disabled={busy} className={`inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-[#d8ff57] px-5 text-xs font-black text-black transition hover:bg-white disabled:opacity-50 ${className}`}>{busy && <Loader2 size={15} className="animate-spin" />}{label}</button>{error && <p className="mt-2 max-w-sm text-[10px] leading-4 text-[#ff8e83]">{error}</p>}</div>;
}
