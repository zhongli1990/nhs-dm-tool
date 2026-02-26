"use client";

import { useEffect, useState } from "react";

type ThemeMode = "light" | "dark" | "system";

const KEY = "dm_theme_mode";

function resolveTheme(mode: ThemeMode): "light" | "dark" {
  if (mode !== "system") return mode;
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function ThemeModeSwitch() {
  const [mode, setMode] = useState<ThemeMode>("system");
  const [resolved, setResolved] = useState<"light" | "dark">("light");

  useEffect(() => {
    const saved = (localStorage.getItem(KEY) as ThemeMode | null) || "system";
    setMode(saved);
  }, []);

  useEffect(() => {
    const apply = () => {
      const finalTheme = resolveTheme(mode);
      setResolved(finalTheme);
      document.documentElement.setAttribute("data-theme", finalTheme);
    };
    apply();
    if (mode !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, [mode]);

  function onChange(value: string) {
    const next = value as ThemeMode;
    setMode(next);
    localStorage.setItem(KEY, next);
  }

  return (
    <div className="theme-switch">
      <span className="muted">Theme</span>
      <select value={mode} onChange={(e) => onChange(e.target.value)} aria-label="Theme mode">
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
      <span className="pill">{resolved}</span>
    </div>
  );
}
