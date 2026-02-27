import "./globals.css";
import type { ReactNode } from "react";
import AppShell from "../components/AppShell";

export const metadata = {
  title: "OpenLI DMM",
  description: "OpenLI Data Migration Manager for NHS enterprise PAS/EPR migrations",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
