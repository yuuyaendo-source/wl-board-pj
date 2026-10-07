import type { NextConfig } from "next";

// 余分な引用符を除去
const rawBasePath = (process.env.NEXT_PUBLIC_BASE_PATH || "").replace(/['"]/g, "").trim();

// クォートや空文字を考慮して安全に basePath を設定
const basePath =
  rawBasePath !== ""
    ? (rawBasePath.startsWith("/") ? rawBasePath : `/${rawBasePath}`)
    : process.env.NODE_ENV === "production"
      ? "/boards"
      : "";

const nextConfig: NextConfig = {
  basePath,
};

export default nextConfig;