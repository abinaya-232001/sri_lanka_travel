import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(dir, '../../shared/frontend');
const unifiedRoot = path.resolve(dir, '../../../tourism-unified');
const unifiedSrc = path.resolve(unifiedRoot, 'src');

export default defineConfig(({ mode }) => {
  // Settings come from environment variables (or frontend/.env):
  //   VITE_API_TARGET        where the Flask API runs (default: standalone app.py on port 5000)
  //   VITE_API_STRIP_PREFIX  "1" (default): the pages call /api/risk/<route>; the prefix is removed
  //                          because the standalone app.py serves /sites, /predict, ... without it.
  //                          "0": keep the prefix (for the unified group backend, which mounts /api/risk).
  const env = loadEnv(mode, dir, '');
  const apiTarget = env.VITE_API_TARGET || 'http://127.0.0.1:5000';
  const stripPrefix = env.VITE_API_STRIP_PREFIX !== '0';

  return {
    plugins: [
      react(),
    ],
    optimizeDeps: {
      esbuildOptions: {
        loader: { '.js': 'jsx' },
      },
    },
    esbuild: {
      include: /\.(js|jsx)$/,
      exclude: [],
      loader: 'jsx',
    },
    publicDir: path.resolve(unifiedRoot, 'public'),
    resolve: {
      alias: {
        '@shared': frontendRoot,
        '@risk': unifiedSrc,
        react: path.resolve(dir, 'node_modules/react'),
        'react-dom': path.resolve(dir, 'node_modules/react-dom'),
        'react-router-dom': path.resolve(dir, 'node_modules/react-router-dom'),
        'lucide-react': path.resolve(dir, 'node_modules/lucide-react'),
        recharts: path.resolve(dir, 'node_modules/recharts'),
      },
      dedupe: ['react', 'react-dom', 'react-router-dom', 'lucide-react', 'recharts'],
    },
    server: {
      port: 5182,
      strictPort: true,
      fs: { allow: [dir, frontendRoot, unifiedRoot] },
      proxy: {
        '/api/risk': {
          target: apiTarget,
          changeOrigin: true,
          ...(stripPrefix ? { rewrite: (p) => p.replace(/^\/api\/risk/, '') } : {}),
        },
      },
    },
  };
});
