"use client";

import { Moon, Sun } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import type { ConnectionState } from "@/lib/types";

function useTheme() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("orynex-theme");
      if (stored === "light" || stored === "dark") setTheme(stored);
    } catch {
      /* localStorage unavailable */
    }
  }, []);

  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    try {
    localStorage.setItem("orynex-theme", next);
    } catch {
      /* localStorage unavailable */
    }
  };

  return { theme, toggle };
}

function useHealthPills() {
  const [api, setApi] = useState<ConnectionState>("checking");
  const [search, setSearch] = useState<ConnectionState>("checking");
  const [chain, setChain] = useState<ConnectionState>("checking");

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then((health) => {
        if (cancelled) return;
        const ok = health.status === "healthy" || health.status === "degraded";
        setApi(ok ? "connected" : "disconnected");
        setSearch(health.components?.search_service === "available" ? "connected" : "disconnected");
        setChain(health.components?.blockchain === "available" ? "connected" : "disconnected");
      })
      .catch(() => {
        if (cancelled) return;
        setApi("disconnected");
        setSearch("disconnected");
        setChain("disconnected");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { api, search, chain };
}

function Pill({ label, state }: { label: string; state: ConnectionState }) {
  const cls = state === "connected" ? "on" : state === "checking" ? "checking" : "off";
  return (
    <span className="pill">
      <i className={cls} />
      {label}
    </span>
  );
}

function TraceLogo() {
  return (
    <svg className="trace-logo" viewBox="0 0 64 64" role="img" aria-label="ORYNEX AI identity mark">
      <defs>
        <linearGradient id="trace-gold" x1="8" y1="7" x2="55" y2="58" gradientUnits="userSpaceOnUse">
          <stop stopColor="#fff0b0" />
          <stop offset="0.32" stopColor="#f7bd43" />
          <stop offset="1" stopColor="#b56c13" />
        </linearGradient>
        <linearGradient id="trace-face" x1="24" y1="17" x2="42" y2="48" gradientUnits="userSpaceOnUse">
          <stop stopColor="#fff3bc" />
          <stop offset="1" stopColor="#c47b1d" />
        </linearGradient>
        <filter id="trace-glow" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="1.1" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
      <path className="trace-shield outer" d="M32 4 54 16v16c-1.8 13-9.2 23.2-22 29C19.2 55.2 11.8 45 10 32V16L32 4Z" />
      <path className="trace-orbit halo" d="M14 36c1-14 12-24 25-22 10 1.6 16 10.8 13 19.8-3.5 10.8-17.4 16-28.4 10.6" filter="url(#trace-glow)" />
      <circle className="trace-lens" cx="32" cy="31" r="11.5" />
      <path className="trace-core" d="m25 25 7 12 7-12m-3.2 7.2h-7.6" />
      <path className="trace-face" d="M39 21.2c3.8 2 5.3 5.4 4.6 9.1l-1.8 1.4.7 2-2.1 1.1.1 2-2.7 1.4-2.1-1.8-1.4-3.8 1.4-6.4 3.3-5Z" />
      <path className="trace-mesh" d="m35 26 5 2m-6 3 6 1m-5 3 4 1m-3-10 3 7" />
      <path className="trace-orbit" d="M4 43c8.8 11.2 23 13.4 36.4 5.8C52.4 41.9 59.6 29.8 53 19" filter="url(#trace-glow)" />
      <circle className="trace-node" cx="7" cy="42" r="3" />
      <circle className="trace-node" cx="20" cy="53" r="2.6" />
      <circle className="trace-node" cx="51" cy="18" r="2.7" />
      <circle className="trace-node small" cx="27" cy="49" r="1.7" />
      <path className="trace-spark" d="m10 20 3 3m-3 0 3-3" />
    </svg>
  );
}

export default function SiteNav() {
  const pathname = usePathname();
  const { theme, toggle } = useTheme();
  const { api, search, chain } = useHealthPills();

  const links = [
    { href: "/", label: "Home" },
    { href: "/evidence", label: "Evidence" },
    { href: "/verify", label: "Verify" }
  ];

  return (
    <header className="site-nav">
      <div className="brandblock">
        <span className="seal" aria-hidden="true"><TraceLogo /></span>
        <div>
          <span className="name">
            ORY<span>NEX</span> AI
          </span>
          <small className="tag">Identify <i>•</i> Discover <i>•</i> Verify</small>
        </div>
      </div>
      <nav>
        {links.map((link) => (
          <Link key={link.href} href={link.href} className={pathname === link.href ? "active" : ""}>
            {link.label}
          </Link>
        ))}
      </nav>
      <div className="nav-trail">
        <Pill label="API" state={api} />
        <Pill label="Search" state={search} />
        <Pill label="Chain" state={chain} />
        <button className="theme-btn" onClick={toggle} aria-label="Toggle color theme">
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  );
}
