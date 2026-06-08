"use client";

import { useEffect, useState } from "react";

type BootLine = { text: string; status: string; tone: "ok" | "warn" | "alpha" };

/**
 * Terminal boot overlay that plays once per browser session (gated via
 * sessionStorage so it doesn't replay on every client-side return to Home).
 * Renders visible on first paint, then fades out after the sequence — or
 * immediately, if this session already booted.
 */
export default function BootSequence({
  dossierCount,
  moduleCount,
}: {
  dossierCount: number;
  moduleCount: number;
}) {
  const [visible, setVisible] = useState(true);
  const [hidden, setHidden] = useState(false);

  const lines: BootLine[] = [
    { text: "initializing kernel", status: "OK", tone: "ok" },
    { text: "mounting secure filesystem", status: "OK", tone: "ok" },
    { text: "establishing encrypted uplink", status: "OK", tone: "ok" },
    { text: "authenticating operator", status: "ALPHA", tone: "alpha" },
    { text: "loading comms channels (4)", status: "OK", tone: "ok" },
    { text: "spinning up telemetry feed", status: "LIVE", tone: "ok" },
    { text: `indexing mission archive`, status: String(dossierCount), tone: "ok" },
    { text: `mounting field modules`, status: String(moduleCount), tone: "ok" },
    { text: "waking alfred assistant", status: "STANDBY", tone: "warn" },
  ];

  useEffect(() => {
    const KEY = "batcave-booted";
    const alreadyBooted =
      typeof sessionStorage !== "undefined" && sessionStorage.getItem(KEY);

    if (!alreadyBooted) {
      try {
        sessionStorage.setItem(KEY, "1");
      } catch {
        /* private mode — boot still plays, just won't persist */
      }
    }

    // Returning visitors (already booted this session) skip the show: the
    // timeouts fire on the next tick instead of synchronously in the effect.
    const fade = setTimeout(() => setVisible(false), alreadyBooted ? 0 : 2500);
    const drop = setTimeout(() => setHidden(true), alreadyBooted ? 0 : 3200);
    return () => {
      clearTimeout(fade);
      clearTimeout(drop);
    };
  }, []);

  if (hidden) return null;

  return (
    <div
      aria-hidden
      className={`fixed inset-0 z-[60] flex flex-col items-center justify-center bg-[#03060c] font-mono transition-opacity duration-700 ${
        visible ? "opacity-100" : "pointer-events-none opacity-0"
      }`}
    >
      <div className="w-[min(560px,86vw)]">
        <div className="mb-4 flex items-center gap-2 text-sm font-bold tracking-[0.18em] text-[#7df9ff] [text-shadow:0_0_18px_rgba(34,230,255,0.6)]">
          <span>🦇</span>
          <span className="font-[family-name:var(--font-geist-mono)]">
            BATCAVE OPS // SECURE TERMINAL
          </span>
        </div>

        <div className="space-y-1">
          {lines.map((ln, i) => (
            <div
              key={ln.text}
              className="hud-boot-line text-[0.8rem] leading-7 text-[#86d9e6]"
              style={{ animationDelay: `${0.18 * i + 0.2}s` }}
            >
              <span>&gt; {ln.text} </span>
              <span className="text-[#3a5a63]">
                {".".repeat(Math.max(2, 26 - ln.text.length))}
              </span>{" "}
              <span
                className={
                  ln.tone === "ok"
                    ? "text-[#39ff9e]"
                    : ln.tone === "warn"
                    ? "text-[#ffc24b]"
                    : "text-[#7df9ff]"
                }
              >
                [{ln.status}]
              </span>
            </div>
          ))}
          <div
            className="hud-boot-line text-[0.8rem] leading-7 text-[#39ff9e]"
            style={{ animationDelay: `${0.18 * lines.length + 0.3}s` }}
          >
            &gt; BATCAVE OPS READY
          </div>
        </div>

        <div className="mt-4 h-1.5 overflow-hidden rounded-sm border border-[rgba(60,225,255,0.55)] bg-black/40">
          <span className="hud-boot-fill block h-full w-0 bg-[linear-gradient(90deg,#22e6ff,#39ff9e)] shadow-[0_0_14px_#22e6ff]" />
        </div>
      </div>
    </div>
  );
}
