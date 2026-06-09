/**
 * Content data-access layer (Flow 1: database -> UI).
 *
 * The pages fetch resume + article content from the FastAPI content API, which
 * reads it from Postgres. The old `src/data/resume.json` and `src/data/projects.ts`
 * files are NO LONGER imported by the running app — they were one-time seed input
 * (now in `backend/seed_data/`, loaded via `python -m backend.seed_content`).
 *
 * These helpers run only in Server Components, and every fetch opts into Next's
 * Data Cache for an hour (`next: { revalidate }`). The first request after the
 * window lapses renders from the DB; the result is then reused for every other
 * request until it goes stale (refreshed in the background). That takes the
 * Python function + Postgres off the hot path for the vast majority of requests,
 * which is what removes the multi-second cold-start hit visitors were seeing.
 *
 * Nothing is fetched at build time — the content API isn't reachable during a
 * Vercel build — so the article route prerenders no params (`generateStaticParams`
 * returns []) and the home/resume routes render on demand. They still avoid the
 * cold start because the underlying fetch is served from the Data Cache.
 */

export type PaperMeta = {
  title: string;
  subtitle?: string;
  venue?: string;
  supervisor?: string;
  pages?: number;
  fileSize?: string;
  url: string;
};

export type ContentBlock =
  | { type: "paragraph"; text: string; links?: { text: string; href: string }[] }
  | { type: "heading"; text: string }
  | { type: "list"; items: string[] }
  | { type: "video"; src: string; poster?: string; caption?: string }
  | {
      type: "image";
      src: string;
      alt: string;
      caption?: string;
      width: number;
      height: number;
    }
  | { type: "report"; label?: string; paper: PaperMeta };

export type ArticleSummary = {
  slug: string;
  title: string;
  date: string;
  description: string;
  imageSrc: string;
  tags: string[];
};

export type Article = ArticleSummary & {
  githubUrl?: string;
  paperUrl?: string;
  content: ContentBlock[];
};

export type Reference = {
  name: string;
  profileUrl: string;
  role: string;
  email: string;
};

export type Resume = {
  personal: {
    name: string;
    summary: string;
    contact: { label: string; href: string }[];
  };
  skills: { label: string; value: string }[];
  education: {
    school: string;
    location: string;
    degree: string;
    details: string;
    dates: string;
    reference?: Reference;
  }[];
  certifications: { title: string; issued: string; href?: string }[];
  experience: {
    company: string;
    companyUrl?: string;
    location: string;
    role: string;
    dates: string;
    bullets: string[];
    reference?: Reference;
  }[];
  projects: { name: string; url?: string; bullets: string[] }[];
};

/**
 * Where to reach the content API.
 *  - dev: hit FastAPI directly (uvicorn on :8000); avoids relying on the Next
 *    rewrite for server-side fetches, which only proxies browser requests.
 *  - prod (Vercel): the public production domain. Vercel routes /api/* to the
 *    Python function via vercel.json; server-side fetch needs an absolute URL.
 */
function apiBase(): string {
  if (process.env.CONTENT_API_BASE_URL) return process.env.CONTENT_API_BASE_URL;
  if (process.env.NODE_ENV === "development") {
    return process.env.BACKEND_DEV_URL ?? "http://127.0.0.1:8000";
  }
  // Must target the canonical production domain, NOT VERCEL_URL. VERCEL_URL is
  // the per-deployment hostname, which Deployment Protection answers with a 401
  // — so a server-side self-fetch to it throws and the page 500s.
  // VERCEL_PROJECT_PRODUCTION_URL is the unprotected production domain.
  const host =
    process.env.VERCEL_PROJECT_PRODUCTION_URL || process.env.VERCEL_URL;
  if (host) return `https://${host}`;
  return "";
}

/**
 * How long rendered content stays cached at the CDN before Next refreshes it in
 * the background (stale-while-revalidate). Resume + articles change rarely, so
 * an hour of staleness buys near-instant loads. The `content` cache tag lets a
 * future seed/admin hook call `revalidateTag("content")` to refresh on demand.
 */
export const CONTENT_REVALIDATE = 3600;

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    next: { revalidate: CONTENT_REVALIDATE, tags: ["content"] },
  });
  if (!res.ok) throw new Error(`content API ${path} -> ${res.status}`);
  return (await res.json()) as T;
}

export async function getResume(): Promise<Resume> {
  return getJson<Resume>("/api/content/resume");
}

export async function getProjects(): Promise<ArticleSummary[]> {
  const data = await getJson<{ projects: ArticleSummary[] }>(
    "/api/content/projects"
  );
  return data.projects;
}

export async function getProjectBySlug(slug: string): Promise<Article | null> {
  const res = await fetch(
    `${apiBase()}/api/content/projects/${encodeURIComponent(slug)}`,
    { next: { revalidate: CONTENT_REVALIDATE, tags: ["content"] } }
  );
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`content API project ${slug} -> ${res.status}`);
  return (await res.json()) as Article;
}
