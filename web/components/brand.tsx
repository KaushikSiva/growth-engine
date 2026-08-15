import Link from "next/link";
import { Activity, CircleDollarSign, Megaphone, PlayCircle } from "lucide-react";

export function Logo({ inverse = false }: { inverse?: boolean }) { return <Link href="/company" className={`flex items-center gap-3 ${inverse ? "text-white" : "text-[#171916]"}`}><span className="grid size-10 place-items-center rounded-[13px] bg-[#d8ff57] shadow-[inset_0_0_0_1px_rgba(0,0,0,.1)]"><span className="size-4 rounded-[4px] border-[3px] border-[#171916]" /></span><span className="display text-[22px] font-bold">ReproClip</span></Link>; }

export function CompanyNav() {
  return <header className="sticky top-0 z-30 border-b hairline bg-[#f7f7f2]/90 backdrop-blur-xl"><div className="mx-auto flex h-[72px] max-w-[1440px] items-center justify-between px-5 lg:px-9"><Logo /><nav className="flex items-center gap-1 text-xs font-bold"><Link href="/company" className="flex items-center gap-2 rounded-xl px-3 py-2.5 hover:bg-black/5"><Activity size={15} /> Company</Link><Link href="/company/campaigns" className="flex items-center gap-2 rounded-xl px-3 py-2.5 hover:bg-black/5"><Megaphone size={15} /> Campaigns</Link><Link href="/company/financials" className="hidden items-center gap-2 rounded-xl px-3 py-2.5 hover:bg-black/5 sm:flex"><CircleDollarSign size={15} /> Financials</Link><Link href="/demo" className="flex items-center gap-2 rounded-xl bg-[#171916] px-4 py-2.5 text-white"><PlayCircle size={15} className="text-[#d8ff57]" /> Demo</Link></nav></div></header>;
}
