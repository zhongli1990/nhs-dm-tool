import "./globals.css";
import type { ReactNode } from "react";
import AppNav from "../components/AppNav";

export const metadata = {
  title: "NHS Data Migration Control Plane",
  description: "PAS/EPR migration engineering workspace"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <header className="app-topbar">
            <div>
              <div className="title">NHS Migration Control Plane</div>
              <div className="subtitle">Enterprise PAS to EPR Data Migration Lifecycle</div>
            </div>
            <div className="topbar-meta">Mission-critical mode</div>
          </header>
          <div className="app-main">
            <AppNav />
            <section className="content">{children}</section>
          </div>
        </div>
      </body>
    </html>
  );
}
