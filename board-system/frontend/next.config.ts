import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 本番で付箋ボードと同一ドメイン運用時、付箋ボードが /_next/ を使うため
  // Board System は /boards 以下にまとめ、アセットは /boards/_next/ で提供する。
  // ビルド時に NEXT_PUBLIC_BASE_PATH=/boards を指定すること。
  basePath: process.env.NEXT_PUBLIC_BASE_PATH ?? "",
};

export default nextConfig;
