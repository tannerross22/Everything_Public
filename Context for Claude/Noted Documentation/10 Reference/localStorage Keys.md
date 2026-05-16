# localStorage Keys

Noted persists a small amount of UI state in the renderer's `localStorage`. The bigger persistence (`vaultDir`) is in the main process's `noted-config.json` ([[Vault Configuration]]).

## All keys

| Key | Type | Default | Module | Purpose |
|---|---|---|---|---|
| `noted_sidebar_width` | number (as string) | `260` | `src/utils/sidebarStorage.ts` | Sidebar pixel width |
| `noted_sidebar_collapsed` | JSON boolean | `false` | `src/utils/sidebarStorage.ts` | Sidebar collapsed flag |
| `noted_folder_colors` | JSON `Record<string, string>` | `{}` | `src/hooks/useFolderColors.ts` | Folder path → hex color |

That's it. Three keys.

## `noted_sidebar_width` and `noted_sidebar_collapsed`

Written together by `saveSidebarState(width, collapsed)`:

```ts
localStorage.setItem('noted_sidebar_width', String(width))
localStorage.setItem('noted_sidebar_collapsed', JSON.stringify(collapsed))
```

Read by `loadSidebarState()` on [[App Component]] mount. See [[Sidebar Resize and Collapse]].

## `noted_folder_colors`

A map: absolute folder path → palette hex color.

```ts
// example contents
{
  "C:\\Users\\tanne\\Everything_Public\\Projects": "#f38ba8",
  "C:\\Users\\tanne\\Everything_Public\\Daily": "#a6e3a1"
}
```

Managed by [[useFolderColors]]: read/written by `assignFolderColor`, `removeFolderColor`, and `loadFolderColors` (the renderer-side helpers).

* New keys added when a top-level folder is created.
* No key removal — deleted folders leave stale entries.

See [[Folder Colors]].

## Persistence boundaries

| Lives in | Persists across | Doesn't persist across |
|---|---|---|
| `localStorage` | Restarts (same OS user, same Electron build) | Vault changes (the values are global, not per-vault) |
| `noted-config.json` | Restarts | OS user changes |

If a user changes the vault directory, **folder colors stay assigned to the old paths**. The new vault starts fresh (no entries exist for its folders yet, so [[App Component]] assigns colors on next mount).

## Where localStorage is not used

* Open tabs are **not** persisted. Closing the app forgets which tabs were open.
* Active note is **not** persisted. Opening the app shows the empty state.
* Sort order is **not** persisted (lives only in React state).
* View mode (editor/graph) is **not** persisted.
* Sidebar selection (multi-select) is **not** persisted.

These are deliberate — they aren't user preferences, they're session state.

## When localStorage is unavailable

In a hardened browser context (incognito, certain sandbox modes), `localStorage` can throw on access. Both load and save call sites use try/catch and silently fall back to defaults / no-op:

```ts
try { localStorage.setItem(…) } catch {}
```

In Electron with the current `webPreferences`, localStorage is always available — the guard is defensive.

## Related

* [[Sidebar Resize and Collapse]]
* [[useFolderColors]]
* [[Vault Configuration]] — the main-process equivalent persistence
