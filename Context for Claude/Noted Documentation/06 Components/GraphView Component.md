# GraphView Component

**Path:** `src/components/GraphView.tsx`

D3 force-directed graph of `[[wiki link]]` relationships between notes. Nodes are notes, edges are link references, sizes encode degree (link count), colors come from [[useFolderColors]].

## Props

```ts
interface GraphViewProps {
  nodes: GraphNode[]        // from useGraph
  links: GraphLink[]        // from useGraph
  onNodeClick: (noteId: string) => void
  folderColors: Record<string, string>
  vaultDir: string
}
```

`nodes` and `links` come from [[useGraph]] in [[App Component]]. `onNodeClick` is wired to `handleGraphNodeClick`, which resolves the link name and opens the note in a tab.

## Mount flow

A single big `useEffect` keyed on `[nodes, links, onNodeClick]` does everything D3-related:

1. **Clear** the SVG (`svg.selectAll('*').remove()`).
2. **Count links per node** to size them.
3. **Deep-copy** nodes/links into D3's mutable form.
4. **Set up zoom**: `d3.zoom().scaleExtent([0.2, 4]).on('zoom', evt => g.attr('transform', evt.transform))`.
5. **Build forces** (see "Forces" below).
6. **Append SVG elements**: lines for links, `<g>` per node containing a circle and label.
7. **Wire hover/click events.**
8. **Start the simulation.** Tick updates positions on every animation frame.
9. **Cleanup** stops the simulation.

The deep copy is essential — D3 mutates `simNodes` in place (adding `x`, `y`, `vx`, `vy`, `fx`, `fy`) and we don't want to pollute the props.

## Forces

```ts
d3.forceSimulation(simNodes)
  .force('link', d3.forceLink(simLinks).id(d => d.id).distance(110))
  .force('charge', d3.forceManyBody().strength(-110))
  .force('center', d3.forceCenter(width/2, height/2))
  .force('radial', d3.forceRadial(d => radialTarget(d), width/2, height/2).strength(0.7))
  .force('folderCluster', folderClusterForce as any)
  .force('collision', d3.forceCollide().radius(d => nodeRadius(d) + 20))
  .alphaDecay(0.04)
```

| Force | Effect |
|---|---|
| `link` | Edges pull connected nodes together with rest length 110px. |
| `charge` (-110) | Repulsion between all nodes; spreads them out. |
| `center` | Mild pull to the canvas center. |
| `radial` | Custom — see below — pulls more-connected nodes toward center, isolated ones to the outer ring. |
| `folderCluster` | Custom — see below — attracts nodes sharing the same folder. |
| `collision` | Prevents node circles from overlapping. |

### Radial layout

```ts
const maxLinks = Math.max(...simNodes.map(d => d.linkCount || 0), 1)
const outerRadius = Math.min(width, height) * 0.38

const radialTarget = (d) => {
  const ratio = (d.linkCount || 0) / maxLinks
  return 40 + (outerRadius - 40) * (1 - ratio)
}
```

Nodes with the most links target a radius of 40px from center; nodes with no links target the outer edge. The result is a hub-and-spoke arrangement where highly connected hubs sit near the middle.

### Folder cluster force

Custom force that attracts nodes from the same top-level folder:

```ts
const folderClusterForce = () => {
  for (const node of simNodes) {
    const nodeFolder = getFolder(node.path)
    for (const other of simNodes) {
      if (node === other) continue
      if (getFolder(other.path) === nodeFolder) {
        // Add attractive velocity toward the other
      }
    }
  }
}
```

`getFolder(path)` returns the path minus the filename. Same-folder pairs attract with strength 0.05.

The visual effect: notes in `Projects/` form a loose cluster, notes in `Daily/` form another, etc.

## Node visuals

* **Radius:** `Math.min(14 + linkCount × 5, 32)`. 0 links → 14px, 1 link → 19px, …, capped at 32px.
* **Color:** resolved via `nodeColor(d)`:
  ```ts
  const folder = getTopLevelFolder(d.path, vaultDir)
  if (!folder) return DULL_COLOR     // root-level files are gray
  return folderColors[folder] ?? DULL_COLOR
  ```
  Uses `getTopLevelFolder` and `DULL_COLOR` from [[useFolderColors]].
* **Hover:** brighter circle (`brighter(0.4)`), 1.2× radius, stroke-width 3.
* **Stroke:** darker version of fill (`darker(0.5)`).

## Labels

Each node has a `<text>` element below the circle (`dy = radius + 16`) showing the note name. Text styling uses the system font stack with `#cdd6f4` (Catppuccin light text).

## Drag

```ts
function drag(simulation) {
  return d3.drag()
    .on('start', evt => { if (!evt.active) simulation.alphaTarget(0.3).restart(); evt.subject.fx = evt.subject.x; evt.subject.fy = evt.subject.y })
    .on('drag',  evt => { evt.subject.fx = evt.x; evt.subject.fy = evt.y })
    .on('end',   evt => { if (!evt.active) simulation.alphaTarget(0); evt.subject.fx = null; evt.subject.fy = null })
}
```

Pinning by setting `fx`/`fy`; releasing on drag end.

## Click

`node.on('click', (_, d) => onNodeClick(d.id))` — passes the note **name** (not path) back up. [[App Component]]'s `handleGraphNodeClick` resolves it via `resolveLink`, which may open or create the note.

## Empty state

If `nodes.length === 0`, the SVG is replaced with:

> No notes to visualize yet.
> Create notes with [[wiki links]] to see the graph.

## Performance

For ~hundreds of notes, performance is fine. The `folderClusterForce` is O(N²) per tick — for a vault with thousands of notes this would become slow. A future optimization would group by folder once per simulation, not per-tick.

## Related

* [[useGraph]] — provides `nodes` and `links`
* [[useFolderColors]] — provides color palette + `getTopLevelFolder`
* [[App Component]] — `handleGraphNodeClick`
* [[Wiki Links]]
* [[Graph View]] — feature view
