import type { Metadata } from "next";
import { DM_Sans, Poppins } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import Navigation from "../components/navigation";

const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-body" });
const poppins = Poppins({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-heading" });

export const metadata: Metadata = { title: "Cracker — Research Studio", description: "A thoughtful workspace for turning questions into structured research briefs." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${dmSans.variable} ${poppins.variable}`}><div className="app-shell">
    <header className="topbar">
      <Navigation />
      <div className="top-note"><span className="status-dot"/>Your thinking space</div>
    </header>
    {children}
    <footer><Link className="brand footer-brand" href="/" aria-label="Cracker home"><span className="brand-mark">c</span><span>cracker<span className="brand-dot">.</span></span></Link><span>Curiosity, with a little more structure.</span><span>RESEARCH STUDIO · EARLY DEMO</span></footer>
  </div></body></html>;
}
