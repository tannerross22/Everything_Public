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
      readNote: (filePath: string) => Promise<string>
      writeNote: (filePath: string, content: string) => Promise<void>
      createNote: (vaultDir: string, name: string) => Promise<string>
      deleteNote: (filePath: string) => Promise<void>

      // File watcher events
      onFilesChanged: (callback: () => void) => () => void

      // Git operations
      gitIsRepo: (vaultDir: string) => Promise<boolean>
      gitStatus: (vaultDir: string) => Promise<string>
      gitSync: (vaultDir: string, message: string) => Promise<string>
      gitLog: (vaultDir: string, count: number) => Promise<string>

      // Window
      setTitle: (title: string) => Promise<void>
    }
  }
}
