import type { NextConfig } from "next";

// 余分な引用符を除去
const rawBasePath = (process.env.NEXT_PUBLIC_BASE_PATH || "").replace(/['"]/g, "").trim();

// 環境変数がある場合のみ basePath を適用し、ない場合は undefined（ルート直下）にする
const basePath = rawBasePath !== "" ? (rawBasePath.startsWith("/") ? rawBasePath : `/${rawBasePath}`) : undefined;

const nextConfig: NextConfig = {
  ...(basePath ? { basePath } : {}),
  // /task へのアクセスを /taskboard へ自動転送
  async redirects() {
    return [
      {
        source: "/task",
        destination: "/taskboard",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;