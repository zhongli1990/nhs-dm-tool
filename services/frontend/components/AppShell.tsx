"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import AppNav from "./AppNav";
import ThemeModeSwitch from "./ThemeModeSwitch";
import AuthToolbar from "./AuthToolbar";
import { buildApiUrl, getTokenFromBrowser } from "../lib/api";
import { APP_VERSION } from "../lib/version";

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const authOnly = pathname === "/login" || pathname === "/register";
  const [authChecked, setAuthChecked] = useState(authOnly);
  const [authorized, setAuthorized] = useState(authOnly);

  useEffect(() => {
    if (authOnly) {
      setAuthChecked(true);
      setAuthorized(true);
      return;
    }
    let cancelled = false;
    async function verify() {
      const token = getTokenFromBrowser();
      if (!token) {
        localStorage.removeItem("dmm_access_token");
        localStorage.removeItem("dmm_user");
        document.cookie = "dmm_access_token=; Max-Age=0; path=/";
        window.location.href = "/login";
        return;
      }
      try {
        const res = await fetch(buildApiUrl("/api/auth/me"), {
          cache: "no-store",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("unauthorized");
        if (!cancelled) {
          setAuthorized(true);
          setAuthChecked(true);
        }
      } catch {
        localStorage.removeItem("dmm_access_token");
        localStorage.removeItem("dmm_user");
        document.cookie = "dmm_access_token=; Max-Age=0; path=/";
        window.location.href = "/login";
      }
    }
    setAuthChecked(false);
    setAuthorized(false);
    verify();
    return () => {
      cancelled = true;
    };
  }, [authOnly, pathname]);

  if (authOnly) {
    return <>{children}</>;
  }

  if (!authChecked || !authorized) {
    return (
      <div className="app-shell">
        <section className="card">
          <div className="muted">Validating secure session...</div>
        </section>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="app-topbar">
        <div>
          <div className="title">OpenLI DMM</div>
          <div className="subtitle">Data Migration Manager - Enterprise EPR Migration Lifecycle Management</div>
        </div>
        <div className="topbar-actions">
          <ThemeModeSwitch />
          <AuthToolbar />
          <div className="topbar-meta">v{APP_VERSION}</div>
          <div className="topbar-meta">Mission-critical mode</div>
        </div>
      </header>
      <div className="app-main">
        <AppNav />
        <section className="content">{children}</section>
      </div>
    </div>
  );
}
