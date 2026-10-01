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
    host: true,
    port: 5173,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          reactflow: ["reactflow"],
          recharts: ["recharts"],
          vendor: ["react", "react-dom", "react-router-dom", "@tanstack/react-query", "zustand", "axios"],
        },
      },
    },
  },
});
