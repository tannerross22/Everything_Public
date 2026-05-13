import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import path from 'path'
import fs from 'fs'
import { watch, type FSWatcher } from 'chokidar'
import {
  listNotes,
  readNote,
  writeNote,
  createNote,
  deleteNote,
  renameNote,
  isGitRepo,
  gitStatus,
  gitSync,
  gitLog,
} from './fileService'

let mainWindow: BrowserWindow | null = null
let fileWatcher: FSWatcher | null = null
let isWriting = false // Guard to ignore self-triggered file changes

// ── Config: persist vault directory ──
const configPath = path.join(app.getPath('userData'), 'noted-config.json')

function loadConfig(): { vaultDir: string } {
  try {
    if (fs.existsSync(configPath)) {
      return JSON.parse(fs.readFileSync(configPath, 'utf-8'))
    }
  } catch {}
  // Default vault is the Everything_Public repo
  // app.isPackaged ? Documents : the repo root (noted-app's parent)
  const defaultVault = path.resolve(__dirname, '..', '..')
  return { vaultDir: defaultVault }
}

function saveConfig(config: { vaultDir: string }) {
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8')
}

// ── File watcher ──
function startWatcher(vaultDir: string) {
  if (fileWatcher) {
    fileWatcher.close()
  }

  fileWatcher = watch(path.join(vaultDir, '*.md'), {
    ignoreInitial: true,
    awaitWriteFinish: { stabilityThreshold: 300 },
  })

  fileWatcher.on('all', () => {
    if (!isWriting && mainWindow) {
      mainWindow.webContents.send('vault:files-changed')
    }
  })
}

// ── Electron window ──
const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'Noted',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(VITE_DEV_SERVER_URL)
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // Start file watcher with saved vault dir
  const config = loadConfig()
  startWatcher(config.vaultDir)
}

// ── IPC Handlers ──
function registerIpcHandlers() {
  // Vault directory
  ipcMain.handle('vault:getDir', () => {
    return loadConfig().vaultDir
  })

  ipcMain.handle('vault:selectDir', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory'],
      title: 'Select Vault Directory',
    })
    if (!result.canceled && result.filePaths[0]) {
      const vaultDir = result.filePaths[0]
      saveConfig({ vaultDir })
      startWatcher(vaultDir)
      return vaultDir
    }
    return null
  })

  // File operations
  ipcMain.handle('vault:list', (_event, vaultDir: string) => {
    return listNotes(vaultDir)
  })

  ipcMain.handle('vault:read', (_event, filePath: string) => {
    return readNote(filePath)
  })

  ipcMain.handle('vault:write', async (_event, filePath: string, content: string) => {
    isWriting = true
    writeNote(filePath, content)
    // Small delay before re-enabling watcher to avoid self-trigger
    setTimeout(() => { isWriting = false }, 200)
  })

  ipcMain.handle('vault:create', (_event, vaultDir: string, name: string) => {
    isWriting = true
    const result = createNote(vaultDir, name)
    setTimeout(() => { isWriting = false }, 200)
    return result
  })

  ipcMain.handle('vault:delete', (_event, filePath: string) => {
    isWriting = true
    deleteNote(filePath)
    setTimeout(() => { isWriting = false }, 200)
  })

  ipcMain.handle('vault:rename', (_event, vaultDir: string, oldPath: string, newName: string) => {
    isWriting = true
    const result = renameNote(vaultDir, oldPath, newName)
    setTimeout(() => { isWriting = false }, 200)
    return result
  })

  // Git operations
  ipcMain.handle('git:isRepo', (_event, vaultDir: string) => {
    return isGitRepo(vaultDir)
  })

  ipcMain.handle('git:status', (_event, vaultDir: string) => {
    return gitStatus(vaultDir)
  })

  ipcMain.handle('git:sync', (_event, vaultDir: string, message: string) => {
    return gitSync(vaultDir, message)
  })

  ipcMain.handle('git:log', (_event, vaultDir: string, count: number) => {
    return gitLog(vaultDir, count)
  })

  // Window title
  ipcMain.handle('window:setTitle', (_event, title: string) => {
    if (mainWindow) {
      mainWindow.setTitle(title)
    }
  })
}

// ── App lifecycle ──
app.whenReady().then(() => {
  registerIpcHandlers()
  createWindow()
})

app.on('window-all-closed', () => {
  if (fileWatcher) fileWatcher.close()
  app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})
