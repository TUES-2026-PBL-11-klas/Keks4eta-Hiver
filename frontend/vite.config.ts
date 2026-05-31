import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        // 127.0.0.1 (not localhost) so the proxy doesn't resolve to IPv6 ::1
        // and miss an IPv4-only backend.
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
