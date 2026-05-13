import fs from 'fs'
import path from 'path'
import { execFile } from 'child_process'

export interface NoteFileData {
  name: string
  path: string
  modifiedAt: number
}

/**
 * List all .md files in the vault directory (non-recursive for now)
 */
export function listNotes(vaultDir: string): NoteFileData[] {
  if (!fs.existsSync(vaultDir)) return []

  const entries = fs.readdirSync(vaultDir, { withFileTypes: true })
  const notes: NoteFileData[] = []

  for (const entry of entries) {
    if (entry.isFile() && entry.name.endsWith('.md')) {
      const fullPath = path.join(vaultDir, entry.name)
      const stat = fs.statSync(fullPath)
      notes.push({
        name: entry.name.replace(/\.md$/, ''),
        path: fullPath,
        modifiedAt: stat.mtimeMs,
      })
    }
  }

  return notes.sort((a, b) => b.modifiedAt - a.modifiedAt)
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
