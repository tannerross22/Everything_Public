# Vault Configuration

How Noted decides which directory is the user's vault, and how that choice persists across launches.

## The config file

Path: `app.getPath('userData') + '/noted-config.json'`

On Windows this is typically `%APPDATA%\Noted\noted-config.json`.

Schema:

```json
{ "vaultDir": "C:\\Users\\tanne\\Everything_Public" }
```

That's the entire schema. Anything else in the file is ignored.

## `loadConfig()` in [[main.ts]]

```ts
function loadConfig(): { vaultDir: string } {
  try {
    if (fs.existsSync(configPath)) {
      return JSON.parse(fs.readFileSync(configPath, 'utf-8'))
    }
  } catch {}
  // Default: two levels above __dirname (which is dist-electron/)
  const defaultVault = path.resolve(__dirname, '..', '..')
  return { vaultDir: defaultVault }
}
```

Three behaviors:

1. **File exists and parses cleanly.** Returns the persisted `vaultDir`.
2. **File is missing.** Returns the default — `path.resolve(__dirname, '..', '..')`.
3. **File is corrupted (JSON parse error).** Silently caught; returns the default.

### The default

`__dirname` at runtime is `<repo>/noted-app/dist-electron/` (where `main.js` lives after bundling). Going up twice gives `<repo>/` — i.e. `Everything_Public`. This is intentional: on a fresh checkout, the app opens the surrounding repo as the vault, so the user's existing notes and the app code share a Git history.

### Caveat in packaged builds

When `app.isPackaged === true`, `__dirname` points into the `app.asar` archive rather than the repo. The current default may not resolve to a sensible directory there. The original design (`Noted App.md`) hints that the intention was "if packaged, use Documents, else use the repo root" — but the current code only handles the repo case. For packaged installs the user gets whatever path resolves and is expected to change it via the picker. (Future improvement: branch on `app.isPackaged`.)

## `saveConfig(config)` in [[main.ts]]

```ts
function saveConfig(config: { vaultDir: string }) {
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8')
}
```

Synchronous, pretty-printed. Called from the `vault:selectDir` handler after the user picks a folder.

## Changing the vault at runtime

The user clicks the vault label in the [[Sidebar Component]] footer → `onChangeVault` → `useVault.changeVaultDir`:

```ts
const newDir = await window.api.selectVaultDir()
if (newDir) {
  setVaultDir(newDir)
  setActiveNote(null)
  window.api.setTitle('Noted')
}
```

`selectVaultDir` in [[main.ts]]:

```ts
ipcMain.handle('vault:selectDir', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory'],
    title: 'Select Vault Directory',
  })
  if (!result.canceled && result.filePaths[0]) {
    const vaultDir = result.filePaths[0]
    saveConfig({ vaultDir })
    startWatcher(vaultDir)   // restart watcher on new path
    return vaultDir
  }
  return null
})
```

Three side effects in sequence:
1. **Persist** to `noted-config.json`.
2. **Restart the [[File Watcher]]** on the new path.
3. **Return** the new path to the renderer, which updates `vaultDir` state and clears the active note.

The full file tree refresh happens automatically because [[useVault]] has a `refreshNotes` effect keyed on `vaultDir`.

## Reading the vault on first launch

[[App Component]] mounts → [[useVault]] runs `window.api.getVaultDir()` → `loadConfig().vaultDir`. The result becomes the initial `vaultDir` state and triggers `refreshNotes` to populate the sidebar.

## Multiple Noted instances

Noted holds a single config file globally, not per-window. If you somehow opened two Noted windows pointing at different vaults, they would race on writes to `noted-config.json`. In practice the app only ever has one window, so this is theoretical.

## Related

* [[main.ts]] — `loadConfig` / `saveConfig` / `selectVaultDir`
* [[File Format and Vault]] — what counts as a vault
* [[useVault]] — `changeVaultDir`
* [[Sidebar Component]] — the vault button in the footer
