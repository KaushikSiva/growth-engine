"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export function AutoRefresh({ everyMs = 5000 }: { everyMs?: number }) {
  const router = useRouter();
  useEffect(() => { const timer = window.setInterval(() => router.refresh(), everyMs); return () => window.clearInterval(timer); }, [everyMs, router]);
  return null;
}
