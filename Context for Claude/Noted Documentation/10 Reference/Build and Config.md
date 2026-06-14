# Build and Config

The configuration files that drive Noted's dev and production builds.

## `package.json` (highlights)

```json
{
  "name": "noted",
  "version": "1.0.0",
  "main": "dist-electron/main.js",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "build:electron": "tsc -p tsconfig.json",
    "dist": "npm run build && npm run build:electron && electron-builder",
    "preview": "vite preview"
  },
  "dependencies": { /* see [[Tech Stack]] */ },
  "devDependencies": { /* see [[Tech Stack]] */ },
  "build": { /* electron-builder config — see below */ }
}
```

* `main` — points at the built main-process entry (`dist-electron/main.js`).
* See [[Tech Stack]] for the dependency list.

## `vite.config.ts`

```ts
export default defineConfig({
  plugins: [
    react(),
    electron([
      {
        entry: 'electron/main.ts',
        vite: {
          build: {
            outDir: 'dist-electron',
            rollupOptions: { external: ['electron', 'chokidar'] },
          },
        },
      },
      {
        entry: 'electron/preload.ts',
        onstart(args) { args.reload() },          // reload renderer when preload changes
        vite: {
          build: {
            outDir: 'dist-electron',
            rollupOptions: { external: ['electron'] },
          },
        },
      },
    ]),
    renderer(),
  ],
})
```

Three plugins:

1. **`react`** — JSX + Fast Refresh for the renderer.
2. **`electron`** — Compiles `electron/main.ts` and `electron/preload.ts` to `dist-electron/` and launches Electron in dev mode. On preload changes, reloads the renderer.
3. **`renderer`** — Allows renderer code to import Node-ish packages safely. (Mostly a no-op given `nodeIntegration: false`.)

`rollupOptions.external` lists Node modules that **shouldn't** be bundled — Electron's `require('electron')` and chokidar should resolve at runtime via Node, not be inlined.

## TypeScript configs

### `tsconfig.json`
Renderer + Electron output. The renderer side is bundled by Vite; the Electron side compiles with `tsc -p tsconfig.json` (or via vite-plugin-electron in dev mode).

### `tsconfig.node.json`
For Vite's own config file (which runs in Node, not the browser). Separate from the renderer config so it can use `module: "ESNext"` for the build tool itself.

## `electron-builder` (`package.json` → `build`)

```json
{
  "appId": "com.noted.app",
  "productName": "Noted",
  "files": ["dist", "dist-electron", "node_modules", "package.json"],
  "win": {
    "target": [
      { "target": "nsis", "arch": ["x64"] },
      "portable"
    ],
    "icon": "electron/app.png",
    "sign": null
  },
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": true,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true,
    "shortcutName": "Noted"
  }
}
```

* **`files`** — what to include in the app bundle. Note `node_modules` is included whole (no pruning).
* **`win.target`** — two outputs:
  * NSIS installer (`Noted Setup-X.Y.Z.exe`).
  * Portable EXE (`Noted-X.Y.Z.exe` — runs without install).
* **`win.sign: null`** — no code signing. Windows SmartScreen will warn the user on first launch; they have to click "Run anyway."
* **`nsis`** — non-one-click installer with directory selection, desktop and start menu shortcuts.

## Build outputs

| File | From | Bundles |
|---|---|---|
| `dist/index.html` | Vite | Renderer entry, references hashed JS/CSS bundles |
| `dist/assets/*.js, *.css` | Vite | Bundled React + Milkdown + D3 |
| `dist-electron/main.js` | vite-plugin-electron | Compiled main process |
| `dist-electron/preload.js` | vite-plugin-electron | Compiled preload |
| Installer `.exe` (after `npm run dist`) | electron-builder | Everything above + node_modules + Electron runtime |

## Dev mode launch

```
npm run dev
   │
   ├── vite serves the renderer on http://localhost:5173
   │
   └── vite-plugin-electron compiles main + preload and launches:
        electron dist-electron/main.js
        │
        └── main reads VITE_DEV_SERVER_URL → loadURL('http://localhost:5173')
            (HMR works because Vite serves the bundle)
```

The two halves (renderer and Electron) run concurrently. Changes to renderer code hot-reload; changes to main/preload trigger an Electron restart.

## Production launch

```
npm run dist
   │
   ├── npm run build → tsc + vite build → renderer bundle in dist/
   │
   ├── npm run build:electron → tsc → main + preload in dist-electron/
   │
   └── electron-builder
        ├── reads build.files → packages dist/, dist-electron/, node_modules/, package.json
        └── creates NSIS installer + portable .exe in dist/
```

## Windows launchers (project root)

* `start-noted.bat` — opens Electron with a visible console window (useful for `console.log` output).
* `start-noted.vbs` — silent launch (calls the bat without a console).
* `Create Desktop Shortcut.ps1` — creates a Desktop shortcut pointing at the VBS.

These exist for users who installed from source rather than the NSIS installer.

## Related

* [[Tech Stack]]
* [[Quick Start]]
* [[Project Structure]]
