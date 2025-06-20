/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  experimental: {
    outputFileTracingRoot: undefined,
  },
  images: {
    domains: ['localhost'], // Add domains for image hosting if needed
    unoptimized: true, // Dla środowiska Docker
  },
  async rewrites() {
    return [
      {
        // Proxy API requests to the backend during development
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'production'
          ? 'http://backend:8000/api/:path*'
          : 'http://localhost:8000/api/:path*',
      },
    ];
  },
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    // !! WARN !!
    ignoreBuildErrors: true,
  },
  // Dodatkowe ustawienia dla Docker
  poweredByHeader: false,
  compress: true,
  generateEtags: false,
};

module.exports = nextConfig;
