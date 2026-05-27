import Link from "next/link";
import { labs, type Lab, type LabStatus } from "@/data/labs";

const STATUS_LABEL: Record<LabStatus, string> = {
  operational: "OPERATIONAL",
  prototype: "PROTOTYPE",
  provisioning: "PROVISIONING",
};

const STATUS_DOT: Record<LabStatus, string> = {
  operational:
    "bg-emerald-300 shadow-[0_0_8px_rgba(110,231,183,0.9)]",
  prototype: "bg-amber-300 shadow-[0_0_8px_rgba(252,211,77,0.9)]",
  provisioning: "bg-cyan-300 shadow-[0_0_8px_rgba(57,243,255,0.9)]",
};

const STATUS_PILL: Record<LabStatus, string> = {
  operational:
    "text-emerald-300 border-emerald-300/40 bg-emerald-300/10",
  prototype: "text-amber-300 border-amber-300/40 bg-amber-300/10",
  provisioning: "text-cyan-200 border-cyan-200/40 bg-cyan-200/10",
};

const HIGHLIGHTED_STACKS = new Set(["Next.js", "Redux", "Socket.io", "MongoDB"]);

function LabTile({ lab }: { lab: Lab }) {
  const disabled = lab.href == null;
  const isExternal = lab.href != null && /^https?:\/\//i.test(lab.href);

  const card = (
    <div
      className={[
        "group relative flex h-full flex-col overflow-hidden rounded-xl",
        "border border-cyan-300/40",
        "bg-[linear-gradient(180deg,rgba(2,30,45,0.55),rgba(0,10,20,0.72))]",
        "p-4 transition-all duration-300",
        disabled
          ? "cursor-pointer"
          : "hover:-translate-y-0.5 hover:border-cyan-200 hover:shadow-[0_0_18px_rgba(69,229,255,0.28)]",
      ].join(" ")}
    >
      {/* scan-line sweep on hover */}
      <div className="pointer-events-none absolute inset-x-0 -top-16 h-16 bg-gradient-to-b from-transparent via-cyan-200/15 to-transparent opacity-0 transition-all duration-700 group-hover:top-[calc(100%+4rem)] group-hover:opacity-100" />

      {/* header row: dot + id + status pill */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[lab.status]}`}
          />
          <span className="text-[10px] tracking-[0.14em] text-cyan-200/70">
            {lab.id}
          </span>
        </div>
        <span
          className={`rounded-full border px-2 py-0.5 text-[9px] tracking-[0.12em] ${STATUS_PILL[lab.status]}`}
        >
          {STATUS_LABEL[lab.status]}
        </span>
      </div>

      {/* title + tagline */}
      <h3 className="mt-3 text-sm font-medium tracking-wide text-cyan-50">
        {lab.title}
      </h3>
      <p className="mt-1 text-xs leading-relaxed text-cyan-100/70">
        {lab.tagline}
      </p>

      {/* tech stack tags */}
      <div className="mt-auto flex flex-wrap gap-1.5 pt-3">
        {lab.stack.map((tech) => (
          <span
            key={tech}
            className={[
              "rounded-full border px-2 py-0.5 text-[10px] transition-colors",
              HIGHLIGHTED_STACKS.has(tech)
                ? "border-cyan-200/85 bg-cyan-200/25 font-semibold text-cyan-50 shadow-[0_0_10px_rgba(103,232,249,0.35)]"
                : "border-cyan-300/30 bg-cyan-300/5 text-cyan-100/75",
            ].join(" ")}
          >
            {tech}
          </span>
        ))}
      </div>

      {/* CTA */}
      <div className="mt-3 flex items-center justify-end border-t border-cyan-300/20 pt-2">
        <span
          className={[
            "text-[11px] tracking-[0.16em] transition-colors duration-300",
            disabled
              ? "text-cyan-200/45 group-hover:text-cyan-200/70"
              : "text-cyan-100 group-hover:text-white",
          ].join(" ")}
        >
          {disabled ? "STANDBY" : isExternal ? "LAUNCH ↗" : "LAUNCH ▸"}
        </span>
      </div>
    </div>
  );

  if (disabled) {
    return (
      <div
        className="text-left opacity-80"
        aria-label={`${lab.title} — not yet available`}
      >
        {card}
      </div>
    );
  }

  if (isExternal) {
    return (
      <a
        href={lab.href!}
        target="_blank"
        rel="noreferrer noopener"
        aria-label={`${lab.title} — opens in new tab`}
      >
        {card}
      </a>
    );
  }

  return <Link href={lab.href!}>{card}</Link>;
}

function GhostTile() {
  return (
    <div className="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-cyan-300/20 bg-[linear-gradient(180deg,rgba(2,30,45,0.2),rgba(0,10,20,0.3))] p-4 text-center">
      <span className="text-[10px] tracking-[0.18em] text-cyan-200/30">
        EMPTY SLOT
      </span>
      <span className="mt-1.5 text-xs text-cyan-100/30">
        More modules inbound...
      </span>
    </div>
  );
}

export default function LabsPanel() {
  return (
    <div className="monitor-screen">
      <div className="monitor-grid-overlay" />

      <div className="monitor-header">
        <span className="monitor-dot" />
        <p className="monitor-title">LABS // MICRO-APPS</p>
        <span className="monitor-scan">
          {labs.length} MODULE{labs.length !== 1 && "S"} LOADED
        </span>
      </div>

      <div className="relative z-10 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {labs.map((lab) => (
          <LabTile key={lab.slug} lab={lab} />
        ))}
        <GhostTile />
      </div>
    </div>
  );
}
