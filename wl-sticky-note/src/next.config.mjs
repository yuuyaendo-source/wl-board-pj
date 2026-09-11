/** @type {import('next').NextConfig} */
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

const nextConfig = {
  basePath,
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