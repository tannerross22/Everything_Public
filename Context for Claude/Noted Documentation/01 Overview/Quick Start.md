# Quick Start

How to run, build, and ship Noted.

## Prerequisites

* Node.js + npm
* Git (must be on `PATH` — Noted shells out via `child_process.execFile('git', …)` for [[Git Sync]])
* Windows (the launchers and packaged target are Windows; nothing else is tested)

## Install

```bash
cd noted-app
npm install
```

This pulls every dependency listed in [[Tech Stack]].

## Run in development

```bash
npm run dev
```

Under the hood (see `vite.config.ts`):

1. **Vite** starts a dev server with HMR for the React renderer.
2. **vite-plugin-electron** compiles [[main.ts]] and [[preload.ts]] to `dist-electron/` and launches Electron.
3. Electron's `BrowserWindow` loads the Vite dev URL (via `VITE_DEV_SERVER_URL`).
4. The [[File Watcher]] starts on the saved vault directory.

You'll see two terminals' worth of logs — Vite output and Electron's stdout (with `[gitSync]`, `[useVault]`, `[FileWatcher]` prefixes from runtime logging).

## Build for distribution

```bash
npm run dist
```

This runs:

1. `npm run build` → `tsc && vite build` → renderer output to `dist/`
2. `npm run build:electron` → main + preload to `dist-electron/`
3. `electron-builder` → reads `package.json` → `build` and produces:
   * an NSIS installer (`Noted Setup-*.exe`)
   * a portable executable
   * Both written to `dist/` at the project root

See [[Build and Config]] for the full `electron-builder` settings.

## Launch from Windows

After install, two convenience launchers live in `noted-app/`:

* **`start-noted.bat`** — opens a console window then Electron
* **`start-noted.vbs`** — silent launch (no console window)

`Create Desktop Shortcut.ps1` pins a shortcut to the Desktop pointing at the silent VBS launcher.

## First-run behavior

When Noted launches for the first time:

1. [[main.ts]] reads `app.getPath('userData')/noted-config.json`. If missing, defaults the vault to the repo root (see [[Vault Configuration]]).
2. The renderer mounts, calls `window.api.getVaultDir()`, and starts [[useVault]].
3. If the vault is **not** a git repository, the [[Git Sync]] setup modal appears (`showGitSetup` in [[App Component]]).
4. The user can either provide a remote URL (triggers [[gitInit]] → [[gitAddRemote]] → [[gitInitialCommit]]) or skip.

## Common npm scripts

| Script | What it does |
|---|---|
| `npm run dev` | Vite dev server + Electron, hot-reload everything |
| `npm run build` | Type-check + production renderer bundle |
| `npm run build:electron` | Type-check main process only |
| `npm run dist` | Full production build + Windows installer |
| `npm run preview` | Preview the built renderer in a browser (rarely useful — needs `window.api`) |

## Related

* [[Project Structure]] — what's where in the repo
* [[Build and Config]] — Vite, electron-builder, tsconfig
* [[main.ts]] — what happens at launch
