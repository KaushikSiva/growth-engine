import { Suspense } from "react";
import Link from "next/link";
import { ArrowLeft, CodeXml, Heart, LockKeyhole } from "lucide-react";
import { CheckoutButton } from "@/components/checkout-button";
import { Logo } from "@/components/brand";

export default function SupportPage() {
  return <main className="grid min-h-screen place-items-center bg-[#171916] p-5 text-white"><div className="w-full max-w-lg"><div className="flex items-center justify-between"><Logo inverse /><Link href="/company" className="flex items-center gap-2 text-xs font-bold text-white/45"><ArrowLeft size={14} /> Company</Link></div><div className="mt-14 rounded-[30px] border border-white/10 bg-white/[.055] p-7 shadow-2xl sm:p-9"><span className="grid size-12 place-items-center rounded-2xl bg-[#d8ff57] text-black"><Heart size={21} fill="currentColor" /></span><div className="mt-7 text-[10px] font-black uppercase tracking-[.16em] text-[#d8ff57]">Open source stays open</div><h1 className="display mt-3 text-[44px] font-bold leading-[.98]">If ReproClip saved you editing time, support the project.</h1><p className="mt-5 text-sm leading-6 text-white/55">This voluntary $5 payment supports development. It does not unlock code, features, or access.</p><div className="mt-7"><Suspense fallback={<div className="h-14 rounded-2xl bg-white/10" />}><CheckoutButton /></Suspense></div><div className="mt-5 flex items-center justify-center gap-2 text-[10px] text-white/35"><LockKeyhole size={12} /> Secure checkout hosted by Stripe</div></div><div className="mt-6 flex items-center justify-center gap-2 text-xs text-white/35"><CodeXml size={14} /> ReproClip remains open source.</div></div></main>;
}
