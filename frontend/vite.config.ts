import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "0.0.0.0",
    allowedHosts: ["dash.aquantlens.com", "ta.aquantlens.com"],
    proxy: {
      "/api": {
        target: process.env.AQUANTLENS_API_PROXY_TARGET ?? "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          if (id.includes("lucide-react")) return "vendor-icons";
          if (id.includes("@tanstack/react-table")) return "vendor-table";
          if (id.includes("@radix-ui") || id.includes("radix-ui")) return "vendor-radix";
          if (id.includes("react") || id.includes("i18next")) return "vendor-react";
          return "vendor";
        },
      },
    },
  },
});
