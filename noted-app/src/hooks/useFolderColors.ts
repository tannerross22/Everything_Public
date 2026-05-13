const STORAGE_KEY = 'noted_folder_colors'

/** Distinct, vibrant colours that read well on the dark Catppuccin background */
export const FOLDER_PALETTE = [
  '#f38ba8', // red
  '#fab387', // peach
  '#f9e2af', // yellow
  '#a6e3a1', // green
  '#94e2d5', // teal
  '#89dceb', // sky
  '#89b4fa', // blue
  '#f5c2e7', // pink
  '#eba0ac', // maroon
  '#a6d189', // lime
]

/** Colour used for notes not inside any top-level folder */
export const DULL_COLOR = '#585b70'

function load(): Record<string, string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function persist(colors: Record<string, string>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(colors))
}

function pickUnused(existing: Record<string, string>): string {
  const used = new Set(Object.values(existing))
  const free = FOLDER_PALETTE.filter((c) => !used.has(c))
  const pool = free.length > 0 ? free : FOLDER_PALETTE
  return pool[Math.floor(Math.random() * pool.length)]
}

/** Returns the top-level folder path for a given file path, or null if root-level. */
export function getTopLevelFolder(filePath: string, vaultDir: string): string | null {
  if (!filePath.startsWith(vaultDir)) return null
  const sep = vaultDir.includes('\\') ? '\\' : '/'
  const relative = filePath.slice(vaultDir.length).replace(/^[/\\]/, '')
  const firstSep = relative.search(/[/\\]/)
  if (firstSep === -1) return null // file is at vault root
  return vaultDir + sep + relative.slice(0, firstSep)
}

/** Returns true if fullPath is a direct child of vaultDir (i.e. top-level folder). */
export function isTopLevelFolder(fullPath: string, vaultDir: string): boolean {
  const relative = fullPath.startsWith(vaultDir)
    ? fullPath.slice(vaultDir.length).replace(/^[/\\]/, '')
    : ''
  return relative.length > 0 && !relative.includes('\\') && !relative.includes('/')
}

// ── Non-hook helpers so GraphView (which can't call hooks) can share the data ──

export function loadFolderColors(): Record<string, string> {
  return load()
}

export function assignFolderColor(folderPath: string): string {
  const current = load()
  if (current[folderPath]) return current[folderPath]
  const color = pickUnused(current)
  persist({ ...current, [folderPath]: color })
  return color
}

export function removeFolderColor(folderPath: string): void {
  const current = load()
  const { [folderPath]: _, ...rest } = current
  persist(rest)
}
