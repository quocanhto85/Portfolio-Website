import type { NextConfig } from "next";

const BACKEND_DEV_URL =
  process.env.BACKEND_DEV_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // The FastAPI backend registers Alfred's routes both with and without a
  // trailing slash, so a POST to /api/alfred/chat/ never triggers a redirect.
  // We keep slashes intact end-to-end to preserve the POST body regardless.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    // In development, the FastAPI backend runs on :8000. In production on
    // Vercel, the rewrite in vercel.json routes /api/* to api/index.py, so
    // these dev rewrites are scoped to NODE_ENV=development.
    if (process.env.NODE_ENV !== "development") return [];
    return [
      {
        source: "/api/alfred/:path*",
        destination: `${BACKEND_DEV_URL}/api/alfred/:path*`,
      },
      {
        source: "/api/content/:path*",
        destination: `${BACKEND_DEV_URL}/api/content/:path*`,
      },
      {
        source: "/api/health",
        destination: `${BACKEND_DEV_URL}/api/health`,
      },
      {
        source: "/api/projects",
        destination: `${BACKEND_DEV_URL}/api/projects`,
      },
    ];
  },
};

export default nextConfig;
