import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('api', {
  // Vault directory
  getVaultDir: (): Promise<string> => ipcRenderer.invoke('vault:getDir'),
  selectVaultDir: (): Promise<string | null> => ipcRenderer.invoke('vault:selectDir'),

  // File operations
  listNotes: (vaultDir: string) => ipcRenderer.invoke('vault:list', vaultDir),
  readNote: (filePath: string): Promise<string> => ipcRenderer.invoke('vault:read', filePath),
  writeNote: (filePath: string, content: string) => ipcRenderer.invoke('vault:write', filePath, content),
  createNote: (vaultDir: string, name: string): Promise<string> => ipcRenderer.invoke('vault:create', vaultDir, name),
  deleteNote: (filePath: string) => ipcRenderer.invoke('vault:delete', filePath),
  renameNote: (vaultDir: string, oldPath: string, newName: string): Promise<{ newPath: string; updatedCount: number }> => ipcRenderer.invoke('vault:rename', vaultDir, oldPath, newName),

  // File watcher events
  onFilesChanged: (callback: () => void) => {
    ipcRenderer.on('vault:files-changed', callback)
    return () => ipcRenderer.removeListener('vault:files-changed', callback)
  },

  // Git operations
  gitIsRepo: (vaultDir: string): Promise<boolean> => ipcRenderer.invoke('git:isRepo', vaultDir),
  gitStatus: (vaultDir: string): Promise<string> => ipcRenderer.invoke('git:status', vaultDir),
  gitSync: (vaultDir: string, message: string): Promise<string> => ipcRenderer.invoke('git:sync', vaultDir, message),
  gitLog: (vaultDir: string, count: number): Promise<string> => ipcRenderer.invoke('git:log', vaultDir, count),

  // Window
  setTitle: (title: string) => ipcRenderer.invoke('window:setTitle', title),
})
