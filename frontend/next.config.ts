import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export to `out/`; FastAPI serves it at `/` in the container (single origin, no CORS).
  output: "export",
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
