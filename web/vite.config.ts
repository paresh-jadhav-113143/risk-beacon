import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/auth": "http://localhost:8000",
      "/agents": "http://localhost:8000",
      "/suppliers": "http://localhost:8000",
      "/review-queue": "http://localhost:8000",
      "/notifications": "http://localhost:8000",
      "/health": "http://localhost:8000"
    }
  }
});
