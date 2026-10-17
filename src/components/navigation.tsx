"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const destinations = [
  { label: "Home", href: "/" },
  { label: "New Chat", href: "/chat/new" },
  { label: "Library", href: "/library" },
  { label: "About", href: "/about" },
];

export default function Navigation() {
  const pathname = usePathname();

  return <>
    <Link className="brand" href="/" aria-label="Cracker home"><span className="brand-mark">c</span><span>cracker<span className="brand-dot">.</span></span></Link>
    <nav aria-label="Main navigation">
      {destinations.map(({ label, href }) => {
        const active = pathname === href;
        return <Link key={href} className={active ? "nav-current" : undefined} href={href} aria-current={active ? "page" : undefined}>{label}</Link>;
      })}
    </nav>
  </>;
}
