/**
 * Content data-access layer (Flow 1: database -> UI).
 *
 * The pages fetch resume + article content from the FastAPI content API, which
 * reads it from Postgres. The old `src/data/resume.json` and `src/data/projects.ts`
 * files are NO LONGER imported by the running app — they were one-time seed input
 * (now in `backend/seed_data/`, loaded via `python -m backend.seed_content`).
 *
 * These helpers run only in Server Components. All fetches are `no-store`, so the
 * pages render at request time straight from the DB; nothing is baked into the
 * bundle at build (the API isn't reachable during a Vercel build anyway).
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
  projects: { name: string; bullets: string[] }[];
};

/**
 * Where to reach the content API.
 *  - dev: hit FastAPI directly (uvicorn on :8000); avoids relying on the Next
 *    rewrite for server-side fetches, which only proxies browser requests.
 *  - prod (Vercel): same-deployment URL; Vercel routes /api/* to the Python
 *    function via vercel.json. Server-side fetch needs an absolute URL.
 */
function apiBase(): string {
  if (process.env.CONTENT_API_BASE_URL) return process.env.CONTENT_API_BASE_URL;
  if (process.env.NODE_ENV === "development") {
    return process.env.BACKEND_DEV_URL ?? "http://127.0.0.1:8000";
  }
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return "";
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, { cache: "no-store" });
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
    { cache: "no-store" }
  );
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`content API project ${slug} -> ${res.status}`);
  return (await res.json()) as Article;
}
