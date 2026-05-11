"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  role: ChatRole;
  content: string;
  pending?: boolean;
};

type RateLimitState = {
  remainingSeconds: number;
};

const MAX_VISIBLE_MESSAGES = 10;

function getGreeting(date = new Date()): string {
  const hour = date.getHours();

  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  // Lightweight v4-shaped fallback (good enough for an opaque session id)
  const rnd = (n: number) =>
    [...Array(n)]
      .map(() => Math.floor(Math.random() * 16).toString(16))
      .join("");
  return `${rnd(8)}-${rnd(4)}-4${rnd(3)}-${rnd(4)}-${rnd(12)}`;
}

export default function Alfred() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimit, setRateLimit] = useState<RateLimitState | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [greeting, setGreeting] = useState(() => getGreeting());

  const messagesRef = useRef<HTMLDivElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Keep Alfred's salutation aligned with the visitor's local time.
  useEffect(() => {
    const updateGreeting = () => setGreeting(getGreeting());

    updateGreeting();
    const id = setInterval(updateGreeting, 60 * 1000);
    return () => clearInterval(id);
  }, []);

  // Auto-scroll on new content
  useEffect(() => {
    if (!messagesRef.current) return;
    messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
  }, [messages, open]);

  // Rate-limit countdown — single ticker that drives the countdown to zero
  // and then clears itself, without calling setState during render.
  useEffect(() => {
    if (!rateLimit) return;
    const id = setInterval(() => {
      setRateLimit((prev) => {
        if (!prev) return null;
        if (prev.remainingSeconds <= 1) return null;
        return { remainingSeconds: prev.remainingSeconds - 1 };
      });
    }, 1000);
    return () => clearInterval(id);
  }, [rateLimit]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || busy || rateLimit) return;

    setError(null);
    setInput("");
    setBusy(true);

    const sid = sessionId ?? uuid();
    if (!sessionId) setSessionId(sid);

    setMessages((prev) =>
      [
        ...prev,
        { role: "user", content: text } as ChatMessage,
        { role: "assistant", content: "", pending: true } as ChatMessage,
      ].slice(-MAX_VISIBLE_MESSAGES)
    );

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("/api/alfred/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sid }),
        signal: controller.signal,
      });

      if (res.status === 429) {
        const data = await res.json().catch(() => ({}));
        const wait = Number(data?.wait_seconds ?? data?.retry_after ?? 30);
        setRateLimit({ remainingSeconds: wait });
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1
              ? { role: "assistant", content: "", pending: false }
              : m
          )
        );
        return;
      }

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`);
      }

      // Parse SSE stream chunk-by-chunk. We accumulate bytes until we have a
      // full ``data: ...\n\n`` frame, then dispatch.
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let idx;
        while ((idx = buffer.indexOf("\n\n")) !== -1) {
          const frame = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const line = frame.split("\n").find((l) => l.startsWith("data:"));
          if (!line) continue;
          const payload = line.slice(5).trim();
          if (!payload) continue;
          try {
            const obj = JSON.parse(payload) as {
              token?: string;
              done?: boolean;
              error?: string;
              session_id?: string;
            };
            if (obj.error) {
              setError(obj.error);
              setMessages((prev) =>
                prev.map((m, i) =>
                  i === prev.length - 1
                    ? {
                        role: "assistant",
                        content:
                          m.content ||
                          "Apologies, sir — Alfred is temporarily indisposed.",
                        pending: false,
                      }
                    : m
                )
              );
              continue;
            }
            if (obj.token) {
              setMessages((prev) =>
                prev.map((m, i) =>
                  i === prev.length - 1
                    ? {
                        role: "assistant",
                        content: m.content + obj.token,
                        pending: false,
                      }
                    : m
                )
              );
            }
            if (obj.done) {
              if (obj.session_id) setSessionId(obj.session_id);
              setMessages((prev) =>
                prev.map((m, i) =>
                  i === prev.length - 1
                    ? { ...m, pending: false }
                    : m
                )
              );
            }
          } catch {
            // ignore malformed frames
          }
        }
      }
    } catch (err) {
      console.log('error: ', err)
      if ((err as Error).name === "AbortError") return;
      setError("Alfred is temporarily indisposed.");
      setMessages((prev) =>
        prev.map((m, i) =>
          i === prev.length - 1
            ? {
                role: "assistant",
                content:
                  m.content ||
                  "Apologies, sir — Alfred is temporarily indisposed.",
                pending: false,
              }
            : m
        )
      );
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  }, [input, busy, rateLimit, sessionId]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <>
      {/* Floating launcher */}
      <button
        type="button"
        aria-label={open ? "Close Alfred" : "Open Alfred"}
        onClick={() => setOpen((v) => !v)}
        className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full border border-cyan-300/60 bg-[linear-gradient(145deg,rgba(0,30,38,0.95),rgba(0,8,18,0.95))] text-2xl text-cyan-100 shadow-[0_0_0_1px_rgba(34,220,255,0.2),0_0_24px_rgba(0,196,255,0.35)] transition hover:-translate-y-0.5 hover:border-cyan-200 hover:text-white"
      >
        <span aria-hidden>🦇</span>
      </button>

      {open && (
        <section
          aria-label="Alfred chat panel"
          className="fixed bottom-24 right-6 z-40 flex h-[520px] w-[380px] flex-col overflow-hidden rounded-2xl border border-cyan-300/55 bg-[linear-gradient(160deg,rgba(0,30,38,0.95),rgba(0,8,18,0.97))] shadow-[0_0_0_1px_rgba(34,220,255,0.18),0_20px_40px_rgba(0,0,0,0.55),0_0_24px_rgba(0,196,255,0.18)] backdrop-blur"
        >
          {/* Grid overlay */}
          <div className="pointer-events-none absolute inset-0 opacity-25 [background-image:linear-gradient(rgba(88,251,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(88,251,255,0.06)_1px,transparent_1px)] [background-size:18px_18px]" />

          {/* Header */}
          <header className="relative z-10 flex items-center gap-2 border-b border-cyan-300/35 px-4 py-3">
            <span aria-hidden>🦇</span>
            <h2 className="text-sm font-semibold tracking-wide text-cyan-50">
              Alfred
            </h2>
            <span className="ml-1 inline-flex items-center gap-1.5 rounded-full border border-emerald-300/40 bg-emerald-300/10 px-2 py-0.5 text-[10px] tracking-[0.14em] text-emerald-200">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-300 opacity-75" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-300" />
              </span>
              ONLINE
            </span>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close panel"
              className="ml-auto rounded-md border border-cyan-300/30 px-2 py-0.5 text-xs text-cyan-200 transition hover:border-cyan-200 hover:text-white"
            >
              ✕
            </button>
          </header>

          {/* Messages */}
          <div
            ref={messagesRef}
            className="relative z-10 flex-1 space-y-2.5 overflow-y-auto px-3 py-3 text-sm"
          >
            {messages.length === 0 && (
              <div className="rounded-lg border border-cyan-300/25 bg-cyan-300/5 px-3 py-2 text-xs text-cyan-100/80">
                <p className="font-mono tracking-wide text-cyan-200">
                  &gt; {greeting}. I am Alfred, at your service.
                </p>
                <p className="mt-1 text-cyan-100/70">
                  Ask about Quoc Anh&apos;s projects, his resume, or this
                  Batcave itself.
                </p>
              </div>
            )}
            {messages.map((m, i) => (
              <MessageBubble key={i} message={m} />
            ))}
            {error && !rateLimit && (
              <p className="text-xs text-rose-300/80">{error}</p>
            )}
            {rateLimit && (
              <p className="text-xs text-amber-300/85">
                Alfred requires a moment to collect himself. Try again in{" "}
                {rateLimit.remainingSeconds}s.
              </p>
            )}
          </div>

          {/* Input */}
          <form
            className="relative z-10 flex items-center gap-2 border-t border-cyan-300/35 px-3 py-3"
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={
                rateLimit
                  ? `Cooling down… ${rateLimit.remainingSeconds}s`
                  : "Ask Alfred anything…"
              }
              disabled={busy || !!rateLimit}
              className="flex-1 rounded-lg border border-cyan-300/35 bg-[linear-gradient(180deg,rgba(2,30,45,0.55),rgba(0,10,20,0.72))] px-3 py-2 text-sm text-cyan-50 placeholder:text-cyan-200/45 outline-none transition focus:border-cyan-200 focus:ring-2 focus:ring-cyan-300/25 disabled:opacity-60"
              aria-label="Message Alfred"
              maxLength={2000}
            />
            <button
              type="submit"
              disabled={busy || !input.trim() || !!rateLimit}
              className="rounded-lg border border-cyan-300/55 bg-cyan-300/10 px-3 py-2 text-[11px] font-mono tracking-[0.18em] text-cyan-100 transition hover:border-cyan-200 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              {busy ? "…" : "TRANSMIT"}
            </button>
          </form>

          <footer className="relative z-10 border-t border-cyan-300/20 px-3 py-1.5 text-center text-[10px] tracking-wide text-cyan-200/55">
            10 requests / minute · Powered by Ollama
          </footer>
        </section>
      )}
    </>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-lg border border-cyan-300/55 bg-cyan-300/10 px-3 py-2 text-cyan-50 shadow-[0_0_10px_rgba(34,220,255,0.15)]">
          {message.content}
        </div>
      </div>
    );
  }

  const showCursor = message.pending || message.content === "";
  return (
    <div className="flex items-start gap-2">
      <span
        aria-hidden
        className="mt-1 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border border-cyan-300/40 bg-cyan-300/5 text-xs"
      >
        🦇
      </span>
      <div className="max-w-[85%] rounded-lg border border-cyan-300/25 bg-slate-900/60 px-3 py-2 text-cyan-50/95">
        {message.content || (showCursor ? <TypingDots /> : null)}
        {message.content && showCursor && (
          <span className="ml-0.5 inline-block w-1.5 animate-pulse text-cyan-300">
            ▍
          </span>
        )}
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <span className="inline-flex gap-1 align-middle text-cyan-200">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-300/80 [animation-delay:0ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-300/80 [animation-delay:150ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-300/80 [animation-delay:300ms]" />
    </span>
  );
}
