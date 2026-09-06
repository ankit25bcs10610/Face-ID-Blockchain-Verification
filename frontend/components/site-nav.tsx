"use client";

import { Moon, ShieldCheck, Sun } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import type { ConnectionState } from "@/lib/types";

function useTheme() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("tracechain-theme");
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
      localStorage.setItem("tracechain-theme", next);
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
        <span className="seal">
          <ShieldCheck size={18} />
        </span>
        <div>
          <span className="name">
            Trace<b>Chain</b> AI
          </span>
          <small className="tag">Identify · Discover · Verify</small>
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
