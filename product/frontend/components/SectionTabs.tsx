"use client";

export type TabOption = {
  id: string;
  label: string;
};

type Props = {
  tabs: TabOption[];
  active: string;
  onChange: (id: string) => void;
};

export default function SectionTabs({ tabs, active, onChange }: Props) {
  return (
    <div className="section-tabs">
      {tabs.map((t) => (
        <button
          key={t.id}
          type="button"
          className={t.id === active ? "section-tab active" : "section-tab"}
          onClick={() => onChange(t.id)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
