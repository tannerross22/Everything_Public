import { useState, useEffect, useCallback, useRef } from 'react'

export interface SyncConflict {
  relativePath: string
  localContent: string
  remoteContent: string
}

export type SyncStatusState =
  | 'idle'          // haven't checked yet
  | 'up-to-date'   // nothing to sync
  | 'has-changes'   // local and/or remote changes, no conflicts
  | 'has-conflicts' // diverged with file-level conflicts
  | 'syncing'       // sync in progress
  | 'synced'        // just finished syncing
  | 'error'         // last sync failed
  | 'no-remote'     // no remote configured

export function useGitSync(vaultDir: string, onFilesRefreshed?: () => Promise<void>) {
  const onFilesRefreshedRef = useRef(onFilesRefreshed)
  useEffect(() => {
    onFilesRefreshedRef.current = onFilesRefreshed
  }, [onFilesRefreshed])

  const [isRepo, setIsRepo] = useState(false)
  const [syncStatus, setSyncStatus] = useState<SyncStatusState>('idle')
  const [ahead, setAhead] = useState(0)
  const [behind, setBehind] = useState(0)
  const [conflicts, setConflicts] = useState<SyncConflict[]>([])
  const [lastMessage, setLastMessage] = useState<string | null>(null)
  const [lastError, setLastError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const applyStatus = useCallback((result: { state: string; ahead?: number; behind?: number; conflicts?: SyncConflict[] }) => {
    switch (result.state) {
      case 'up-to-date':
        setSyncStatus('up-to-date')
        setAhead(0)
        setBehind(0)
        setConflicts([])
        break
      case 'local-only':
        setSyncStatus('has-changes')
        setAhead(result.ahead ?? 0)
        setBehind(0)
        setConflicts([])
        break
      case 'remote-only':
        setSyncStatus('has-changes')
        setAhead(0)
        setBehind(result.behind ?? 0)
        setConflicts([])
        break
      case 'clean-merge':
        setSyncStatus('has-changes')
        setAhead(result.ahead ?? 0)
        setBehind(result.behind ?? 0)
        setConflicts([])
        break
      case 'diverged':
        setSyncStatus('has-conflicts')
        setAhead(result.ahead ?? 0)
        setBehind(result.behind ?? 0)
        setConflicts(result.conflicts ?? [])
        break
      case 'no-remote':
        setSyncStatus('no-remote')
        setAhead(0)
        setBehind(0)
        setConflicts([])
        break
    }
  }, [])

  // Full status check (fetches from remote — expensive)
  const refreshStatus = useCallback(async () => {
    if (!vaultDir) return
    try {
      const repo = await window.api.gitIsRepo(vaultDir)
      setIsRepo(repo)
      if (!repo) return
      const result = await window.api.syncAnalyseStatus(vaultDir)
      applyStatus(result)
    } catch {
      setIsRepo(false)
    }
  }, [vaultDir, applyStatus])

  // Fast local-only check (no fetch — cheap, for file changes)
  const refreshLocalStatus = useCallback(async () => {
    if (!vaultDir) return
    try {
      const repo = await window.api.gitIsRepo(vaultDir)
      setIsRepo(repo)
      if (!repo) return
      const status = await window.api.gitStatus(vaultDir)
      const lines = status.trim().split('\n').filter((l: string) => l.trim())
      if (lines.length > 0 && syncStatus !== 'has-conflicts') {
        setSyncStatus('has-changes')
        setAhead(prev => Math.max(prev, 1))
      }
    } catch {
      // ignore
    }
  }, [vaultDir, syncStatus])

  // Initial full check + periodic full refresh + fast check on file changes
  useEffect(() => {
    refreshStatus()

    let processingTimeout: ReturnType<typeof setTimeout> | null = null

    const unsubscribe = window.api.onFilesChanged(async () => {
      if (processingTimeout) clearTimeout(processingTimeout)
      setIsProcessing(true)
      processingTimeout = setTimeout(async () => {
        await refreshLocalStatus()
        setIsProcessing(false)
        processingTimeout = null
      }, 1000)
    })

    // Full remote check every 60s
    const interval = setInterval(() => refreshStatus(), 60000)

    return () => {
      if (processingTimeout) clearTimeout(processingTimeout)
      unsubscribe()
      clearInterval(interval)
    }
  }, [vaultDir, refreshStatus, refreshLocalStatus])

  const handleSync = useCallback(async (
    resolutions?: Record<string, 'keep-local' | 'keep-remote' | 'conflict-note'>
  ) => {
    if (syncStatus === 'syncing' || !vaultDir) return
    setSyncStatus('syncing')
    setLastError(null)
    setLastMessage(null)

    try {
      const result = await window.api.syncExecute(vaultDir, resolutions)

      if (result.success) {
        if (onFilesRefreshedRef.current) {
          await onFilesRefreshedRef.current()
        }

        setLastMessage(result.message)
        setSyncStatus('synced')
        setConflicts([])

        setTimeout(async () => {
          await refreshStatus()
        }, 2500)
      } else {
        setLastError(result.message)
        setSyncStatus('error')
        setTimeout(async () => {
          await refreshStatus()
        }, 3000)
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error)
      setLastError(msg)
      setSyncStatus('error')
      setTimeout(async () => {
        await refreshStatus()
      }, 3000)
    }
  }, [syncStatus, vaultDir, refreshStatus])

  return {
    isRepo,
    syncStatus,
    ahead,
    behind,
    conflicts,
    lastMessage,
    lastError,
    isProcessing,
    handleSync,
    refreshStatus,
  }
}
