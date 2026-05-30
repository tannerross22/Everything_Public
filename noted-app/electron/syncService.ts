import fs from 'fs'
import path from 'path'
import { execFile } from 'child_process'

// ── Types ──

export interface SyncConflict {
  relativePath: string
  localContent: string
  remoteContent: string
}

export type SyncStatus =
  | { state: 'up-to-date' }
  | { state: 'local-only'; ahead: number }
  | { state: 'remote-only'; behind: number }
  | { state: 'diverged'; ahead: number; behind: number; conflicts: SyncConflict[] }
  | { state: 'clean-merge'; ahead: number; behind: number }
  | { state: 'no-remote' }

export interface SyncResult {
  success: boolean
  message: string
  conflictsCreated?: string[]
}

// ── Helpers ──

function run(cmd: string, args: string[], cwd: string): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(cmd, args, { cwd, maxBuffer: 10 * 1024 * 1024 }, (err, stdout, stderr) => {
      if (err) {
        const msg = stderr?.trim() || err.message
        reject(new Error(msg))
      } else {
        resolve(stdout)
      }
    })
  })
}

function runSafe(cmd: string, args: string[], cwd: string): Promise<string | null> {
  return run(cmd, args, cwd).catch(() => null)
}

async function getBranch(vaultDir: string): Promise<string> {
  const branch = (await run('git', ['rev-parse', '--abbrev-ref', 'HEAD'], vaultDir)).trim()
  if (branch === 'HEAD') {
    const remotes = await run('git', ['branch', '-r'], vaultDir)
    if (remotes.includes('origin/main')) return 'main'
    return 'master'
  }
  return branch
}

function ensureSyncDir(vaultDir: string): void {
  const syncDir = path.join(vaultDir, '.noted')
  if (!fs.existsSync(syncDir)) {
    fs.mkdirSync(syncDir, { recursive: true })
  }
  const gitignorePath = path.join(vaultDir, '.gitignore')
  let gitignore = ''
  if (fs.existsSync(gitignorePath)) {
    gitignore = fs.readFileSync(gitignorePath, 'utf-8')
  }
  if (!gitignore.includes('.noted')) {
    gitignore += '\n.noted/\n'
    fs.writeFileSync(gitignorePath, gitignore, 'utf-8')
  }
}

// ── Core sync functions ──

/**
 * Analyse the vault's divergence from origin without changing any files.
 * Returns a status object describing what a sync would do.
 */
export async function analyseSyncStatus(vaultDir: string): Promise<SyncStatus> {
  try {
    // Fetch latest remote state
    await run('git', ['fetch', 'origin'], vaultDir)
  } catch {
    // No remote configured or network error
    return { state: 'no-remote' }
  }

  const branch = await getBranch(vaultDir)

  // Check if remote tracking branch exists
  const hasRemote = await runSafe('git', ['rev-parse', `origin/${branch}`], vaultDir)
  if (!hasRemote) {
    return { state: 'no-remote' }
  }

  // Count how far ahead/behind we are
  const counts = await runSafe(
    'git',
    ['rev-list', '--left-right', '--count', `HEAD...origin/${branch}`],
    vaultDir
  )

  let ahead = 0
  let behind = 0
  if (counts) {
    const parts = counts.trim().split(/\s+/)
    ahead = parseInt(parts[0] || '0', 10)
    behind = parseInt(parts[1] || '0', 10)
  }

  // Also check uncommitted changes — these count as "ahead"
  const status = await runSafe('git', ['status', '--porcelain'], vaultDir)
  const hasUncommitted = !!(status && status.trim())
  if (hasUncommitted) ahead = Math.max(ahead, 1)

  if (ahead === 0 && behind === 0) {
    return { state: 'up-to-date' }
  }

  if (behind === 0) {
    return { state: 'local-only', ahead }
  }

  if (ahead === 0) {
    return { state: 'remote-only', behind }
  }

  // Both sides have changes — check for file-level conflicts
  // Files changed on remote since common ancestor
  const remoteChanged = await runSafe(
    'git', ['diff', '--name-only', `HEAD...origin/${branch}`], vaultDir
  )
  const remoteFiles = new Set(
    (remoteChanged || '').trim().split('\n').filter(Boolean)
  )

  // Files changed locally (committed divergent changes)
  const localChanged = await runSafe(
    'git', ['diff', '--name-only', `origin/${branch}...HEAD`], vaultDir
  )
  const localCommittedFiles = new Set(
    (localChanged || '').trim().split('\n').filter(Boolean)
  )

  // Files changed locally (uncommitted)
  const uncommittedLines = (status || '').trim().split('\n').filter(Boolean)
  for (const line of uncommittedLines) {
    const filePath = line.substring(3).trim().replace(/^"(.*)"$/, '$1')
    if (filePath) localCommittedFiles.add(filePath)
  }

  // Find conflicts: files changed on BOTH sides
  const conflictPaths: string[] = []
  for (const f of localCommittedFiles) {
    if (remoteFiles.has(f)) {
      conflictPaths.push(f)
    }
  }

  if (conflictPaths.length === 0) {
    return { state: 'clean-merge', ahead, behind }
  }

  // Gather both versions for each conflicted file
  const conflicts: SyncConflict[] = []
  for (const rel of conflictPaths) {
    const absPath = path.join(vaultDir, rel)
    let localContent = ''
    let remoteContent = ''

    try {
      localContent = fs.existsSync(absPath)
        ? fs.readFileSync(absPath, 'utf-8')
        : '(file deleted locally)'
    } catch {
      localContent = '(could not read local version)'
    }

    try {
      remoteContent = (
        await run('git', ['show', `origin/${branch}:${rel}`], vaultDir)
      )
    } catch {
      remoteContent = '(file deleted on remote)'
    }

    conflicts.push({ relativePath: rel, localContent, remoteContent })
  }

  return { state: 'diverged', ahead, behind, conflicts }
}

/**
 * Execute the actual sync: commit local, pull remote, push everything.
 *
 * `resolutions` maps conflicted relative paths to a resolution strategy.
 * If omitted, all conflicts produce conflict notes.
 */
export async function executeSync(
  vaultDir: string,
  resolutions?: Record<string, 'keep-local' | 'keep-remote' | 'conflict-note'>
): Promise<SyncResult> {
  ensureSyncDir(vaultDir)
  const branch = await getBranch(vaultDir)
  const conflictsCreated: string[] = []

  // 1. Stage + commit any local changes
  await run('git', ['add', '-A'], vaultDir)
  const status = (await runSafe('git', ['status', '--porcelain'], vaultDir) || '').trim()
  if (status) {
    const now = new Date()
    const pad = (n: number) => String(n).padStart(2, '0')
    const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
    await run('git', ['commit', '-m', `vault sync: ${ts}`], vaultDir)
  }

  // 2. Fetch
  await run('git', ['fetch', 'origin'], vaultDir)

  // Check if we need to handle detached HEAD
  const headRef = (await run('git', ['rev-parse', '--abbrev-ref', 'HEAD'], vaultDir)).trim()
  if (headRef === 'HEAD') {
    await run('git', ['checkout', '-B', branch, `origin/${branch}`], vaultDir)
  }

  // 3. Check divergence
  const counts = await runSafe(
    'git', ['rev-list', '--left-right', '--count', `HEAD...origin/${branch}`], vaultDir
  )
  let ahead = 0
  let behind = 0
  if (counts) {
    const parts = counts.trim().split(/\s+/)
    ahead = parseInt(parts[0] || '0', 10)
    behind = parseInt(parts[1] || '0', 10)
  }

  // 4. If behind, handle conflicts then pull
  if (behind > 0) {
    // Pre-pull: save local content for files the user wants to keep
    const savedLocal: Record<string, string> = {}
    const conflictNoteData: Array<{ rel: string; localContent: string; remoteContent: string }> = []

    if (resolutions && Object.keys(resolutions).length > 0) {
      for (const [rel, strategy] of Object.entries(resolutions)) {
        const absPath = path.join(vaultDir, rel)

        if (strategy === 'keep-local') {
          try {
            if (fs.existsSync(absPath)) {
              savedLocal[rel] = fs.readFileSync(absPath, 'utf-8')
            }
          } catch { /* empty */ }
        }

        if (strategy === 'conflict-note') {
          let localContent = ''
          let remoteContent = ''
          try {
            localContent = fs.existsSync(absPath) ? fs.readFileSync(absPath, 'utf-8') : ''
          } catch { /* empty */ }
          try {
            remoteContent = await run('git', ['show', `origin/${branch}:${rel}`], vaultDir)
          } catch { /* empty */ }
          conflictNoteData.push({ rel, localContent, remoteContent })
        }
      }
    }

    // Pull remote changes — use theirs so clean files get remote version
    try {
      await run('git', ['pull', 'origin', branch, '--allow-unrelated-histories', '-X', 'theirs'], vaultDir)
    } catch {
      await runSafe('git', ['merge', '--abort'], vaultDir)
      try {
        await run('git', ['pull', 'origin', branch, '--allow-unrelated-histories', '-X', 'theirs'], vaultDir)
      } catch (retryErr) {
        return {
          success: false,
          message: `Pull failed: ${retryErr instanceof Error ? retryErr.message : String(retryErr)}`,
        }
      }
    }

    // Post-pull: restore files the user chose to keep local
    for (const [rel, content] of Object.entries(savedLocal)) {
      const absPath = path.join(vaultDir, rel)
      const dir = path.dirname(absPath)
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
      fs.writeFileSync(absPath, content, 'utf-8')
    }

    // Post-pull: create conflict notes
    for (const { rel, localContent, remoteContent } of conflictNoteData) {
      const absPath = path.join(vaultDir, rel)
      const baseName = path.basename(rel, '.md')
      const dir = path.dirname(absPath)
      const conflictFileName = `conflict-${baseName}-${Date.now()}.md`
      const conflictPath = path.join(dir, conflictFileName)

      const content = `# Sync Conflict: ${baseName}\n\nThis file was edited on multiple devices. Both versions are shown below.\n\n---\n\n## Your Version (This Device)\n\n${localContent}\n\n---\n\n## Remote Version (Other Device)\n\n${remoteContent}\n\n---\n\n*Resolve this conflict by editing the original note and deleting this conflict note, then sync again.*\n`
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
      fs.writeFileSync(conflictPath, content, 'utf-8')
      conflictsCreated.push(conflictPath)
    }

    // Commit any restorations and conflict notes
    if (Object.keys(savedLocal).length > 0 || conflictsCreated.length > 0) {
      await run('git', ['add', '-A'], vaultDir)
      await runSafe('git', ['commit', '-m', 'vault sync: resolved conflicts'], vaultDir)
    }
  }

  // 5. Push everything
  try {
    await run('git', ['push', '-u', 'origin', branch], vaultDir)
  } catch (pushErr) {
    return {
      success: false,
      message: `Push failed: ${pushErr instanceof Error ? pushErr.message : String(pushErr)}`,
    }
  }

  return {
    success: true,
    message: behind > 0
      ? `Synced — pulled ${behind} update${behind !== 1 ? 's' : ''}, pushed ${ahead} change${ahead !== 1 ? 's' : ''}`
      : `Pushed ${ahead} change${ahead !== 1 ? 's' : ''}`,
    conflictsCreated: conflictsCreated.length > 0 ? conflictsCreated : undefined,
  }
}
