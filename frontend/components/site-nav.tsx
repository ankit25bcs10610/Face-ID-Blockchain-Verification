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
          <stop stopColor="#bbf7d0" />
          <stop offset="0.32" stopColor="#4ade80" />
          <stop offset="1" stopColor="#15803d" />
        </linearGradient>
      </defs>
      <path className="trace-shield outer" d="M32 5.5 51.5 16v14.2c0 12.5-7.2 22-19.5 28.3C19.7 52.2 12.5 42.7 12.5 30.2V16L32 5.5Z" />
      <path className="trace-orbit" d="M17.5 34.5c1-8.4 7.1-14.8 14.5-14.8 8 0 14.3 6.5 14.3 14.7 0 8.1-6.3 14.7-14.3 14.7-4.6 0-8.7-2.2-11.4-5.8" />
      <circle className="trace-lens" cx="32" cy="34.3" r="8.2" />
      <path className="trace-core" d="M26.8 34.7 30.7 38.5 38.2 30" />
      <path className="trace-spark" d="M48.5 18.5v5m-2.5-2.5h5" />
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
