# Wiki Links

`[[Note Name]]` in any note's body becomes a clickable link to another note. Clicking opens (or creates) the target. This is the headline feature that ties the vault into a navigable network.

## What the user sees

* As they type `[[Foo]]`, the text styles itself: purple, dotted underline, pointer cursor.
* Clicking jumps to `Foo.md` (creating it after a confirm if missing).
* The text on disk stays as literal `[[Foo]]` — no transformation.
* Every cross-reference is drawn in the [[Graph View]].

## End-to-end flow

```
User types [[Foo]]
       │
       ▼
[[Editor Component]] / [[Wiki Link Plugin]] sees the new text, applies decoration
       │
       ▼
.wiki-link <span data-target="Foo"> appears in DOM (no markdown change)
       │
User clicks
       │
       ▼
Plugin's handleClick reads data-target ("Foo"), calls onLinkClick("Foo")
       │
       ▼
[[App Component]] resolveLink("Foo"):
   ├── if notes.find(n => n.name.toLowerCase() === "foo")
   │      → await openNote(match.path) → openNoteInTab(path)
   └── else
       → modal.confirm "Create new note 'Foo'?"
       → if yes: createNewNote("Foo", currentNoteFolder) → openNoteInTab(newPath)
```

## Three places `[[...]]` is parsed

The same regex appears in three places. Keeping them in sync is important:

1. **[[Wiki Link Plugin]]** — `findWikiLinks` in the editor (decoration).
   `/\[\[([^\]]+)\]\]/g`

2. **[[useGraph]]** — building the graph nodes/edges.
   `/\\?\[\\?\[([^\]]+)\]\]/g` (also handles escaped brackets)

3. **[[renameNote]]** — rewriting references after a rename.
   `/\[\[([^\]]+)\]\]/g`

All three are case-sensitive at the regex level. **Name matching** (resolving a link to a note) is **case-insensitive** in [[App Component]]'s `resolveLink` and [[useGraph]]'s `nodesMap`.

## Case-insensitivity

```ts
const match = notes.find(n => n.name.toLowerCase() === linkName.toLowerCase())
```

`[[Apollo]]`, `[[apollo]]`, `[[APOLLO]]` all resolve to the same `Apollo.md`. The display preserves whatever the user typed in the link.

But **rename rewriting** in [[renameNote]] is exact-match:

```ts
if (linkText === oldNameWithoutExt) { … }
```

So renaming `Apollo` doesn't rewrite `[[apollo]]`. This is a known asymmetry.

## What "create" means

If `[[Foo]]` is clicked and `Foo.md` doesn't exist:

1. [[Modal Component]] (via [[useModal]]) asks: "Create new note 'Foo'? Create / Cancel".
2. If confirmed, [[createNote]] makes `Foo.md` next to the **currently open** note (or at vault root if no note is open).
3. The new note opens in a new tab.

The target folder is computed from the active note's path:

```ts
let targetFolder = vaultDir
if (activeNote?.path) {
  const sep = activeNote.path.includes('\\') ? '\\' : '/'
  targetFolder = activeNote.path.substring(0, activeNote.path.lastIndexOf(sep))
}
```

## Where wiki links don't render as links

* **GitHub.** GitHub's markdown renderer shows literal `[[text]]`. To preview Noted-style links on GitHub you'd need a custom renderer.
* **Outside Milkdown.** Any other markdown viewer treats `[[...]]` as plain text.

This is by design: the markdown stays standard CommonMark; wiki links are a Noted convention that lives in the editor's decoration layer only.

## Limitations

* **No alias syntax.** Obsidian supports `[[Target|Display Text]]`. Noted doesn't — the entire `[[…]]` body is both the target and the display text.
* **No section links.** `[[Note#Heading]]` is treated as a name with literal `#` in it (which won't match any real note).
* **No external links.** `[[https://…]]` doesn't open URLs — it's interpreted as a note name with `https://` in it.

## Related

* [[Wiki Link Plugin]] — implementation
* [[useGraph]] — same regex, different purpose
* [[renameNote]] — rewrites references on rename
* [[App Component]] `resolveLink` — the click handler
* [[createNote]] — creates missing targets
* [[Graph View]] — visualizes the link network
