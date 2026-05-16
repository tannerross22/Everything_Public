import { useState, useEffect, useCallback } from 'react'

interface GitPanelProps {
  vaultDir: string
}

export default function GitPanel({ vaultDir }: GitPanelProps) {
  const [isRepo, setIsRepo] = useState(false)
  const [changedCount, setChangedCount] = useState(0)
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)
  const [expanded, setExpanded] = useState(false)

  const [isProcessing, setIsProcessing] = useState(false)

  const refreshStatus = useCallback(async () => {
    if (!vaultDir) return
    try {
      const repo = await window.api.gitIsRepo(vaultDir)
      setIsRepo(repo)
      if (repo) {
        const status = await window.api.gitStatus(vaultDir)
        const lines = status.trim().split('\n').filter((l: string) => l.trim())
        setChangedCount(lines.length)
      }
    } catch {
      setIsRepo(false)
    }
  }, [vaultDir])

  useEffect(() => {
    refreshStatus()

    // Listen for file changes and refresh status immediately
    let processingTimeout: ReturnType<typeof setTimeout> | null = null
    const unsubscribe = window.api.onFilesChanged(() => {
      // Clear any pending timeout
      if (processingTimeout) clearTimeout(processingTimeout)

      setIsProcessing(true)
      // Debounce to wait for file writes to stabilize (300ms from chokidar config)
      processingTimeout = setTimeout(async () => {
        await refreshStatus()
        setIsProcessing(false)
        processingTimeout = null
      }, 400) // Slightly longer than chokidar's stabilityThreshold
    })

    // Also refresh every 30 seconds as fallback
    const interval = setInterval(refreshStatus, 30000)

    return () => {
      if (processingTimeout) clearTimeout(processingTimeout)
      unsubscribe()
      clearInterval(interval)
    }
  }, [refreshStatus])

  const handleSync = async () => {
    if (syncing || !vaultDir) return
    setSyncing(true)
    setMessage(null)
    try {
      // Format timestamp safely: YYYY-MM-DD HH:MM:SS
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const day = String(now.getDate()).padStart(2, '0')
      const hours = String(now.getHours()).padStart(2, '0')
      const mins = String(now.getMinutes()).padStart(2, '0')
      const secs = String(now.getSeconds()).padStart(2, '0')
      const timestamp = `${year}-${month}-${day} ${hours}:${mins}:${secs}`
      await window.api.gitSync(vaultDir, `vault sync: ${timestamp}`)
      setMessage({ text: 'Synced successfully!', type: 'success' })
      await refreshStatus()
    } catch (err: any) {
      const errMsg = err?.message || String(err)
      if (errMsg.includes('nothing to commit')) {
        setMessage({ text: 'Already up to date', type: 'success' })
      } else if (errMsg.includes('push') && errMsg.includes('http')) {
        setMessage({ text: 'Push failed: Check git credentials/remote URL', type: 'error' })
      } else if (errMsg.includes('ENOTFOUND')) {
        setMessage({ text: 'Network error: Check internet connection', type: 'error' })
      } else {
        // Show first 60 chars of error, truncated nicely
        const shortErr = errMsg.length > 60 ? errMsg.slice(0, 60) + '...' : errMsg
        setMessage({ text: `Sync failed: ${shortErr}`, type: 'error' })
      }
    } finally {
      setSyncing(false)
      // Clear message after 5 seconds
      setTimeout(() => setMessage(null), 5000)
    }
  }

  if (!isRepo) {
    return (
      <div className="git-panel">
        <div className="git-header" onClick={() => setExpanded(!expanded)}>
          <span className="git-label">Git</span>
          <span className="git-status-badge no-repo">No repo</span>
        </div>
      </div>
    )
  }

  return (
    <div className="git-panel">
      <div className="git-header" onClick={() => setExpanded(!expanded)}>
        <span className="git-label">Git</span>
        <span className={`git-status-badge ${changedCount > 0 ? 'has-changes' : 'clean'}`}>
          {changedCount > 0 ? `${changedCount} changed` : 'Clean'}
        </span>
        <span className="git-expand">{expanded ? '▴' : '▾'}</span>
      </div>

      {expanded && (
        <div className="git-body">
          <button
            className="git-sync-btn"
            onClick={handleSync}
            disabled={syncing || isProcessing || changedCount === 0}
            title={isProcessing ? 'Processing changes...' : changedCount === 0 ? 'No changes to sync' : ''}
          >
            {syncing ? 'Syncing...' : isProcessing ? '⟳ Processing...' : 'Sync to GitHub'}
          </button>

          {message && (
            <div className={`git-message ${message.type}`}>
              {message.text}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
