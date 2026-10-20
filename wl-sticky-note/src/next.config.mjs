/** @type {import('next').NextConfig} */
// 不要なクォート文字を除去し、'/' から始まる有効なパスのみ basePath に設定します
const rawBasePath = (process.env.NEXT_PUBLIC_BASE_PATH || '').replace(/['"]/g, '').trim();
const basePath = rawBasePath.startsWith('/') ? rawBasePath : undefined;

const nextConfig = {
  ...(basePath ? { basePath } : {}),
};

export default nextConfig;