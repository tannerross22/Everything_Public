import { useState, useEffect, useCallback } from 'react'

interface GitPanelProps {
  vaultDir: string
}

export default function GitPanel({ vaultDir }: GitPanelProps) {
  const [isRepo, setIsRepo] = useState(false)
  const [changedCount, setChangedCount] = useState(0)
  const [recentCommits, setRecentCommits] = useState<string[]>([])
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)
  const [expanded, setExpanded] = useState(false)

  const refreshStatus = useCallback(async () => {
    if (!vaultDir) return
    try {
      const repo = await window.api.gitIsRepo(vaultDir)
      setIsRepo(repo)
      if (repo) {
        const status = await window.api.gitStatus(vaultDir)
        const lines = status.trim().split('\n').filter((l: string) => l.trim())
        setChangedCount(lines.length)

        const log = await window.api.gitLog(vaultDir, 5)
        setRecentCommits(log.trim().split('\n').filter((l: string) => l.trim()))
      }
    } catch {
      setIsRepo(false)
    }
  }, [vaultDir])

  useEffect(() => {
    refreshStatus()
    // Refresh status every 30 seconds
    const interval = setInterval(refreshStatus, 30000)
    return () => clearInterval(interval)
  }, [refreshStatus])

  const handleSync = async () => {
    if (syncing || !vaultDir) return
    setSyncing(true)
    setMessage(null)
    try {
      const timestamp = new Date().toISOString().replace('T', ' ').slice(0, 19)
      await window.api.gitSync(vaultDir, `vault sync: ${timestamp}`)
      setMessage({ text: 'Synced successfully!', type: 'success' })
      await refreshStatus()
    } catch (err: any) {
      const errMsg = err?.message || String(err)
      if (errMsg.includes('nothing to commit')) {
        setMessage({ text: 'Already up to date', type: 'success' })
      } else {
        setMessage({ text: `Sync failed: ${errMsg.slice(0, 80)}`, type: 'error' })
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
            disabled={syncing || changedCount === 0}
          >
            {syncing ? 'Syncing...' : 'Sync to GitHub'}
          </button>

          {message && (
            <div className={`git-message ${message.type}`}>
              {message.text}
            </div>
          )}

          {recentCommits.length > 0 && (
            <div className="git-commits">
              <div className="git-commits-label">Recent commits</div>
              {recentCommits.map((commit, i) => (
                <div key={i} className="git-commit">
                  {commit}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
