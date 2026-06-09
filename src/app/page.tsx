import Image from "next/image";
import Link from "next/link";
import { getProjects } from "@/lib/content";
import { labs } from "@/data/labs";
import LabsPanel from "./components/LabsPanel";
import CommandBar from "./components/CommandBar";
import TelemetryPanel from "./components/TelemetryPanel";
import BootSequence from "./components/BootSequence";

// Rendered on demand (this route can't be prerendered — the content API isn't
// reachable during a Vercel build), but the expensive call to the Python content
// API is served from Next's Data Cache for an hour (see CONTENT_REVALIDATE in
// src/lib/content.ts). So Postgres + the Python function are hit at most once an
// hour instead of on every visit, which removes the cold-start stall; the warm
// Node renderer just re-uses the cached JSON.
export const dynamic = "force-dynamic";

const channels = [
  {
    label: "Email",
    id: "01",
    type: "DIRECT",
    ico: "@",
    icoClass: "text-[0.95rem]",
    href: "mailto:quocanhtophuong@gmail.com",
    external: false,
  },
  {
    label: "LinkedIn",
    id: "02",
    type: "NETWORK",
    ico: "in",
    icoClass: "text-[0.82rem] font-semibold",
    href: "https://www.linkedin.com/in/quoc-anh-to-79024b148/",
    external: true,
  },
  {
    label: "GitHub",
    id: "03",
    type: "REPO",
    ico: "</>",
    icoClass: "text-[0.62rem] font-bold tracking-tighter",
    href: "https://github.com/quocanhto85",
    external: true,
  },
  {
    label: "Resume",
    id: "04",
    type: "DOSSIER",
    ico: "▤",
    icoClass: "text-[0.95rem]",
    href: "/resume",
    external: false,
  },
];

function PanelHead({
  title,
  meta,
  live,
}: {
  title: string;
  meta: string;
  live?: boolean;
}) {
  return (
    <div className="relative z-[2] mb-3 flex items-center gap-2.5 border-b border-[rgba(40,200,230,0.22)] pb-2.5">
      <span className="hud-dot-pulse h-2.5 w-2.5 rounded-full bg-[#22e6ff] shadow-[0_0_12px_#22e6ff]" />
      <h2 className="font-mono text-[0.74rem] font-semibold tracking-[0.22em] text-[#7df9ff]">
        {title}
      </h2>
      <span
        className={`ml-auto font-mono text-[0.6rem] tracking-[0.14em] ${
          live ? "text-[#39ff9e]" : "text-[#5e8f99]"
        }`}
      >
        {meta}
      </span>
    </div>
  );
}

function Brackets() {
  return (
    <>
      <span className="hud-bracket hud-bracket-tl" />
      <span className="hud-bracket hud-bracket-tr" />
      <span className="hud-bracket hud-bracket-bl" />
      <span className="hud-bracket hud-bracket-br" />
    </>
  );
}

export default async function Home() {
  const projects = await getProjects();

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-batcave pb-12 text-slate-100">
      <div className="hud-fx-grid" />
      <div className="hud-fx-scan" />
      <div className="hud-fx-sweep" />
      <div className="hud-fx-vignette" />

      <BootSequence dossierCount={projects.length} moduleCount={labs.length} />

      <main className="relative z-[5] mx-auto w-full max-w-6xl px-4 py-5 sm:px-6 sm:py-6">
        <CommandBar />

        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-12">
          {/* COMMS */}
          <section className="hud-panel rounded-xl border border-[rgba(40,200,230,0.22)] bg-[linear-gradient(150deg,rgba(6,20,30,0.78),rgba(3,9,16,0.9))] p-4 shadow-[0_0_0_1px_rgba(34,230,255,0.05),inset_0_0_34px_rgba(0,140,190,0.05)] lg:col-span-7">
            <Brackets />
            <span className="hud-panel-scan" />
            <PanelHead
              title="COMMS // SECURE CHANNELS"
              meta="4 CHANNELS ENCRYPTED"
              live
            />
            <div className="relative z-[2] grid grid-cols-1 gap-2.5 sm:grid-cols-2">
              {channels.map((c) => (
                <a
                  key={c.label}
                  href={c.href}
                  target={c.external ? "_blank" : undefined}
                  rel={c.external ? "noreferrer noopener" : undefined}
                  className="hud-sweep-tile flex items-center gap-3 rounded-[9px] border border-[rgba(40,200,230,0.22)] bg-[linear-gradient(180deg,rgba(4,26,38,0.5),rgba(2,10,18,0.6))] px-3 py-2.5 hover:-translate-y-0.5 hover:border-[rgba(60,225,255,0.55)] hover:shadow-[0_0_18px_rgba(34,230,255,0.22)]"
                >
                  <span
                    className={`grid h-[34px] w-[34px] flex-shrink-0 place-items-center rounded-lg border border-[rgba(40,200,230,0.22)] bg-[rgba(34,230,255,0.06)] font-mono leading-none text-[#7df9ff] ${c.icoClass}`}
                  >
                    {c.ico}
                  </span>
                  <span className="flex min-w-0 flex-col">
                    <span className="text-[0.92rem] font-semibold text-[#dffbff]">
                      {c.label}
                    </span>
                    <span className="font-mono text-[0.58rem] tracking-[0.16em] text-[#5e8f99]">
                      CHANNEL:{c.id} · {c.type}
                    </span>
                  </span>
                  <span className="ml-auto flex flex-col items-end gap-1">
                    <span className="font-mono text-[0.55rem] tracking-[0.14em] text-[#39ff9e]">
                      SECURE
                    </span>
                    <span className="hud-signal" aria-hidden>
                      <i />
                      <i />
                      <i />
                      <i />
                    </span>
                  </span>
                </a>
              ))}
            </div>
          </section>

          {/* TELEMETRY */}
          <div className="lg:col-span-5">
            <TelemetryPanel />
          </div>

          {/* LABS */}
          <div className="lg:col-span-12">
            <LabsPanel />
          </div>

          {/* ARCHIVE QUERY */}
          <section className="hud-panel rounded-xl border border-[rgba(40,200,230,0.22)] bg-[linear-gradient(150deg,rgba(6,20,30,0.78),rgba(3,9,16,0.9))] p-4 shadow-[0_0_0_1px_rgba(34,230,255,0.05),inset_0_0_34px_rgba(0,140,190,0.05)] lg:col-span-12">
            <Brackets />
            <PanelHead
              title="ARCHIVE // QUERY"
              meta={`INDEX: ${projects.length} ${
                projects.length === 1 ? "DOSSIER" : "DOSSIERS"
              }`}
            />
            <div className="relative z-[2] flex items-center gap-3 rounded-[10px] border border-[rgba(40,200,230,0.22)] bg-[linear-gradient(180deg,rgba(4,24,36,0.5),rgba(2,10,18,0.6))] px-4 py-3">
              <span className="font-mono text-[0.85rem] text-[#39ff9e]">&gt;</span>
              <input
                aria-label="Search the mission archive by title, tag or keyword"
                placeholder="search archive by title, tag, or keyword…"
                className="flex-1 bg-transparent font-mono text-[0.86rem] tracking-[0.04em] text-[#dffbff] outline-none placeholder:text-[#4d7d86]"
              />
              <span className="hud-caret" aria-hidden />
              <span className="hidden font-mono text-[0.58rem] tracking-[0.14em] text-[#5e8f99] sm:inline">
                RETURN TO EXECUTE
              </span>
            </div>
          </section>
        </div>

        {/* MISSION ARCHIVE */}
        <div className="mt-7 mb-3 flex items-center gap-2.5">
          <h2 className="font-mono text-[0.72rem] font-semibold tracking-[0.26em] text-[#7df9ff]">
            MISSION ARCHIVE
          </h2>
          <span className="font-mono text-[0.6rem] tracking-[0.12em] text-[#5e8f99]">
            {"// DECLASSIFIED OPERATIONS"}
          </span>
          <span className="h-px flex-1 bg-[linear-gradient(90deg,rgba(60,225,255,0.55),transparent)]" />
        </div>

        <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project, i) => (
            <Link
              key={project.slug}
              href={`/articles/${project.slug}`}
              className="hud-panel group block rounded-xl border border-[rgba(40,200,230,0.22)] bg-[linear-gradient(150deg,rgba(6,20,30,0.8),rgba(3,9,16,0.92))] transition-all duration-300 hover:-translate-y-1.5 hover:border-[rgba(60,225,255,0.55)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.5),0_0_30px_rgba(34,230,255,0.25)] focus-visible:-translate-y-1.5 focus-visible:border-[rgba(60,225,255,0.55)] focus-visible:shadow-[0_12px_40px_rgba(0,0,0,0.5),0_0_30px_rgba(34,230,255,0.25)] focus-visible:outline-none"
            >
              <div className="relative h-44 w-full overflow-hidden rounded-t-xl border-b border-[rgba(40,200,230,0.22)] bg-black/30">
                <Image
                  src={project.imageSrc}
                  alt={project.title}
                  fill
                  className="object-cover transition-transform duration-500 [filter:saturate(1.1)_contrast(1.05)] group-hover:scale-[1.07]"
                />
                <div className="pointer-events-none absolute inset-0 z-[2] opacity-40 [background-image:linear-gradient(rgba(60,225,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(60,225,255,0.06)_1px,transparent_1px)] [background-size:20px_20px]" />
                <div className="pointer-events-none absolute inset-0 [background:linear-gradient(180deg,rgba(4,7,13,0)_40%,rgba(4,7,13,0.85))]" />
                <span className="absolute left-2.5 top-2.5 z-[3] rounded-[5px] border border-[rgba(60,225,255,0.55)] bg-[rgba(4,12,20,0.65)] px-2 py-0.5 font-mono text-[0.56rem] tracking-[0.16em] text-[#7df9ff]">
                  DOSSIER-{String(i + 1).padStart(3, "0")}
                </span>
                <span className="absolute right-2.5 top-2.5 z-[3] rounded-[5px] border border-[rgba(57,255,158,0.4)] bg-[rgba(4,12,20,0.65)] px-2 py-0.5 font-mono text-[0.56rem] tracking-[0.14em] text-[#39ff9e]">
                  CLEARED
                </span>
              </div>
              <div className="relative z-[2] space-y-2.5 p-4">
                <p className="font-mono text-[0.6rem] tracking-[0.14em] text-[#5e8f99]">
                  ▣ {project.date}
                </p>
                <h3 className="text-[1.02rem] font-bold leading-tight text-[#e9fcff] transition-colors duration-300 group-hover:text-white">
                  {project.title}
                </h3>
                <p className="text-[0.8rem] leading-relaxed text-[#8fc3cd]">
                  {project.description}
                </p>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {project.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-[rgba(40,200,230,0.22)] bg-[rgba(34,230,255,0.05)] px-2 py-0.5 font-mono text-[0.58rem] text-[#a6e8f0]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </Link>
          ))}
        </section>
      </main>

      {/* SYS FEED ticker */}
      <div className="fixed inset-x-0 bottom-0 z-20 flex h-[30px] items-center overflow-hidden border-t border-[rgba(40,200,230,0.22)] bg-[linear-gradient(180deg,rgba(4,12,20,0.92),rgba(3,7,13,0.96))] font-mono text-[0.62rem] tracking-[0.1em]">
        <span className="flex h-full flex-shrink-0 items-center bg-[#22e6ff] px-3.5 font-bold tracking-[0.18em] text-[#03060c]">
          SYS FEED
        </span>
        <div className="hud-ticker whitespace-nowrap pl-[100%] text-[#7fc9d6]">
          <span className="text-[#39ff9e]">[OK]</span> secure uplink established
          &nbsp;·&nbsp; <span className="text-[#39ff9e]">[OK]</span> 4/4 comms
          channels encrypted &nbsp;·&nbsp;{" "}
          <span className="text-[#ffc24b]">[INFO]</span> alfred assistant standing
          by &nbsp;·&nbsp; <span className="text-[#39ff9e]">[OK]</span> archive index
          synced — {projects.length} dossiers declassified &nbsp;·&nbsp;{" "}
          <span className="text-[#39ff9e]">[OK]</span> {labs.length} module
          {labs.length === 1 ? "" : "s"} operational &nbsp;·&nbsp;{" "}
          <span className="text-[#39ff9e]">[OK]</span> telemetry stream nominal
          &nbsp;·&nbsp; <span className="text-[#ffc24b]">[INFO]</span> clearance
          level ALPHA confirmed &nbsp;·&nbsp;
        </div>
      </div>
    </div>
  );
}
