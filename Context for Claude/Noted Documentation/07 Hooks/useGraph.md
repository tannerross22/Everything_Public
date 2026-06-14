# useGraph

**Path:** `src/hooks/useGraph.ts`

Parses every note in the vault for `[[wiki links]]` and produces the `nodes` and `links` arrays consumed by [[GraphView Component]].

## Signature

```ts
function useGraph(notes: NoteFile[], vaultDir: string): {
  nodes: GraphNode[]
  links: GraphLink[]
  refresh: () => Promise<void>
}
```

`notes` comes from [[useVault]] (originally [[listNotes]]).

## How it works

```ts
const buildGraph = useCallback(async () => {
  if (!vaultDir || notes.length === 0) {
    setGraphData({ nodes: [], links: [] })
    return
  }

  const nodesMap = new Map<string, GraphNode>()
  const links: GraphLink[] = []

  // Add a node for every real note
  for (const note of notes) {
    nodesMap.set(note.name.toLowerCase(), { id: note.name, path: note.path })
  }

  // Scan every note for [[links]]
  for (const note of notes) {
    const content = await window.api.readNote(note.path)
    const regex = /\\?\[\\?\[([^\]]+)\]\]/g
    let match
    while ((match = regex.exec(content)) !== null) {
      const targetName = match[1].trim()
      const targetKey = targetName.toLowerCase()
      // Only draw links to notes that actually exist
      if (!nodesMap.has(targetKey)) continue
      links.push({ source: note.name, target: nodesMap.get(targetKey)!.id })
    }
  }

  setGraphData({ nodes: Array.from(nodesMap.values()), links })
}, [notes, vaultDir])

useEffect(() => { buildGraph() }, [buildGraph])
```

## The regex

`/\\?\[\\?\[([^\]]+)\]\]/g`

* Allows for backslash-escaped brackets (`\[\[link\]\]`) — needed because some markdown environments escape them.
* Captures the link target between `[[` and `]]`.

## Phantom links

If a `[[link]]` points to a note that doesn't exist, the link is **skipped entirely**. There is no phantom node rendered for nonexistent targets.

An earlier design added gray phantom nodes (per the original [[Noted App]] plan) but the current implementation drops them. To re-enable, push to `nodesMap` even when the note doesn't exist, with `path` undefined; [[GraphView Component]]'s `nodeColor` would then need to handle the undefined path.

## Case-insensitive matching

Wiki link resolution is case-insensitive across the codebase. `[[Apollo]]` and `[[apollo]]` both link to `Apollo.md`. The `toLowerCase()` keying enforces this:

```ts
nodesMap.set(note.name.toLowerCase(), { id: note.name, path: note.path })
//                  ^^^^^^^^^^^^                   ^^^^^^^^^^
//                  used for lookup                  preserves display case
```

## Performance

This is O(N) IPC roundtrips per refresh (one [[readNote and writeNote|readNote]] per note). For a 100-note vault on local SSD, refresh takes ~hundreds of ms.

It runs **on every change** to `notes` or `vaultDir`, which means **every file watcher event** triggers a re-scan. [[App Component]] mitigates by calling `refreshNotes` (which produces a new `notes` reference) only when the user is viewing the graph:

```ts
useEffect(() => {
  if (viewMode === 'graph') refreshNotes()
}, [viewMode])
```

But the regex-scan re-runs regardless when `notes` changes, even if the user is in editor mode. A future optimization would cache content + scan results.

## Where it's used

| Consumer | What it uses |
|---|---|
| [[App Component]] | `const { nodes, links } = useGraph(notes, vaultDir)`; passes both to `<GraphView />` |

`refresh` is returned but **not currently called** — the `useEffect` does its own re-runs.

## Related

* [[GraphView Component]] — the renderer
* [[Wiki Links]]
* [[Graph View]] — feature view
* [[Types]] — `GraphNode`, `GraphLink`
* [[listNotes]] — upstream data source
