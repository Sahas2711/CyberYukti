/**
 * @type {import('next').NextConfig}
 *
 * Default configuration is unchanged for normal development and hosting.
 * Setting BUILD_STATIC_EXPORT=true produces a fully static build in `out/`
 * which is embedded into the CyberYukti Windows EXE and the Docker image
 * (served by the FastAPI backend from a single process/port).
 */
const isStaticExport = process.env.BUILD_STATIC_EXPORT === "true";

const nextConfig = {
  ...(isStaticExport
    ? {
        output: "export",
        trailingSlash: true,
        images: { unoptimized: true },
      }
    : {}),
};

module.exports = nextConfig;
