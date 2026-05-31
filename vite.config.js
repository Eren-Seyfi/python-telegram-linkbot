import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  base: './',
  build: {
    outDir: resolve(__dirname, 'static/dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'frontend/main.js'),
      output: {
        entryFileNames: 'main.js',
        chunkFileNames: 'chunk-[hash].js',
        assetFileNames: ({ name }) => {
          if (/\.(woff2?|ttf|eot)(\?.*)?$/.test(name || '')) return 'fonts/[name][extname]'
          if (/\.css$/.test(name || ''))                        return 'main.css'
          return '[name][extname]'
        },
      },
    },
  },
})
