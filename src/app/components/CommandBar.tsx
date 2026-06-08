"use client";

import { useEffect, useState } from "react";

function SignalBars() {
  return (
    <span className="hud-signal" aria-hidden>
      <i />
      <i />
      <i />
      <i />
    </span>
  );
}

function Stat({
  label,
  children,
  tone,
}: {
  label: string;
  children: React.ReactNode;
  tone?: "cyan" | "green";
}) {
  return (
    <div className="flex flex-col leading-tight">
      <span className="font-mono text-[0.56rem] tracking-[0.22em] text-[#5e8f99]">
        {label}
      </span>
      <span
        className={`font-mono text-[0.9rem] ${
          tone === "green" ? "text-[#39ff9e]" : "text-[#7df9ff]"
        }`}
      >
        {children}
      </span>
    </div>
  );
}

/**
 * Top command bar. Clock + latency hydrate to placeholders on the server and
 * are filled in on the client after mount, so there's no SSR/CSR mismatch.
 */
export default function CommandBar() {
  const [clock, setClock] = useState("--:--:--");
  const [latency, setLatency] = useState("—");

  useEffect(() => {
    const pad = (n: number) => String(n).padStart(2, "0");
    const tickClock = () => {
      const d = new Date();
      setClock(`${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`);
    };
    tickClock();
    const c = setInterval(tickClock, 1000);

    const tickLatency = () =>
      setLatency(`${Math.floor(Math.random() * 13 + 9)}ms`);
    tickLatency();
    const l = setInterval(tickLatency, 1400);

    return () => {
      clearInterval(c);
      clearInterval(l);
    };
  }, []);

  return (
    <div className="hud-panel relative flex flex-wrap items-center gap-4 rounded-xl border border-[rgba(40,200,230,0.22)] bg-[linear-gradient(120deg,rgba(6,20,30,0.82),rgba(4,10,18,0.9))] px-4 py-3 shadow-[0_0_0_1px_rgba(34,230,255,0.06),inset_0_0_30px_rgba(0,150,200,0.05)]">
      <span className="hud-rail" />

      <div className="relative z-[2] flex min-w-0 items-center gap-3">
        <span className="text-2xl [filter:drop-shadow(0_0_10px_rgba(34,230,255,0.7))]">
          🦇
        </span>
        <div>
          <h1 className="font-mono text-[1rem] font-bold leading-tight tracking-[0.14em] text-[#eafdff]">
            QUOC ANH{" "}
            <span className="text-[#7df9ff] [text-shadow:0_0_14px_rgba(34,230,255,0.6)]">
              {"// BATCAVE OPS"}
            </span>
          </h1>
          <p className="font-mono text-[0.6rem] tracking-[0.26em] text-[#5e8f99]">
            OPERATOR CONSOLE · CLEARANCE: ALPHA
          </p>
        </div>
      </div>

      <div className="relative z-[2] ml-auto flex flex-wrap items-center gap-x-5 gap-y-2">
        <Stat label="UPLINK">
          <SignalBars />
        </Stat>
        <Stat label="ENCRYPTION" tone="green">
          AES-256
        </Stat>
        <Stat label="LATENCY">{latency}</Stat>
        <Stat label="SECTOR">GOTHAM-7</Stat>
        <Stat label="LOCAL TIME">{clock}</Stat>
        <span className="inline-flex items-center gap-2 font-mono text-[0.62rem] tracking-[0.2em] text-[#39ff9e]">
          <span className="hud-dot-pulse h-2 w-2 rounded-full bg-[#39ff9e] shadow-[0_0_10px_#39ff9e]" />
          SYSTEM ONLINE
        </span>
      </div>
    </div>
  );
}
