'use strict'

import { app, protocol, BrowserWindow } from 'electron'
import { createProtocol } from 'vue-cli-plugin-electron-builder/lib'
import installExtension, { VUEJS3_DEVTOOLS } from 'electron-devtools-installer'
const http = require('http');
const { exec } = require('child_process');
const { spawn } = require('child_process');
const path = require('path');

// import { autoUpdater } from "electron-updater"
import Store from 'electron-store';
Store.initRenderer()

// Specify the process name you want to check
const targetProcessName = 'py-portfolio-ui-backend';
const isDevelopment = process.env.NODE_ENV !== 'production'

// Scheme must be registered before the app is ready
protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { secure: true, standard: true } }
])

function stripQuotes(str) {
  str = str.trim();
  if (str.startsWith('"') && str.endsWith('"')) {
    return str.slice(1, -1);
  } else if (str.startsWith("'") && str.endsWith("'")) {
    return str.slice(1, -1);
  }
  return str;
}



function stopBackground() {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: '127.0.0.1',
      port: 3042,
      path: '/terminate',
      method: 'GET',
    };

    const req = http.request(options, (res) => {
      let data = '';

      // Receive data chunks
      res.on('data', (chunk) => {
        data += chunk;
      });

      // Process the complete response
      res.on('end', () => {
        resolve(data); // Resolve the Promise with the received data
      });
    });

    req.on('error', (error) => {
      reject(error); // Reject the Promise with the error
    });

    req.end(); // Send the HTTP request
  });
}



// helper to ensure the background process is managed
function findProcessesByName(processName): Promise<object[]> {
  return new Promise((resolve, reject) => {
    const platform = process.platform;
    let cmd;
    if (platform === 'win32') {
      cmd = `tasklist /FI "IMAGENAME eq ${processName}.exe" /FO CSV /NH`;
    } else if (platform === 'darwin' || platform === 'linux') {
      cmd = `ps -C ${processName} -o pid=`;
    } else {
      reject(new Error(`Unsupported platform: ${platform}`));
      return;
    }

    exec(cmd, (error, stdout) => {
      if (error) {
        reject(error);
        return;
      }

      const output = stdout.trim();
      if (output) {
        if (platform === 'win32' && output.includes('No tasks are running which match the specified criteria.')) {
          resolve([]);
        }
        else if (platform === 'win32') {
          const lines = output.split('\n');
          const processes: object[] = [];

          for (const line of lines) {
            if (line.trim() !== '') {
              const pid = line.split(',')[1].trim();
              processes.push({ pid: stripQuotes(pid), name: processName });
            }
          }
          resolve(processes);
        }
        else {
          const pid = output.split('\n')[0].trim();
          resolve([{ pid: pid, name: processName, }]);
        }
      } else {
        resolve([]);
      }
    });
  });
}


const startBackgroundService = () => {
  // let uuid = randomUUID()
  const backgroundService = spawn(path.join(app.getAppPath(), '..', '/src/background/', `${targetProcessName}.exe`))

  console.log(`Background process started with pid ${backgroundService.pid}`)
  backgroundService.on('close', (code) => {
    console.log(`Background python process exited with code ${code}`);
  });

  backgroundService.stdout.on('data', (data) => {
    console.log(`Child background python stdout: ${data}`);
  });

  backgroundService.on('error', (error) => {
    console.error(`Error occurred in background python process: ${error.message}`);
  });

  backgroundService.on('exit', (code) => {
    console.log(`Background process ${backgroundService.pid} exited with code ${code}`);
  });


  let backgroundClosed = false;
  app.on("before-quit", async (e) => {
    if (!backgroundClosed) {
      e.preventDefault();
      await stopBackground().then(() => {
        backgroundClosed = true;
        console.log(`Background service ${backgroundService.pid} shut down, quitting`);
        app.quit();
      }).catch((err) => {
        console.log(`Background service ${backgroundService.pid} failed to shut down ${err}`);
      })

    }
  });
  return backgroundService
}

async function startBackgroundServiceSafe() {
  await findProcessesByName(targetProcessName).then((procs) => {
    if (procs.length>0) {
      procs.map((proc) =>  {
        console.log(proc)
        console.log(`Background ${targetProcessName} is already running ${proc['pid']}!`)
        console.log(`Killing ${proc['pid']} and restarting`)
        process.kill(proc['pid'])
        
      })
    }
    else {
      console.log(`Background ${targetProcessName} is not running, starting it!`)
    }
    
    startBackgroundService()

  })
};

async function createWindow() {
  // Create the browser window.
  const win = new BrowserWindow({
    width: 1000,
    height: 600,
    minWidth: 800, // Set the minimum width here
    autoHideMenuBar: true,
    icon: path.join(__dirname, 'assets', 'appicon.png'),
    webPreferences: {

      // Use pluginOptions.nodeIntegration, leave this alone
      // See nklayman.github.io/vue-cli-plugin-electron-builder/guide/security.html#node-integration for more info
      nodeIntegration: !!(process.env
        .ELECTRON_NODE_INTEGRATION as unknown) as boolean,
      contextIsolation: !process.env.ELECTRON_NODE_INTEGRATION
    }
  })

  // await pollServer();
  if (process.env.WEBPACK_DEV_SERVER_URL) {
    // Load the url of the dev server if in development mode
    await win.loadURL(process.env.WEBPACK_DEV_SERVER_URL as string)
    if (!process.env.IS_TEST) win.webContents.openDevTools()
  } else {
    createProtocol('app')
    // Load the index.html when not in development
    win.loadURL('app://./index.html')
  }
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

  startBackgroundServiceSafe();
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
