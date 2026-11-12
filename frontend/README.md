# PharmaAssist UI

Single-page Next.js app (App Router, TypeScript, Tailwind): one request box plus optional patient details.
The agent decides how to handle each request (label search, prescription check, or draft). It calls `POST /ask/stream` and shows the live trace (plan, tool calls, critic
review), the cited answer, the validation verdict, and the cited passages.

```bash
npm ci
npm run dev     # http://localhost:3000, talks to the API on http://localhost:8000 (CORS allowed in dev)
npm run lint
npm run build   # static export to out/, served by FastAPI at / (see the root Dockerfile)
```
