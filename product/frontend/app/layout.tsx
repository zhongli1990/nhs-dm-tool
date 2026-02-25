import "./globals.css";
import Link from "next/link";
import type { ReactNode } from "react";

export const metadata = {
  title: "NHS Data Migration Control Plane",
  description: "PAS/EPR migration engineering workspace"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="topbar">
            <div>
              <div className="title">NHS Migration Control Plane</div>
              <div className="subtitle">QVH PAS Migration Productization Workspace</div>
            </div>
            <nav className="nav">
              <Link href="/">Dashboard</Link>
              <Link href="/schemas">Schemas</Link>
              <Link href="/mappings">Mappings</Link>
              <Link href="/runs">Runs</Link>
              <Link href="/connectors">Connectors</Link>
              <Link href="/users">Users</Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
