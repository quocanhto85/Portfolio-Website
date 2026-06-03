import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getProjectBySlug, type ContentBlock } from "@/lib/content";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const project = await getProjectBySlug(slug);
  if (!project) return { title: "Article Not Found" };
  return {
    title: `${project.title} | Batcave Portfolio`,
    description: project.description,
  };
}

function renderParagraphWithLinks(
  text: string,
  links?: { text: string; href: string }[]
) {
  if (!links?.length) return text;

  const parts: React.ReactNode[] = [];
  let remaining = text;

  for (const link of links) {
    const idx = remaining.indexOf(link.text);
    if (idx === -1) continue;
    if (idx > 0) parts.push(remaining.slice(0, idx));
    parts.push(
      <a
        key={link.href}
        href={link.href}
        target="_blank"
        rel="noreferrer"
        className="text-cyan-200 underline underline-offset-4 transition hover:text-cyan-50"
      >
        {link.text}
      </a>
    );
    remaining = remaining.slice(idx + link.text.length);
  }

  if (remaining) parts.push(remaining);
  return parts;
}

function renderBlock(block: ContentBlock, index: number) {
  switch (block.type) {
    case "heading":
      return (
        <h2
          key={index}
          className="flex items-center gap-2 pt-2 text-xl font-semibold text-cyan-50"
        >
          <span className="h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_10px_rgba(57,243,255,0.9)]" />
          {block.text}
        </h2>
      );
    case "list":
      return (
        <ul key={index} className="space-y-2 text-cyan-100/90">
          {block.items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      );
    case "video":
      return (
        <figure key={index} className="space-y-2">
          <div className="overflow-hidden rounded-xl border border-cyan-300/45 bg-black/40 shadow-[0_0_0_1px_rgba(34,220,255,0.14),0_0_24px_rgba(0,196,255,0.18)]">
            <video
              controls
              preload="metadata"
              playsInline
              poster={block.poster}
              className="block h-auto w-full"
            >
              <source src={block.src} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
          {block.caption ? (
            <figcaption className="text-xs text-cyan-200/70">
              {block.caption}
            </figcaption>
          ) : null}
        </figure>
      );
    case "image":
      return (
        <figure key={index} className="space-y-2">
          <div className="overflow-hidden rounded-xl border border-cyan-300/45 bg-[#f5f0e6]/95 shadow-[0_0_0_1px_rgba(34,220,255,0.14),0_0_24px_rgba(0,196,255,0.18)]">
            <Image
              src={block.src}
              alt={block.alt}
              width={block.width}
              height={block.height}
              className="block h-auto w-full"
            />
          </div>
          {block.caption ? (
            <figcaption className="text-xs text-cyan-200/70">
              {block.caption}
            </figcaption>
          ) : null}
        </figure>
      );
    case "report": {
      const { paper, label } = block;
      const meta = [
        paper.pages ? `${paper.pages} pages` : null,
        paper.fileSize,
      ]
        .filter(Boolean)
        .join(" · ");
      return (
        <aside
          key={index}
          className="relative my-2 overflow-hidden rounded-2xl border border-cyan-300/50 bg-[linear-gradient(145deg,rgba(0,30,38,0.85),rgba(0,8,18,0.95))] p-6 shadow-[0_0_0_1px_rgba(34,220,255,0.18),0_0_28px_rgba(0,196,255,0.22),inset_0_0_32px_rgba(0,149,255,0.10)]"
        >
          <div className="pointer-events-none absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(88,251,255,0.10)_1px,transparent_1px),linear-gradient(90deg,rgba(88,251,255,0.08)_1px,transparent_1px)] [background-size:18px_18px]" />
          <div className="relative z-10 flex flex-col gap-5 sm:flex-row">
            <div
              aria-hidden
              className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border border-cyan-300/55 bg-cyan-300/10 text-base font-semibold tracking-wide text-cyan-100 shadow-[0_0_14px_rgba(69,229,255,0.22)]"
            >
              PDF
            </div>
            <div className="flex flex-1 flex-col gap-3">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_10px_rgba(57,243,255,0.9)]" />
                <p className="text-[11px] tracking-[0.18em] text-cyan-200/80">
                  {(label ?? "Full Report").toUpperCase()}
                </p>
                {meta ? (
                  <span className="ml-auto text-[11px] tracking-[0.08em] text-cyan-200/60">
                    {meta}
                  </span>
                ) : null}
              </div>
              <h3 className="text-lg font-semibold leading-snug text-cyan-50">
                {paper.title}
              </h3>
              {paper.subtitle ? (
                <p className="text-sm text-cyan-100/80">{paper.subtitle}</p>
              ) : null}
              {(paper.venue || paper.supervisor) && (
                <p className="text-xs text-cyan-200/70">
                  {paper.venue}
                  {paper.venue && paper.supervisor ? " · " : ""}
                  {paper.supervisor
                    ? `Supervisor: ${paper.supervisor}`
                    : ""}
                </p>
              )}
              <div className="flex flex-wrap gap-3 pt-2">
                <a
                  href={paper.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-lg border border-cyan-300/55 bg-[linear-gradient(180deg,rgba(2,30,45,0.55),rgba(0,10,20,0.72))] px-4 py-2 text-sm font-medium text-cyan-100 shadow-[0_0_14px_rgba(69,229,255,0.12)] transition hover:-translate-y-0.5 hover:border-cyan-200 hover:bg-cyan-300/10 hover:text-cyan-50 hover:shadow-[0_0_18px_rgba(69,229,255,0.28)]"
                >
                  Read Paper &rarr;
                </a>
                <a
                  href={paper.url}
                  download
                  className="inline-flex items-center gap-2 rounded-lg border border-cyan-300/35 bg-transparent px-4 py-2 text-sm font-medium text-cyan-100/85 transition hover:-translate-y-0.5 hover:border-cyan-200 hover:text-cyan-50"
                >
                  Download PDF &darr;
                </a>
              </div>
            </div>
          </div>
        </aside>
      );
    }
    case "paragraph":
    default:
      return (
        <p key={index} className="text-cyan-100/85">
          {renderParagraphWithLinks(block.text, block.links)}
        </p>
      );
  }
}

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const project = await getProjectBySlug(slug);
  if (!project) notFound();

  return (
    <main className="min-h-screen bg-batcave px-6 py-10 text-slate-100">
      <div className="mx-auto w-full max-w-4xl">
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-lg border border-cyan-300/55 bg-[linear-gradient(180deg,rgba(2,30,45,0.55),rgba(0,10,20,0.72))] px-4 py-2 text-sm font-medium text-cyan-100 shadow-[0_0_14px_rgba(69,229,255,0.12)] transition hover:-translate-y-0.5 hover:border-cyan-200 hover:bg-cyan-300/10 hover:text-cyan-50 hover:shadow-[0_0_18px_rgba(69,229,255,0.28)]"
          >
            &larr; Back
          </Link>
        </div>

        <article className="relative overflow-hidden rounded-2xl border border-cyan-300/50 bg-[linear-gradient(145deg,rgba(0,30,38,0.78),rgba(0,8,18,0.93))] shadow-[0_0_0_1px_rgba(34,220,255,0.14),0_0_28px_rgba(0,196,255,0.15),inset_0_0_32px_rgba(0,149,255,0.08)]">
          <div className="pointer-events-none absolute inset-0 opacity-25 [background-image:linear-gradient(rgba(88,251,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(88,251,255,0.06)_1px,transparent_1px)] [background-size:18px_18px]" />

          <div className="relative h-80 w-full border-b border-cyan-300/25 bg-black/30 sm:h-96">
            <Image
              src={project.imageSrc}
              alt={project.title}
              fill
              priority
              className="object-cover"
            />
          </div>

          <div className="relative z-10 space-y-6 p-6 sm:p-10">
            <div className="space-y-3">
              <p className="text-xs tracking-[0.18em] text-cyan-200/70">
                {project.date}
              </p>
              <h1 className="text-3xl font-semibold leading-tight tracking-tight text-cyan-50 sm:text-4xl">
                {project.title}
              </h1>
            </div>

            <div className="flex flex-wrap gap-2">
              {project.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-cyan-300/45 bg-cyan-300/10 px-2.5 py-1 text-xs text-cyan-100"
                >
                  {tag}
                </span>
              ))}
            </div>

            {project.githubUrl || project.paperUrl ? (
              <div className="flex flex-wrap gap-3 pt-1">
                {project.githubUrl ? (
                  <a
                    href={project.githubUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-lg border border-cyan-300/55 bg-[linear-gradient(180deg,rgba(2,30,45,0.55),rgba(0,10,20,0.72))] px-4 py-2 text-sm font-medium text-cyan-100 shadow-[0_0_14px_rgba(69,229,255,0.12)] transition hover:-translate-y-0.5 hover:border-cyan-200 hover:bg-cyan-300/10 hover:text-cyan-50 hover:shadow-[0_0_18px_rgba(69,229,255,0.28)]"
                  >
                    GitHub &rarr;
                  </a>
                ) : null}
                {project.paperUrl ? (
                  <a
                    href={project.paperUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-lg border border-cyan-300/55 bg-[linear-gradient(180deg,rgba(2,30,45,0.55),rgba(0,10,20,0.72))] px-4 py-2 text-sm font-medium text-cyan-100 shadow-[0_0_14px_rgba(69,229,255,0.12)] transition hover:-translate-y-0.5 hover:border-cyan-200 hover:bg-cyan-300/10 hover:text-cyan-50 hover:shadow-[0_0_18px_rgba(69,229,255,0.28)]"
                  >
                    Read Paper &rarr;
                  </a>
                ) : null}
              </div>
            ) : null}

            <div className="space-y-5 border-t border-cyan-300/20 pt-6 leading-7">
              {project.content.map((block, index) => renderBlock(block, index))}
            </div>
          </div>
        </article>
      </div>
    </main>
  );
}
