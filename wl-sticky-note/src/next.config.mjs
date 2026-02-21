/** @type {import('next').NextConfig} */
// AI-Board が HTTPS で動作する場合は https に変更（自己証明書は NODE_TLS_REJECT_UNAUTHORIZED=0 で許可）
// 本番で Nginx の /board/ 配下で提供する場合は NEXT_PUBLIC_BASE_PATH=/board でビルド（アセットが /board/_next/ になる）
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

const nextConfig = {
  basePath,
  async redirects() {
    // basePath あり（本番 /board）のときは /board を /board/wl へ
    const dest = basePath ? `${basePath}/wl` : '/board/wl';
    return [
      { source: '/', destination: dest, permanent: false },
    ];
  },
  async rewrites() {
    return [
      {
        source: '/api/proxy/:path*',
        destination: 'https://127.0.0.1:5000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
