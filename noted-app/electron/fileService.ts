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
      if (err) {
        console.error(`[gitStatus] Error:`, err)
        reject(err)
      } else {
        console.log(`[gitStatus] Current status:\n${stdout || '(no changes)'}`)
        resolve(stdout)
      }
    })
  })
}

export function gitSync(vaultDir: string, message: string): Promise<string> {
  return new Promise((resolve, reject) => {
    console.log(`[gitSync] ========== STARTING SYNC ==========`)
    console.log(`[gitSync] Vault: ${vaultDir}`)
    console.log(`[gitSync] Message: ${message}`)

    execFile('git', ['add', '-A'], { cwd: vaultDir }, (err, stdout, stderr) => {
      console.log(`[gitSync] git add -A completed`)
      console.log(`[gitSync]   stdout: "${stdout}"`)
      console.log(`[gitSync]   stderr: "${stderr}"`)
      if (err) {
        console.error(`[gitSync] Error in git add:`, err.message)
        return reject(err)
      }

      console.log(`[gitSync] >>> Files staged, creating commit...`)

      execFile('git', ['commit', '-m', message], { cwd: vaultDir }, (err2, stdout2, stderr2) => {
        console.log(`[gitSync] git commit completed`)
        console.log(`[gitSync]   stdout: "${stdout2}"`)
        console.log(`[gitSync]   stderr: "${stderr2}"`)
        if (err2) {
          console.error(`[gitSync] Error in git commit:`, err2.message)
          return reject(err2)
        }

        console.log(`[gitSync] >>> Commit created, fetching remote changes...`)

        // First, fetch to get all remote refs
        execFile('git', ['fetch', 'origin'], { cwd: vaultDir }, (errFetch, stdoutFetch, stderrFetch) => {
          console.log(`[gitSync] git fetch origin completed`)
          console.log(`[gitSync]   stdout: "${stdoutFetch}"`)
          console.log(`[gitSync]   stderr: "${stderrFetch}"`)
          if (errFetch) {
            console.error(`[gitSync] Error in git fetch:`, errFetch.message)
            return reject(errFetch)
          }

          console.log(`[gitSync] >>> Remote refs updated, checking branch state...`)

          // Get current branch name - if detached, we need to attach to a proper branch
          execFile('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { cwd: vaultDir }, (errBranch, currentBranch) => {
            let branch = currentBranch.trim()
            console.log(`[gitSync] Current branch/HEAD: ${branch}`)

            // If detached HEAD, find and checkout a proper branch
            if (branch === 'HEAD') {
              console.log(`[gitSync] Detached HEAD state detected, finding a valid branch...`)

              // Get list of remote branches to find a valid one to checkout
              execFile('git', ['branch', '-r'], { cwd: vaultDir }, (errList, branchList) => {
                console.log(`[gitSync] Remote branches:\n${branchList}`)

                // Try to find master or main
                let targetBranch = 'master'
                if (branchList.includes('origin/main')) {
                  targetBranch = 'main'
                }

                console.log(`[gitSync] Checking out ${targetBranch}...`)
                execFile('git', ['checkout', '-B', targetBranch, `origin/${targetBranch}`], { cwd: vaultDir }, (errCheckout) => {
                  if (errCheckout) {
                    console.error(`[gitSync] Error checking out branch:`, errCheckout.message)
                    return reject(errCheckout)
                  }

                  branch = targetBranch
                  continueSync(branch)
                })
              })
            } else {
              continueSync(branch)
            }

            function continueSync(branch: string) {
              console.log(`[gitSync] >>> Pulling remote changes on branch: ${branch}...`)

              // Pull with explicit remote and branch reference (merge strategy, no rebase)
              // Regular merge is simpler and avoids complex rebase conflicts
              execFile('git', ['pull', 'origin', branch], { cwd: vaultDir }, (err2b, stdout2b, stderr2b) => {
                console.log(`[gitSync] git pull origin ${branch} completed`)
                console.log(`[gitSync]   stdout: "${stdout2b}"`)
                console.log(`[gitSync]   stderr: "${stderr2b}"`)
                if (err2b) {
                  console.warn(`[gitSync] Warning during pull:`, err2b.message)
                  // Try to abort any in-progress rebase/merge
                  execFile('git', ['rebase', '--abort'], { cwd: vaultDir }, () => {
                    console.log(`[gitSync] Aborted any in-progress rebase`)
                  })
                  // Don't reject - we still have our commits locally
                }

                console.log(`[gitSync] >>> Remote changes integrated, pushing to remote...`)

                // Push to current branch explicitly
                execFile('git', ['push', '-u', 'origin', branch, '-v'], { cwd: vaultDir }, (err3, stdout3, stderr3) => {
                  console.log(`[gitSync] git push -u origin ${branch} -v completed`)
                  console.log(`[gitSync]   stdout: "${stdout3}"`)
                  console.log(`[gitSync]   stderr: "${stderr3}"`)
                  if (err3) {
                    console.error(`[gitSync] Error in git push:`, err3.message)
                    console.error(`[gitSync]   Full error:`, err3)
                    return reject(err3)
                  }

                  console.log(`[gitSync] ========== SYNC SUCCESSFUL! ==========`)
                  resolve('Synced successfully')
                })
              })
            }
          })
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

// Initialize a new git repository
export function gitInit(vaultDir: string): Promise<string> {
  return new Promise((resolve, reject) => {
    console.log(`[gitInit] Initializing git repo at: ${vaultDir}`)
    execFile('git', ['init'], { cwd: vaultDir }, (err, stdout) => {
      if (err) {
        console.error(`[gitInit] Error:`, err)
        reject(err)
      } else {
        console.log(`[gitInit] Success:`, stdout)
        resolve(stdout)
      }
    })
  })
}

// Add a remote to the repository
export function gitAddRemote(vaultDir: string, remoteName: string, remoteUrl: string): Promise<string> {
  return new Promise((resolve, reject) => {
    console.log(`[gitAddRemote] Adding remote "${remoteName}" to: ${vaultDir}`)
    console.log(`[gitAddRemote] Remote URL: ${remoteUrl}`)
    execFile('git', ['remote', 'add', remoteName, remoteUrl], { cwd: vaultDir }, (err) => {
      if (err) {
        console.error(`[gitAddRemote] Error:`, err)
        reject(err)
      } else {
        console.log(`[gitAddRemote] Success`)
        resolve('Remote added successfully')
      }
    })
  })
}

// Get the remote URL
export function gitGetRemoteUrl(vaultDir: string, remoteName: string = 'origin'): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile('git', ['config', '--get', `remote.${remoteName}.url`], { cwd: vaultDir }, (err, stdout) => {
      if (err) reject(err)
      else resolve(stdout.trim())
    })
  })
}

// Create initial commit with a message
export function gitInitialCommit(vaultDir: string, message: string = 'Initial commit'): Promise<string> {
  return new Promise((resolve, reject) => {
    console.log(`[gitInitialCommit] Creating initial commit in: ${vaultDir}`)
    console.log(`[gitInitialCommit] Message: ${message}`)

    // First add all files
    execFile('git', ['add', '-A'], { cwd: vaultDir }, (err1) => {
      if (err1) {
        console.error(`[gitInitialCommit] Error in git add:`, err1)
        return reject(err1)
      }

      console.log(`[gitInitialCommit] Files staged, creating commit...`)

      // Check if there's anything to commit
      execFile('git', ['commit', '-m', message], { cwd: vaultDir }, (err2, stdout, stderr) => {
        // If there's nothing to commit, that's fine
        if (err2 && err2.message?.includes('nothing to commit')) {
          console.log(`[gitInitialCommit] No files to commit`)
          resolve('No files to commit')
        } else if (err2) {
          console.error(`[gitInitialCommit] Error in git commit:`, err2)
          console.error(`[gitInitialCommit] stderr:`, stderr)
          reject(err2)
        } else {
          console.log(`[gitInitialCommit] Commit created successfully`)
          console.log(`[gitInitialCommit] stdout:`, stdout)
          resolve('Initial commit created')
        }
      })
    })
  })
}
