"use client";

import { useEffect, useState } from "react";

function PanelHeader() {
  return (
    <div className="relative z-[2] mb-3 flex items-center gap-2.5 border-b border-[rgba(40,200,230,0.22)] pb-2.5">
      <span className="hud-dot-pulse h-2.5 w-2.5 rounded-full bg-[#22e6ff] shadow-[0_0_12px_#22e6ff]" />
      <h2 className="font-mono text-[0.74rem] font-semibold tracking-[0.22em] text-[#7df9ff]">
        OPS // TELEMETRY
      </h2>
      <span className="ml-auto inline-flex items-center gap-1.5 font-mono text-[0.6rem] tracking-[0.16em] text-[#39ff9e]">
        <span className="hud-dot-pulse h-1.5 w-1.5 rounded-full bg-[#39ff9e] shadow-[0_0_8px_#39ff9e]" />
        LIVE
      </span>
    </div>
  );
}

function Radar() {
  const blips = [
    { top: "32%", left: "60%", delay: "0.4s" },
    { top: "58%", left: "40%", delay: "1.6s" },
    { top: "46%", left: "70%", delay: "2.4s" },
  ];
  return (
    <div className="hud-radar" aria-hidden>
      <div className="hud-radar-ring" />
      <div className="hud-radar-ring r2" />
      <div className="hud-radar-ring r3" />
      <div className="hud-radar-cross" />
      <div className="hud-radar-cross h" />
      <div className="hud-radar-beam" />
      {blips.map((b, i) => (
        <span
          key={i}
          className="hud-radar-blip"
          style={{ top: b.top, left: b.left, animationDelay: b.delay }}
        />
      ))}
    </div>
  );
}

function Meter({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between font-mono text-[0.6rem] tracking-[0.12em] text-[#5e8f99]">
        <span>{label}</span>
        <b className="text-[#7df9ff]">{value}%</b>
      </div>
      <div className="hud-meter">
        <span className="hud-meter-fill" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

const SPARK_W = 220;
const SPARK_H = 40;

export default function TelemetryPanel() {
  const [meters, setMeters] = useState({ core: 62, mem: 41, net: 78 });
  const [spark, setSpark] = useState<number[]>(() =>
    Array.from({ length: 40 }, (_, i) => 20 + Math.sin(i / 3) * 8)
  );

  useEffect(() => {
    const rnd = (min: number, max: number) =>
      Math.floor(Math.random() * (max - min) + min);

    const m = setInterval(() => {
      setMeters({ core: rnd(48, 74), mem: rnd(33, 58), net: rnd(64, 92) });
    }, 1400);

    const s = setInterval(() => {
      setSpark((prev) => [...prev.slice(1), 8 + Math.random() * 26]);
    }, 420);

    return () => {
      clearInterval(m);
      clearInterval(s);
    };
  }, []);

  const step = SPARK_W / (spark.length - 1);
  const points = spark
    .map((y, i) => `${(i * step).toFixed(1)},${(SPARK_H - y).toFixed(1)}`)
    .join(" ");

  return (
    <div className="hud-panel h-full rounded-xl border border-[rgba(40,200,230,0.22)] bg-[linear-gradient(150deg,rgba(6,20,30,0.78),rgba(3,9,16,0.9))] p-4 shadow-[0_0_0_1px_rgba(34,230,255,0.05),inset_0_0_34px_rgba(0,140,190,0.05)]">
      <span className="hud-bracket hud-bracket-tl" />
      <span className="hud-bracket hud-bracket-tr" />
      <span className="hud-bracket hud-bracket-bl" />
      <span className="hud-bracket hud-bracket-br" />

      <PanelHeader />

      <div className="relative z-[2] flex flex-col items-center gap-4 sm:flex-row">
        <Radar />
        <div className="flex w-full flex-1 flex-col gap-2.5">
          <Meter label="CORE LOAD" value={meters.core} />
          <Meter label="MEM BUFFER" value={meters.mem} />
          <Meter label="NET THRUPUT" value={meters.net} />
          <svg
            className="mt-1 h-10 w-full"
            viewBox={`0 0 ${SPARK_W} ${SPARK_H}`}
            preserveAspectRatio="none"
            aria-hidden
          >
            <polyline
              points={points}
              fill="none"
              stroke="#22e6ff"
              strokeWidth="1.6"
              style={{ filter: "drop-shadow(0 0 4px rgba(34,230,255,0.7))" }}
            />
          </svg>
        </div>
      </div>
    </div>
  );
}
