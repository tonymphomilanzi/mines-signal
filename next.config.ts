import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "127.0.0.1",
    "localhost",
    "https://mines-signal-production.up.railway.app"
  ],
};

export default nextConfig;
