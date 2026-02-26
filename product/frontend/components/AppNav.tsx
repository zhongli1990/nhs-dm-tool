"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const MENU = [
  { header: "Overview", items: [{ href: "/", label: "Dashboard" }] },
  {
    header: "Design",
    items: [
      { href: "/schemas", label: "Schemas" },
      { href: "/mappings", label: "Mappings" },
      { href: "/connectors", label: "Connectors" },
    ],
  },
  {
    header: "Execution",
    items: [
      { href: "/lifecycle", label: "Lifecycle" },
      { href: "/runs", label: "Runs" },
      { href: "/quality", label: "Quality" },
    ],
  },
  { header: "Ops", items: [{ href: "/users", label: "Roles" }] },
];

export default function AppNav() {
  const pathname = usePathname();
  return (
    <aside className="sidebar">
      {MENU.map((group) => (
        <div key={group.header} className="menu-group">
          <div className="menu-header">{group.header}</div>
          {group.items.map((it) => {
            const active = pathname === it.href || pathname.startsWith(`${it.href}/`);
            return (
              <Link key={it.href} href={it.href} className={active ? "menu-link active" : "menu-link"}>
                {it.label}
              </Link>
            );
          })}
        </div>
      ))}
    </aside>
  );
}
