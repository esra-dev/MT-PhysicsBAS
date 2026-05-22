import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The Live Mode talks to a Node-RED simulator. We proxy /sim/* through Vite
// to avoid CORS issues. Default points at the custom2 lab on port 1882; you can
// override with the SIM_URL environment variable when starting `npm run dev`.
const SIM_URL = process.env.SIM_URL || 'http://localhost:1882';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      '/sim': {
        target: SIM_URL,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/sim/, ''),
      },
    },
  },
});
