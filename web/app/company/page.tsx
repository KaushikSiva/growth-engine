import { AlertTriangle, ArrowUpRight, Bot, CheckCircle2, Radio, Zap } from "lucide-react";
import { CompanyNav } from "@/components/brand";
import { FounderAction } from "@/components/founder-action";
import { AutoRefresh } from "@/components/auto-refresh";
import { api, CEOAction, CompanyEvent, Metrics } from "@/lib/api";

export const dynamic = "force-dynamic";

const metricLabels: Array<[keyof Metrics, string, "money" | "percent" | "number"]> = [
  ["revenue", "Revenue", "money"], ["supporters", "Supporters", "number"], ["campaigns", "Campaigns", "number"], ["human_creators", "Human creators", "number"],
  ["humans_surveyed", "Humans surveyed", "number"], ["social_posts", "Social posts", "number"], ["landing_visits", "Landing visits", "number"], ["conversion_rate", "Conversion", "percent"],
];
const format = (value: number, type: string) => type === "money" ? `$${value.toFixed(2)}` : type === "percent" ? `${(value * 100).toFixed(1)}%` : value.toLocaleString();

export default async function CompanyPage() {
  const [data, events, health] = await Promise.all([
    api<{ metrics: Metrics; current_decision: CEOAction | null; campaign_performance: Array<Record<string, unknown>> }>("/api/company/metrics").catch(() => null),
    api<CompanyEvent[]>("/api/company/events?limit=30").catch(() => []),
    api<{ integrations: Record<string, string> }>("/health").catch((): { integrations: Record<string, string> } => ({ integrations: {} })),
  ]);
  const metrics = data?.metrics ?? { revenue: 0, supporters: 0, campaigns: 0, human_creators: 0, humans_surveyed: 0, social_posts: 0, landing_visits: 0, conversion_rate: 0, human_employees: 0, terac_spend: 0, infrastructure_cost: null, gross_contribution: null, roas: null, cac: null };
  const coreReady = ["stripe", "pioneer", "terac"].every((key) => health.integrations[key] === "configured");
  return <main className="min-h-screen"><AutoRefresh /><CompanyNav />
    <section className="mx-auto max-w-[1440px] px-5 pb-20 pt-10 lg:px-9">
      <div className="grid gap-8 border-b hairline pb-10 lg:grid-cols-[1.35fr_.65fr] lg:items-end"><div><div className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-[10px] font-black uppercase tracking-[.16em] ${coreReady ? "bg-[#d8ff57] text-black" : "bg-[#ffe2dc] text-[#913d34]"}`}><Radio size={12} className={coreReady ? "animate-pulse" : ""} /> {coreReady ? "Autonomy mode: on" : "Autonomy mode: setup required"}</div><h1 className="display mt-5 max-w-4xl text-[clamp(44px,6vw,82px)] font-bold leading-[.94]">ReproClip<br />Autonomous Company</h1><p className="mt-6 max-w-2xl text-[17px] leading-7 text-[#62665d]">Pioneer decides. Terac hires real human creators and testers. Stripe measures voluntary support. Every real result changes the next campaign.</p></div><div className="rounded-[26px] bg-[#171916] p-6 text-white shadow-[0_22px_70px_rgba(20,22,18,.17)]"><div className="text-[10px] font-black uppercase tracking-[.16em] text-white/40">Primary company objective</div><p className="display mt-4 text-[25px] font-bold leading-tight">Generate real revenue while growing open-source ReproClip with an on-demand human workforce.</p><div className="mt-6 flex items-center justify-between border-t border-white/10 pt-4 text-xs"><span className="text-white/45">Human employees</span><strong className="text-2xl text-[#d8ff57]">0</strong></div></div></div>

      <div className="mt-8 grid grid-cols-2 border-l border-t hairline md:grid-cols-4">{metricLabels.map(([key, label, type]) => <div key={key} className="border-b border-r hairline bg-white/45 p-5"><div className="text-[10px] font-black uppercase tracking-[.14em] text-[#85887f]">{label}</div><div className="display tabular mt-3 text-[clamp(29px,3vw,43px)] font-bold">{format(Number(metrics[key] ?? 0), type)}</div></div>)}</div>

      <div className="mt-10 grid gap-6 lg:grid-cols-[.9fr_1.1fr]">
        <section className="overflow-hidden rounded-[26px] bg-[#171916] text-white"><div className="flex items-center justify-between border-b border-white/10 px-6 py-5"><div className="flex items-center gap-2 text-sm font-bold"><Bot size={18} className="text-[#d8ff57]" /> CEO current decision</div><span className="rounded-full border border-white/15 px-2 py-1 text-[9px] font-black uppercase tracking-wider text-white/50">Pioneer</span></div>{data?.current_decision ? <div className="p-6"><div className="text-[10px] font-black uppercase tracking-[.15em] text-[#d8ff57]">{data.current_decision.decision.replaceAll("_", " ")}</div><h2 className="display mt-3 text-3xl font-bold leading-tight">{data.current_decision.summary}</h2><div className="mt-6 border-l-2 border-[#d8ff57] pl-4"><div className="text-[9px] font-black uppercase tracking-wider text-white/35">Why</div><p className="mt-2 text-sm leading-6 text-white/65">{data.current_decision.reasoning_summary}</p></div><div className="mt-6 space-y-2">{data.current_decision.next_actions.map((item) => <div key={item} className="flex gap-2 text-xs text-white/70"><ArrowUpRight size={14} className="mt-0.5 shrink-0 text-[#d8ff57]" />{item}</div>)}</div></div> : <div className="p-6"><AlertTriangle size={24} className="text-[#ffb9ae]" /><h2 className="display mt-4 text-2xl font-bold">No CEO decision yet.</h2><p className="mt-2 text-sm leading-6 text-white/45">Connect Pioneer, then run the CEO against the real zero-state or live Stripe and Terac results. Nothing is seeded.</p></div>}<div className="border-t border-white/10 p-5"><FounderAction path="/api/company/ceo/run" label={data?.current_decision ? "Run next CEO review" : "Run first CEO review"} /></div></section>

        <section className="rounded-[26px] border hairline bg-white/70"><div className="flex items-center justify-between border-b hairline px-6 py-5"><div><h2 className="display text-xl font-bold">Live company activity</h2><p className="mt-1 text-xs text-[#81847b]">Persisted business events only</p></div><Zap size={18} className="text-[#89ad00]" /></div><div className="max-h-[560px] overflow-y-auto p-2">{events.length ? events.map((event) => <div key={event.id} className="grid grid-cols-[58px_70px_1fr] gap-3 border-b hairline px-4 py-3 text-xs last:border-0"><time className="font-mono text-[#989b92]">{new Date(event.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time><strong className={event.actor === "Stripe" ? "text-[#598100]" : event.actor === "Terac" ? "text-[#6e56a8]" : "text-[#30332e]"}>{event.actor}</strong><span className="leading-5 text-[#63665f]">{event.action}</span></div>) : <div className="grid min-h-64 place-items-center p-8 text-center"><div><Radio className="mx-auto text-[#b4b7ae]" /><p className="mt-3 text-sm font-bold">Waiting for the first real event</p><p className="mt-1 text-xs text-[#85887f]">Open a Stripe checkout or run the Pioneer CEO.</p></div></div>}</div></section>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-4">{Object.entries(health.integrations).map(([name, state]) => <div key={name} className="flex items-center justify-between rounded-2xl border hairline bg-white/55 p-4"><span className="text-xs font-bold capitalize">{name}</span><span className={`flex items-center gap-1 text-[9px] font-black uppercase tracking-wider ${state === "configured" ? "text-[#618100]" : "text-[#9a4b42]"}`}>{state === "configured" ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}{state}</span></div>)}</div>
    </section>
  </main>;
}
