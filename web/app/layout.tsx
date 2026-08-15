import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "ReproClip Autonomous Company", description: "The zero-human growth company behind open-source ReproClip." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
