import type { NoteFile } from './types'

export {}

declare global {
  interface Window {
    api: {
      // Vault directory
      getVaultDir: () => Promise<string>
      selectVaultDir: () => Promise<string | null>

      // File operations
      listNotes: (vaultDir: string) => Promise<NoteFile[]>
      buildFileTree: (vaultDir: string) => Promise<any[]>
      readNote: (filePath: string) => Promise<string>
      writeNote: (filePath: string, content: string) => Promise<void>
      createNote: (vaultDir: string, name: string) => Promise<string>
      deleteNote: (filePath: string) => Promise<void>
      deleteFolder: (folderPath: string) => Promise<void>
      renameNote: (vaultDir: string, oldPath: string, newName: string) => Promise<{ newPath: string; updatedCount: number }>
      createFolder: (folderPath: string) => Promise<string>
      moveNote: (oldPath: string, newFolderPath: string) => Promise<string>
      copyItem: (sourcePath: string, destFolder: string) => Promise<string>

      // File watcher events
      onFilesChanged: (callback: () => void) => () => void

      // Menu events
      onMenuNewNote: (callback: () => void) => () => void
      onMenuOpenSettings: (callback: () => void) => () => void
      onMenuSetSortOrder: (callback: (order: string) => void) => () => void

      // Git operations
      isGitRepo: (vaultDir: string) => Promise<boolean>
      gitIsRepo: (vaultDir: string) => Promise<boolean>
      gitStatus: (vaultDir: string) => Promise<string>
      gitSync: (vaultDir: string, message: string) => Promise<string>
      gitPull: (vaultDir: string) => Promise<string>
      gitPush: (vaultDir: string, message: string) => Promise<string>
      gitLog: (vaultDir: string, count: number) => Promise<string>
      gitInit: (vaultDir: string) => Promise<string>
      gitAddRemote: (vaultDir: string, remoteName: string, remoteUrl: string) => Promise<string>
      gitGetRemoteUrl: (vaultDir: string, remoteName?: string) => Promise<string>
      gitInitialCommit: (vaultDir: string, message: string) => Promise<string>

      // Vault sync operations
      syncAnalyseStatus: (vaultDir: string) => Promise<{
        state: 'up-to-date' | 'local-only' | 'remote-only' | 'diverged' | 'clean-merge' | 'no-remote'
        ahead?: number
        behind?: number
        conflicts?: Array<{ relativePath: string; localContent: string; remoteContent: string }>
      }>
      syncExecute: (vaultDir: string, resolutions?: Record<string, 'keep-local' | 'keep-remote' | 'conflict-note'>) => Promise<{
        success: boolean
        message: string
        conflictsCreated?: string[]
      }>

      // Window
      setTitle: (title: string) => Promise<void>
      windowMinimize: () => Promise<void>
      windowToggleMaximize: () => Promise<void>
      windowClose: () => Promise<void>
      windowIsMaximized: () => Promise<boolean>
      confirm: (message: string) => Promise<boolean>

      // Image handling
      saveImage: (vaultDir: string, imageData: ArrayBuffer, imageType: string) => Promise<string>
      convertBase64ImagesToFiles: (vaultDir: string, noteId: string, markdown: string) => Promise<string>
    }
  }
}
