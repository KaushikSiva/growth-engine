import { Check, CircleDashed, Play, Radio } from "lucide-react";
import { CompanyNav } from "@/components/brand";
import { api, CEOAction, CompanyEvent, Metrics } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DemoPage() {
  const [company, events] = await Promise.all([
    api<{ metrics: Metrics; current_decision: CEOAction | null }>("/api/company/metrics").catch(() => null),
    api<CompanyEvent[]>("/api/company/events?limit=100").catch(() => []),
  ]);
  const metrics = company?.metrics; const has = (actor: string, text?: string) => events.some((item) => item.actor === actor && (!text || item.action.toLowerCase().includes(text)));
  const stages = [
    ["Pioneer CEO identifies a strategy", Boolean(company?.current_decision), company?.current_decision?.decision.replaceAll("_", " ") || "Awaiting a validated Pioneer decision"],
    ["Terac recruits human creators", has("Terac", "launched"), `${metrics?.human_creators ?? 0} real creator records`],
    ["Creators produce content", has("Terac", "submission"), "Submission events ingested from Terac"],
    ["Founder approves creator work", has("Founder", "approved"), "Financial Human Approval Required"],
    ["Terac tests candidates with people", (metrics?.humans_surveyed ?? 0) > 0, `${metrics?.humans_surveyed ?? 0} persisted responses`],
    ["CEO chooses a winner", has("CEO") && (metrics?.humans_surveyed ?? 0) > 0, "Uses human preference and campaign economics"],
    ["Creative is distributed", (metrics?.social_posts ?? 0) > 0, `${metrics?.social_posts ?? 0} social post records`],
    ["Referral traffic arrives", (metrics?.landing_visits ?? 0) > 0, `${metrics?.landing_visits ?? 0} attributed visits`],
    ["Stripe receives $5 support", (metrics?.supporters ?? 0) > 0, `$${(metrics?.revenue ?? 0).toFixed(2)} webhook-verified revenue`],
    ["Pioneer reinvests based on results", has("CEO", "revenue"), "A new CEO action follows the payment event"],
  ] as const;
  return <main className="min-h-screen"><CompanyNav /><section className="mx-auto max-w-[1180px] px-5 pb-20 pt-10 lg:px-9"><div className="grid gap-8 border-b hairline pb-10 lg:grid-cols-[1fr_330px] lg:items-end"><div><div className="inline-flex items-center gap-2 rounded-full bg-[#171916] px-3 py-1.5 text-[10px] font-black uppercase tracking-[.16em] text-[#d8ff57]"><Play size={11} fill="currentColor" /> Judge demo</div><h1 className="display mt-5 text-[clamp(42px,6vw,76px)] font-bold leading-[.95]">One company.<br />Zero marketing employees.</h1><p className="mt-5 max-w-2xl text-[16px] leading-7 text-[#696c65]">This view never seeds success. Each check appears only when the corresponding persisted Pioneer, Terac, referral, founder, or Stripe event exists.</p></div><div className="rounded-[24px] bg-[#d8ff57] p-6"><div className="text-[9px] font-black uppercase tracking-[.16em]">Real company state</div><div className="display mt-3 text-5xl font-bold">${(metrics?.revenue ?? 0).toFixed(2)}</div><div className="mt-2 text-xs font-bold">Stripe revenue · {metrics?.supporters ?? 0} supporters</div></div></div><div className="mt-8 grid gap-3">{stages.map(([label, complete, detail], index) => <div key={label} className={`grid grid-cols-[46px_1fr_auto] items-center gap-4 rounded-2xl border p-4 transition ${complete ? "border-[#b6d84a]/35 bg-[#f1f8d7]" : "hairline bg-white/55"}`}><span className={`grid size-9 place-items-center rounded-xl font-mono text-xs font-bold ${complete ? "bg-[#d8ff57]" : "bg-[#e9eae4] text-[#8d9088]"}`}>{complete ? <Check size={16} strokeWidth={3} /> : String(index + 1).padStart(2, "0")}</span><div><strong className="text-sm">{label}</strong><p className="mt-1 text-xs text-[#777a72]">{detail}</p></div><span className={`hidden items-center gap-1 text-[9px] font-black uppercase tracking-wider sm:flex ${complete ? "text-[#5e7900]" : "text-[#9a9d95]"}`}>{complete ? <Check size={12} /> : <CircleDashed size={12} />} {complete ? "Persisted" : "Waiting"}</span></div>)}</div><div className="mt-10 rounded-[28px] bg-[#171916] p-7 text-white"><Radio className="text-[#d8ff57]" /><blockquote className="display mt-5 text-[clamp(24px,3.4vw,42px)] font-bold leading-tight">“Pioneer acts as CEO. Terac supplies humans on demand. Stripe proves revenue. Every result changes the next decision.”</blockquote><div className="mt-6 text-xs text-white/40">ReproClip remains open source. Human employees: 0.</div></div></section></main>;
}
