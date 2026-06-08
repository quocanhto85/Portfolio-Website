import Link from "next/link";
import { labs, type Lab, type LabStatus } from "@/data/labs";

const STATUS_LABEL: Record<LabStatus, string> = {
  operational: "OPERATIONAL",
  prototype: "PROTOTYPE",
  provisioning: "PROVISIONING",
};

const STATUS_DOT: Record<LabStatus, string> = {
  operational: "bg-[#39ff9e] shadow-[0_0_9px_#39ff9e]",
  prototype: "bg-[#ffc24b] shadow-[0_0_9px_#ffc24b]",
  provisioning: "bg-[#22e6ff] shadow-[0_0_9px_#22e6ff]",
};

const STATUS_PILL: Record<LabStatus, string> = {
  operational: "text-[#39ff9e] border-[rgba(57,255,158,0.4)] bg-[rgba(57,255,158,0.08)]",
  prototype: "text-[#ffc24b] border-[rgba(255,194,75,0.4)] bg-[rgba(255,194,75,0.08)]",
  provisioning: "text-[#22e6ff] border-[rgba(34,230,255,0.4)] bg-[rgba(34,230,255,0.08)]",
};

// Total module bays in the console — ghosts fill the unused capacity.
const MODULE_BAYS = 4;

function LabTile({ lab }: { lab: Lab }) {
  const disabled = lab.href == null;
  const isExternal = lab.href != null && /^https?:\/\//i.test(lab.href);

  const card = (
    <div
      className={[
        "hud-sweep-tile group flex h-full flex-col rounded-[10px] border border-[rgba(40,200,230,0.22)]",
        "bg-[linear-gradient(180deg,rgba(4,24,36,0.55),rgba(2,9,17,0.66))] p-3.5",
        disabled
          ? ""
          : "hover:-translate-y-[3px] hover:border-[rgba(60,225,255,0.55)] hover:shadow-[0_0_22px_rgba(34,230,255,0.22)]",
      ].join(" ")}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-mono text-[0.6rem] tracking-[0.14em] text-[#5e8f99]">
          <span className={`h-1.5 w-1.5 rounded-full hud-dot-pulse ${STATUS_DOT[lab.status]}`} />
          {lab.id}
        </div>
        <span
          className={`rounded-full border px-2 py-0.5 font-mono text-[0.55rem] tracking-[0.12em] ${STATUS_PILL[lab.status]}`}
        >
          {STATUS_LABEL[lab.status]}
        </span>
      </div>

      <h3 className="mt-2.5 text-[0.98rem] font-bold tracking-wide text-[#e6fbff]">
        {lab.title}
      </h3>
      <p className="mt-1.5 text-[0.78rem] leading-relaxed text-[#8fc3cd]">
        {lab.tagline}
      </p>

      <div className="mt-auto flex flex-wrap gap-1.5 pt-3">
        {lab.stack.map((tech) => (
          <span
            key={tech}
            className="rounded-md border border-[rgba(40,200,230,0.22)] bg-[rgba(34,230,255,0.05)] px-2 py-0.5 font-mono text-[0.6rem] text-[#a6e8f0]"
          >
            {tech}
          </span>
        ))}
      </div>

      <div className="mt-3 flex items-center justify-end border-t border-[rgba(40,200,230,0.22)] pt-2">
        <span
          className={[
            "font-mono text-[0.62rem] tracking-[0.2em] transition-colors duration-300",
            disabled
              ? "text-[#5e8f99] group-hover:text-[#8fc3cd]"
              : "text-[#7df9ff] group-hover:text-white",
          ].join(" ")}
        >
          {disabled ? "STANDBY" : isExternal ? "LAUNCH ↗" : "LAUNCH ▸"}
        </span>
      </div>
    </div>
  );

  if (disabled) {
    return (
      <div className="text-left opacity-80" aria-label={`${lab.title} — not yet available`}>
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
    <div className="grid min-h-[170px] place-content-center rounded-[10px] border border-dashed border-[rgba(40,200,230,0.2)] bg-[linear-gradient(180deg,rgba(4,24,36,0.2),rgba(2,9,17,0.3))] p-4 text-center">
      <span className="font-mono text-[0.62rem] tracking-[0.22em] text-[#5e8f99]">
        ▢ EMPTY BAY
      </span>
      <span className="mt-1.5 font-mono text-[0.62rem] tracking-[0.1em] text-[#3f6770]">
        MODULE INBOUND…
      </span>
    </div>
  );
}

export default function LabsPanel() {
  const openBays = Math.max(0, MODULE_BAYS - labs.length);

  return (
    <div className="hud-panel rounded-xl border border-[rgba(40,200,230,0.22)] bg-[linear-gradient(150deg,rgba(6,20,30,0.78),rgba(3,9,16,0.9))] p-4 shadow-[0_0_0_1px_rgba(34,230,255,0.05),inset_0_0_34px_rgba(0,140,190,0.05)]">
      <span className="hud-bracket hud-bracket-tl" />
      <span className="hud-bracket hud-bracket-tr" />
      <span className="hud-bracket hud-bracket-bl" />
      <span className="hud-bracket hud-bracket-br" />
      <span className="hud-panel-scan" />

      <div className="relative z-[2] mb-3 flex items-center gap-2.5 border-b border-[rgba(40,200,230,0.22)] pb-2.5">
        <span className="hud-dot-pulse h-2.5 w-2.5 rounded-full bg-[#22e6ff] shadow-[0_0_12px_#22e6ff]" />
        <h2 className="font-mono text-[0.74rem] font-semibold tracking-[0.22em] text-[#7df9ff]">
          LABS // DEPLOYED MODULES
        </h2>
        <span className="ml-auto font-mono text-[0.6rem] tracking-[0.14em] text-[#5e8f99]">
          {labs.length} LOADED · {openBays} {openBays === 1 ? "BAY" : "BAYS"} OPEN
        </span>
      </div>

      <div className="relative z-[2] grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {labs.map((lab) => (
          <LabTile key={lab.slug} lab={lab} />
        ))}
        {Array.from({ length: openBays }).map((_, i) => (
          <GhostTile key={`ghost-${i}`} />
        ))}
      </div>
    </div>
  );
}
