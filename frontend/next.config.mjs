/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Every page in the console is a client component talking to the FastAPI
  // service over NEXT_PUBLIC_API_URL, so there is no server work to host:
  // exporting it lets the console be served as a static site from a CDN.
  output: "export",
  // Emit directory-style routes (out/verify/index.html) so a static host
  // resolves /verify without per-route rewrite rules.
  trailingSlash: true,
  images: { unoptimized: true }
};

export default nextConfig;
