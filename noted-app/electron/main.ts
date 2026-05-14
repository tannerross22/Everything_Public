import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import path from 'path'
import fs from 'fs'
import { watch, type FSWatcher } from 'chokidar'
import {
  listNotes,
  buildFileTree,
  readNote,
  writeNote,
  createNote,
  deleteNote,
  deleteFolder,
  renameNote,
  createFolder,
  moveNote,
  copyItem,
  isGitRepo,
  gitStatus,
  gitSync,
  gitLog,
  gitInit,
  gitAddRemote,
  gitGetRemoteUrl,
  gitInitialCommit,
  saveImage,
  convertBase64ImagesToFiles,
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

  const watchPath = path.join(vaultDir, '**/*.md')
  console.log(`[startWatcher] Starting file watcher on: ${watchPath}`)

  fileWatcher = watch(watchPath, {
    ignoreInitial: true,
    awaitWriteFinish: { stabilityThreshold: 300 },
    ignored: ['**/node_modules/**', '**/dist/**', '**/dist-electron/**', '**/.git/**'],
  })

  fileWatcher.on('ready', () => {
    console.log('[FileWatcher] Ready and listening for changes')
  })

  fileWatcher.on('all', (event, filePath) => {
    console.log(`[FileWatcher] File event: ${event} on ${filePath}, isWriting: ${isWriting}`)
    if (!isWriting && mainWindow) {
      console.log('[FileWatcher] → Sending vault:files-changed event')
      mainWindow.webContents.send('vault:files-changed')
    } else {
      console.log(`[FileWatcher] → Event blocked (isWriting=${isWriting})`)
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
    icon: path.join(__dirname, '../electron/app.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
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

  ipcMain.handle('vault:tree', (_event, vaultDir: string) => {
    return buildFileTree(vaultDir)
  })

  ipcMain.handle('vault:createFolder', (_event, folderPath: string) => {
    return createFolder(folderPath)
  })

  ipcMain.handle('vault:moveNote', (_event, oldPath: string, newFolderPath: string) => {
    return moveNote(oldPath, newFolderPath)
  })

  ipcMain.handle('vault:copyItem', (_event, sourcePath: string, destFolder: string) => {
    isWriting = true
    const result = copyItem(sourcePath, destFolder)
    setTimeout(() => { isWriting = false }, 500)
    return result
  })

  ipcMain.handle('vault:read', (_event, filePath: string) => {
    return readNote(filePath)
  })

  ipcMain.handle('vault:write', async (_event, filePath: string, content: string) => {
    console.log(`[vault:write] Writing to ${filePath}`)
    isWriting = true
    console.log('[vault:write] isWriting = true')
    writeNote(filePath, content)
    console.log('[vault:write] File written, isWriting will be reset in 200ms')
    // Small delay before re-enabling watcher to avoid self-trigger
    setTimeout(() => {
      isWriting = false
      console.log('[vault:write] isWriting = false')
      // Emit file changed event after write completes
      if (mainWindow) {
        console.log('[vault:write] Emitting vault:files-changed event')
        mainWindow.webContents.send('vault:files-changed')
      }
    }, 200)
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

  ipcMain.handle('vault:deleteFolder', (_event, folderPath: string) => {
    isWriting = true
    deleteFolder(folderPath)
    setTimeout(() => { isWriting = false }, 500)
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

  ipcMain.handle('git:sync', async (_event, vaultDir: string, message: string) => {
    const result = await gitSync(vaultDir, message)
    // Emit files changed event to refresh UI with any new files from remote
    if (mainWindow) {
      mainWindow.webContents.send('vault:files-changed')
    }
    return result
  })

  ipcMain.handle('git:log', (_event, vaultDir: string, count: number) => {
    return gitLog(vaultDir, count)
  })

  ipcMain.handle('git:init', (_event, vaultDir: string) => {
    return gitInit(vaultDir)
  })

  ipcMain.handle('git:addRemote', (_event, vaultDir: string, remoteName: string, remoteUrl: string) => {
    return gitAddRemote(vaultDir, remoteName, remoteUrl)
  })

  ipcMain.handle('git:getRemoteUrl', (_event, vaultDir: string, remoteName: string = 'origin') => {
    return gitGetRemoteUrl(vaultDir, remoteName)
  })

  ipcMain.handle('git:initialCommit', (_event, vaultDir: string, message: string) => {
    return gitInitialCommit(vaultDir, message)
  })

  // Window title
  ipcMain.handle('window:setTitle', (_event, title: string) => {
    if (mainWindow) {
      mainWindow.setTitle(title)
    }
  })

  // Native confirm dialog — avoids renderer confirm() which corrupts Electron focus state
  ipcMain.handle('dialog:confirm', async (_event, message: string) => {
    if (!mainWindow) return false
    const result = await dialog.showMessageBox(mainWindow, {
      type: 'question',
      buttons: ['Cancel', 'Delete'],
      defaultId: 1,
      cancelId: 0,
      message,
    })
    return result.response === 1
  })

  // Image handling
  ipcMain.handle('vault:saveImage', (_event, vaultDir: string, imageData: ArrayBuffer, imageType: string) => {
    const buffer = Buffer.from(imageData)
    return saveImage(vaultDir, buffer, imageType)
  })

  ipcMain.handle('vault:convertBase64ImagesToFiles', (_event, vaultDir: string, noteId: string, markdown: string) => {
    return convertBase64ImagesToFiles(vaultDir, noteId, markdown)
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
