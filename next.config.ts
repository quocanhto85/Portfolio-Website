import type { NextConfig } from "next";

const DJANGO_DEV_URL =
  process.env.DJANGO_DEV_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Django's APPEND_SLASH forwards POST 405s when the URL is missing a
  // trailing slash. We keep slashes intact end-to-end so Alfred's POST sails
  // through to Django without a redirect dance.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    // In development, the Django backend runs on :8000. In production on
    // Vercel, the rewrite in vercel.json routes /api/* to api/index.py, so
    // these dev rewrites are scoped to NODE_ENV=development.
    if (process.env.NODE_ENV !== "development") return [];
    return [
      {
        source: "/api/alfred/:path*",
        destination: `${DJANGO_DEV_URL}/api/alfred/:path*`,
      },
      {
        source: "/api/health",
        destination: `${DJANGO_DEV_URL}/api/health`,
      },
      {
        source: "/api/projects",
        destination: `${DJANGO_DEV_URL}/api/projects`,
      },
    ];
  },
};

export default nextConfig;
