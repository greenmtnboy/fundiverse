'use strict'

import { app, protocol, BrowserWindow } from 'electron'
import { createProtocol } from 'vue-cli-plugin-electron-builder/lib'
import installExtension, { VUEJS3_DEVTOOLS } from 'electron-devtools-installer'
const { spawn } = require('child_process');
const path = require('path');

// import { autoUpdater } from "electron-updater"
import Store from 'electron-store';
Store.initRenderer()


const isDevelopment = process.env.NODE_ENV !== 'production'

// Scheme must be registered before the app is ready
protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { secure: true, standard: true } }
])

const startBackgroundService = () => {
  const backgroundService = spawn(path.join(app.getAppPath(), '..', '/src/background/py-portfolio-ui-backend.exe'))
  backgroundService.on('close', (code) => {
    console.log(`Background process exited with code ${code}`);
  });
  return backgroundService
}

async function createWindow() {
  // Create the browser window.
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      
      // Use pluginOptions.nodeIntegration, leave this alone
      // See nklayman.github.io/vue-cli-plugin-electron-builder/guide/security.html#node-integration for more info
      nodeIntegration: !!(process.env
          .ELECTRON_NODE_INTEGRATION as unknown) as boolean,
      contextIsolation: !process.env.ELECTRON_NODE_INTEGRATION
    }
  })
  const pythonProcess = startBackgroundService()
  if (process.env.WEBPACK_DEV_SERVER_URL) {
    // Load the url of the dev server if in development mode
    await win.loadURL(process.env.WEBPACK_DEV_SERVER_URL as string)
    if (!process.env.IS_TEST) win.webContents.openDevTools()
  } else {
    createProtocol('app')
    // Load the index.html when not in development
    win.loadURL('app://./index.html')
  }
   win.on('closed', () => {
    // Terminate the Python process when the Electron app is closed
    if (pythonProcess) {
      pythonProcess.kill();
    }
  });
}

// Quit when all windows are closed.
app.on('window-all-closed', () => {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit()
  }
})


app.on('activate', () => {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', async () => {
  if (isDevelopment && !process.env.IS_TEST) {
    // Install Vue Devtools
    try {
      await installExtension(VUEJS3_DEVTOOLS)
    } catch (e) {
      if (e instanceof Error) {
      console.error('Vue Devtools failed to install:', e.toString())
    }
  }
  }
  // console.log(path.join(app.getAppPath(), '..','/src/background/py-portfolio-ui-backend.exe'))

  createWindow()
})
// if (process.env.WEBPACK_DEV_SERVER_URL) {
//   // Load the url of the dev server if in development mode
//   win.loadURL(process.env.WEBPACK_DEV_SERVER_URL)
//   if (!process.env.IS_TEST) win.webContents.openDevTools()
// } else {
//   createProtocol('app')
//   // Load the index.html when not in development
//   win.loadURL('app://./index.html')
//   autoUpdater.checkForUpdatesAndNotify()
// }


// Exit cleanly on request from parent process in development mode.
if (isDevelopment) {
  if (process.platform === 'win32') {
    process.on('message', (data) => {
      if (data === 'graceful-exit') {
        app.quit()
      }
    })
  } else {
    process.on('SIGTERM', () => {
      app.quit()
    })
  }
}
