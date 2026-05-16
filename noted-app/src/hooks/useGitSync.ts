import { useState, useEffect, useCallback } from 'react'

export function useGitSync(vaultDir: string) {
  const [isRepo, setIsRepo] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [showSynced, setShowSynced] = useState(false)

  const refreshGitStatus = useCallback(async () => {
    if (!vaultDir) return
    try {
      const repo = await window.api.gitIsRepo(vaultDir)
      setIsRepo(repo)
      if (repo) {
        const status = await window.api.gitStatus(vaultDir)
        const lines = status.trim().split('\n').filter((l: string) => l.trim())
        setHasChanges(lines.length > 0)
      }
    } catch {
      setIsRepo(false)
    }
  }, [vaultDir])

  useEffect(() => {
    refreshGitStatus()

    let processingTimeout: ReturnType<typeof setTimeout> | null = null

    const unsubscribe = window.api.onFilesChanged(async () => {
      if (processingTimeout) clearTimeout(processingTimeout)
      setIsProcessing(true)
      processingTimeout = setTimeout(async () => {
        await refreshGitStatus()
        setIsProcessing(false)
        processingTimeout = null
      }, 1000)
    })

    const interval = setInterval(() => refreshGitStatus(), 30000)

    return () => {
      if (processingTimeout) clearTimeout(processingTimeout)
      unsubscribe()
      clearInterval(interval)
    }
  }, [vaultDir])

  const handleSync = useCallback(async () => {
    if (syncing || !vaultDir) return
    setSyncing(true)
    try {
      const now = new Date()
      const pad = (n: number) => String(n).padStart(2, '0')
      const timestamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
      await window.api.gitSync(vaultDir, `vault sync: ${timestamp}`)
      await new Promise(resolve => setTimeout(resolve, 500))
      await refreshGitStatus()
      setShowSynced(true)
      setTimeout(() => setShowSynced(false), 2000)
    } catch (error) {
      console.error('[useGitSync] Sync error:', error)
      await refreshGitStatus()
    } finally {
      setSyncing(false)
    }
  }, [syncing, vaultDir, refreshGitStatus])

  return { isRepo, hasChanges, syncing, isProcessing, showSynced, handleSync }
}
