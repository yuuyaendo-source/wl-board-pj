import type { NextConfig } from "next";

// 本番で付箋ボードと同一ドメイン運用時は /boards で提供（環境変数より優先して確実に効かせる）
const basePath =
  process.env.NEXT_PUBLIC_BASE_PATH !== undefined
    ? process.env.NEXT_PUBLIC_BASE_PATH
    : process.env.NODE_ENV === "production"
      ? "/boards"
      : "";

const nextConfig: NextConfig = {
  basePath,
};

export default nextConfig;
