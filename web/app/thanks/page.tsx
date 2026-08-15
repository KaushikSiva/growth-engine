import Link from "next/link";
import { ArrowRight, Heart } from "lucide-react";
import { PaymentStatus } from "@/components/payment-status";

export default async function ThanksPage({ searchParams }: { searchParams: Promise<{ session_id?: string }> }) {
  const { session_id } = await searchParams;
  return <main className="grid min-h-screen place-items-center bg-[#171916] p-5 text-white"><div className="max-w-xl text-center"><span className="mx-auto grid size-16 place-items-center rounded-[22px] bg-[#d8ff57] text-black"><Heart size={26} fill="currentColor" /></span><h1 className="display mt-7 text-6xl font-bold">Thank you.</h1><p className="mx-auto mt-5 max-w-md text-[16px] leading-7 text-white/55">Your support helps keep ReproClip open and gives its autonomous company one real signal about what is working.</p><div className="mt-8 rounded-2xl border border-white/10 bg-white/5 p-5">{session_id ? <PaymentStatus sessionId={session_id} /> : <p className="text-sm text-white/55">No Checkout session was supplied.</p>}</div><Link href="/company" className="mt-8 inline-flex h-12 items-center gap-2 rounded-xl bg-white px-5 text-xs font-black text-black">Watch the company learn <ArrowRight size={15} /></Link></div></main>;
}
