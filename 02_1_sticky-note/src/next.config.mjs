/** @type {import('next').NextConfig} */
// AI-Board が HTTPS で動作する場合は https に変更（自己証明書は NODE_TLS_REJECT_UNAUTHORIZED=0 で許可）
const nextConfig = {
  async redirects() {
    return [
      { source: '/', destination: '/board/wl', permanent: false },
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
