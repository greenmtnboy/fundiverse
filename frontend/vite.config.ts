import { defineConfig } from 'vite'
import electron from 'vite-plugin-electron'
import renderer from 'vite-plugin-electron-renderer'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import commonjsExternals from "vite-plugin-commonjs-externals";
import {builtinModules} from 'module';
// https://vitejs.dev/config/
export default defineConfig({
  optimizeDeps: {
    exclude: builtinModules,
  },
  plugins: [
    vue(),
    vuetify({ styles: { configFile: 'src/styles/settings.scss' } }),
    commonjsExternals({
      externals: builtinModules,
    }),
    electron([
      {
        // Main-Process entry file of the Electron App.
        entry: 'electron/main.ts',
      },
      {
        entry: 'electron/preload.ts',
        onstart(options) {
          // Notify the Renderer-Process to reload the page when the Preload-Scripts build is complete, 
          // instead of restarting the entire Electron App.
          options.reload()
        },
      },
    ]),
    renderer(),
  ],
  build: {
    assetsDir: '.',
    rollupOptions: {
      output: {
        format: 'cjs'
      },
      external: builtinModules
    },
  }
})
