# Graph View

The force-directed graph visualization of the vault's `[[wiki link]]` structure. Toggled with **Ctrl+G** or the graph icon in the title bar.

## What it shows

* One node per note. Color = top-level folder ([[useFolderColors]]). Size = number of links (in or out).
* One edge per `[[link]]` between notes.
* Drag any node to pin it. Scroll to zoom. Drag the canvas to pan.
* Click a node to open that note (closes the graph, switches view to editor).

## Where the data comes from

```
notes (from [[useVault]])
       │
       ▼
[[useGraph]] reads every note, regex-scans for [[…]] patterns
       │
       ▼
{ nodes: GraphNode[], links: GraphLink[] }
       │
       ▼
[[GraphView Component]] renders with D3
```

* [[useGraph]] only includes links to notes that **actually exist** — phantom links are silently dropped.
* The scan reads every note's content via [[readNote and writeNote|readNote]] IPC. O(N) calls per refresh.

## Folder clustering

A custom D3 force pulls nodes with the same top-level folder toward each other (strength 0.05). The visual result: notes from `Projects/` group on one side, `Daily/` on another, etc.

See [[GraphView Component]] → "Folder cluster force" for the implementation.

## Radial layout

```
maxLinks → near center (40px radius)
0 links   → outer ring (38% of min canvas dimension)
```

Highly connected hubs sit in the middle, isolated notes float outward. Combined with folder clustering, the result is a "hub at center, clusters in petals" arrangement.

## Coloring

Each node is colored by its **top-level folder** via [[useFolderColors]]:

* `getTopLevelFolder(node.path, vaultDir)` → folder absolute path or null
* `folderColors[folder] ?? DULL_COLOR` → the actual hex

Notes at the vault root (no top-level folder) get the gray `DULL_COLOR`.

## Refresh triggers

[[useGraph]]'s `useEffect` depends on `notes`. Since `notes` is a new array reference every [[refreshNotes|refreshNotes]] call, the graph effectively re-scans on every [[File Watcher]] event.

[[App Component]] partially mitigates this by only refreshing notes **on entering graph view**:

```ts
useEffect(() => {
  if (viewMode === 'graph') refreshNotes()
}, [viewMode])
```

But the [[useGraph]] regex-scan still runs whenever `notes` changes, regardless of view mode.

## Performance

For ~hundreds of notes the simulation runs smoothly at 60 fps. The bottleneck on larger vaults is:

1. **[[useGraph]]'s read pass** — O(N) IPC calls + regex scans per refresh.
2. **Folder cluster force** — O(N²) per tick.

Both could be optimized but aren't pressing for typical vault sizes.

## Empty state

If `nodes.length === 0`:

> No notes to visualize yet.
> Create notes with [[wiki links]] to see the graph.

Shown by [[GraphView Component]] when there are no notes or no links.

## Switching views

* **Ctrl+G** toggles `viewMode` between `'editor'` and `'graph'` in [[App Component]].
* Title bar graph icon does the same.
* Clicking a graph node sets `viewMode = 'editor'` and opens the note in a tab.

## What the graph doesn't show

* **Phantom links.** Links to nonexistent notes are dropped (not rendered as gray nodes). Originally planned per [[Noted App|Phase 5]] but not implemented.
* **Edge direction.** All edges are undirected lines; there's no arrowhead.
* **Edge weight.** All edges are equal stroke width regardless of how many times a note links to another.
* **Backlinks panel.** No "what links to this note" panel inside the editor.

## Related

* [[useGraph]] — the data source
* [[GraphView Component]] — the renderer
* [[useFolderColors]] — color resolution
* [[Wiki Links]]
* [[App Component]] — `viewMode`, Ctrl+G, `handleGraphNodeClick`
