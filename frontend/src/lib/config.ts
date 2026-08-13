// Server-side only — the browser never talks to the FastAPI backend
// directly, only to this Next.js app's own Route Handlers, which proxy to
// it. In the combined HF Spaces container, the backend listens on localhost
// only (see root Dockerfile).
export const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";
