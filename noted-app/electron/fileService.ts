import fs from 'fs'
import path from 'path'
import { execFile } from 'child_process'

export interface NoteFileData {
  name: string
  path: string
  modifiedAt: number
}

export interface FileTreeNode {
  name: string
  type: 'file' | 'folder'
  path: string
  children?: FileTreeNode[]
  modifiedAt?: number
}

/**
 * List all .md files in the vault directory (flat list for backward compatibility)
 */
export function listNotes(vaultDir: string): NoteFileData[] {
  if (!fs.existsSync(vaultDir)) return []

  const notes: NoteFileData[] = []

  // Recursively find all .md files
  function walkDir(dir: string) {
    const entries = fs.readdirSync(dir, { withFileTypes: true })

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name)

      if (entry.isFile() && entry.name.endsWith('.md')) {
        const stat = fs.statSync(fullPath)
        notes.push({
          name: entry.name.replace(/\.md$/, ''),
          path: fullPath,
          modifiedAt: stat.mtimeMs,
        })
      } else if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules' && entry.name !== 'dist' && entry.name !== 'dist-electron') {
        walkDir(fullPath)
      }
    }
  }

  walkDir(vaultDir)
  return notes.sort((a, b) => b.modifiedAt - a.modifiedAt)
}

/**
 * Build a file tree structure (folders and notes) for the sidebar
 */
export function buildFileTree(vaultDir: string): FileTreeNode[] {
  if (!fs.existsSync(vaultDir)) return []

  function walkDir(dir: string): FileTreeNode[] {
    const entries = fs.readdirSync(dir, { withFileTypes: true })
    const nodes: FileTreeNode[] = []

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name)

      // Skip hidden and system files/folders
      if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === 'dist' || entry.name === 'dist-electron') {
        continue
      }

      if (entry.isFile() && entry.name.endsWith('.md')) {
        const stat = fs.statSync(fullPath)
        nodes.push({
          name: entry.name.replace(/\.md$/, ''),
          type: 'file',
          path: fullPath,
          modifiedAt: stat.mtimeMs,
        })
      } else if (entry.isDirectory()) {
        const children = walkDir(fullPath)
        nodes.push({
          name: entry.name,
          type: 'folder',
          path: fullPath,
          children,
        })
      }
    }

    // Sort: folders first, then files by modification time
    return nodes.sort((a, b) => {
      if (a.type !== b.type) return a.type === 'folder' ? -1 : 1
      if (a.type === 'file') return (b.modifiedAt || 0) - (a.modifiedAt || 0)
      return a.name.localeCompare(b.name)
    })
  }

  return walkDir(vaultDir)
}

/**
 * Read a note's content
 */
export function readNote(filePath: string): string {
  return fs.readFileSync(filePath, 'utf-8')
}

/**
 * Write content to a note file
 */
export function writeNote(filePath: string, content: string): void {
  const dir = path.dirname(filePath)
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true })
  }
  fs.writeFileSync(filePath, content, 'utf-8')
}

/**
 * Create a new note, returns the full path
 */
export function createNote(vaultDir: string, name: string): string {
  let fileName = `${name}.md`
  let fullPath = path.join(vaultDir, fileName)

  // Handle name collisions
  let counter = 1
  while (fs.existsSync(fullPath)) {
    fileName = `${name} ${counter}.md`
    fullPath = path.join(vaultDir, fileName)
    counter++
  }

  fs.writeFileSync(fullPath, `# ${name}\n\n`, 'utf-8')
  return fullPath
}

/**
 * Delete a note file
 */
export function deleteNote(filePath: string): void {
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath)
  }
}

/**
 * Create a new folder
 */
export function createFolder(folderPath: string): string {
  if (!fs.existsSync(folderPath)) {
    fs.mkdirSync(folderPath, { recursive: true })
  }
  return folderPath
}

/**
 * Delete a folder and all its contents recursively
 */
export function deleteFolder(folderPath: string): void {
  fs.rmSync(folderPath, { recursive: true, force: true })
}

/**
 * Move a note to a different folder
 */
export function moveNote(oldPath: string, newFolderPath: string): string {
  const fileName = path.basename(oldPath)
  const newPath = path.join(newFolderPath, fileName)

  // Ensure destination folder exists
  if (!fs.existsSync(newFolderPath)) {
    fs.mkdirSync(newFolderPath, { recursive: true })
  }

  // Move the file
  fs.renameSync(oldPath, newPath)
  return newPath
}

/**
 * Rename a note and update all [[references]] in other notes
 */
export function renameNote(vaultDir: string, oldPath: string, newName: string): { newPath: string; updatedCount: number } {
  const oldNameWithoutExt = path.basename(oldPath, '.md')
  const newPath = path.join(path.dirname(oldPath), `${newName}.md`)

  // Rename the file
  fs.renameSync(oldPath, newPath)

  // Update all references in other notes
  let updatedCount = 0
  const notes = listNotes(vaultDir)

  // Simple regex to find [[linkText]] patterns
  const linkRegex = /\[\[([^\]]+)\]\]/g

  for (const note of notes) {
    // Skip the renamed note itself
    if (note.path === newPath) continue

    const content = readNote(note.path)
    let newContent = content
    let hasChanges = false

    // Replace all references to the old name with the new name
    newContent = newContent.replace(linkRegex, (match, linkText) => {
      if (linkText === oldNameWithoutExt) {
        hasChanges = true
        updatedCount++
        return `[[${newName}]]`
      }
      return match
    })

    // Write back if there were changes
    if (hasChanges) {
      writeNote(note.path, newContent)
    }
  }

  return { newPath, updatedCount }
}

// ── Copy operations ──

/** Copy a file or folder into destFolder, auto-renaming on conflict. Returns new path. */
export function copyItem(sourcePath: string, destFolder: string): string {
  const basename = path.basename(sourcePath)
  let destPath = path.join(destFolder, basename)

  // Handle name conflicts by adding (copy), (copy 2), etc.
  if (fs.existsSync(destPath)) {
    const ext = path.extname(basename)
    const nameNoExt = path.basename(basename, ext)
    let i = 1
    do {
      const suffix = i === 1 ? ' (copy)' : ` (copy ${i})`
      destPath = path.join(destFolder, `${nameNoExt}${suffix}${ext}`)
      i++
    } while (fs.existsSync(destPath))
  }

  const stat = fs.statSync(sourcePath)
  if (stat.isDirectory()) {
    fs.cpSync(sourcePath, destPath, { recursive: true })
  } else {
    fs.copyFileSync(sourcePath, destPath)
  }

  return destPath
}

// ── Git operations ──

export function isGitRepo(vaultDir: string): Promise<boolean> {
  return new Promise((resolve) => {
    execFile('git', ['rev-parse', '--is-inside-work-tree'], { cwd: vaultDir }, (err) => {
      resolve(!err)
    })
  })
}

export function gitStatus(vaultDir: string): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile('git', ['status', '--porcelain'], { cwd: vaultDir }, (err, stdout) => {
      if (err) reject(err)
      else resolve(stdout)
    })
  })
}

export function gitSync(vaultDir: string, message: string): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile('git', ['add', '-A'], { cwd: vaultDir }, (err) => {
      if (err) return reject(err)
      execFile('git', ['commit', '-m', message], { cwd: vaultDir }, (err2) => {
        if (err2) return reject(err2)
        execFile('git', ['push'], { cwd: vaultDir }, (err3) => {
          if (err3) return reject(err3)
          resolve('Synced successfully')
        })
      })
    })
  })
}

export function gitLog(vaultDir: string, count: number = 10): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile('git', ['log', '--oneline', `-${count}`], { cwd: vaultDir }, (err, stdout) => {
      if (err) reject(err)
      else resolve(stdout)
    })
  })
}
