import { app, BrowserWindow } from "electron";
import path from "node:path";
import Store from "electron-store";
import Os from "os";
import http from "http";
import { exec, execFile } from "child_process";
import { randomInt } from "crypto";
import instance from "/src/api/instance.ts";
import { autoUpdater } from "electron-updater";

app.on("ready", function () {
  autoUpdater.checkForUpdatesAndNotify();
});

const API_KEY = (
  randomInt(1, 1000000) * 1000000 +
  randomInt(1, 1000000)
).toString();


instance.defaults.headers.post["Authorization"] = `Bearer ${API_KEY}`;
instance.defaults.headers.get["Authorization"] = `Bearer ${API_KEY}`;

function isWindows(): boolean {
  return Os.platform() === "win32";
}

let targetProcessName = "fundiverse-backend";
let servicePort = 3042;

if (isWindows()) {
  targetProcessName = `${targetProcessName}.exe`;
}

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
      hostname: "127.0.0.1",
      port: servicePort,
      path: "/terminate",
      method: "GET",
      headers: {
        Authorization: `Bearer ${API_KEY}`,
      },
    };

    const req = http.request(options, (res) => {
      if (res.statusCode && [200, 503].includes(res.statusCode)) {
        let data = "";

        // Receive data chunks
        res.on("data", (chunk) => {
          data += chunk;
        });

        // Process the complete response
        res.on("end", () => {
          resolve(data); // Resolve the Promise with the received data
        });
      } else {
        // Handle other status codes here
        console.error(
          `Failed to shutdown background service -HTTP Status Code: ${res.statusCode}`,
        );
      }
    });

    req.on("error", (error) => {
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
    if (platform === "win32") {
      cmd = `tasklist /FI "IMAGENAME eq ${processName}" /FO CSV /NH`;
    } else if (platform === "darwin" || platform === "linux") {
      cmd = `ps -C ${processName} -o pid=`;
    } else {
      reject(new Error(`Unsupported platform: ${platform}`));
      return;
    }

    exec(cmd, (error, stdout) => {
      if (error) {
        if (
          (platform === "darwin" || platform === "linux") &&
          error.code === 1 &&
          !error.killed
        ) {
          resolve([]);
        } else {
          reject(error);
          return;
        }
      }

      const output = stdout.trim();
      if (output) {
        if (
          platform === "win32" &&
          output.includes(
            "No tasks are running which match the specified criteria.",
          )
        ) {
          resolve([]);
        } else if (platform === "win32") {
          const lines = output.split("\n");
          const processes: object[] = [];

          for (const line of lines) {
            if (line.trim() !== "") {
              const pid = line.split(",")[1].trim();
              processes.push({ pid: stripQuotes(pid), name: processName });
            }
          }
          resolve(processes);
        } else {
          const pid = output.split("\n")[0].trim();
          resolve([{ pid: pid, name: processName }]);
        }
      } else {
        resolve([]);
      }
    });
  });
}

const startBackgroundService = () => {
  // let uuid = randomUUID()
  const spath = path.join(process.env.PUBLIC, targetProcessName);
  //const spath = path.join(app.getAppPath(), '/src/background/', `${targetProcessName}`)
  console.log(`spawning background service at ${spath}`);
  const backgroundService = execFile(
    spath,
    [API_KEY],
    {
      env: { ...process.env, FUNDIVERSE_API_SECRET_KEY: API_KEY },
      windowsHide: true,
    },
    (error, stdout, stderr) => {
      if (error) {
        throw error;
      }
      console.log(stdout);
      console.log(stderr);
    },
  );

  console.log(`Background process started with pid ${backgroundService.pid}`);
  backgroundService.on("close", (code) => {
    console.log(`Background python process exited with code ${code}`);
  });
  if (backgroundService.stdout) {
    backgroundService.stdout.on("data", (data) => {
      console.log(`Child background python stdout: ${data}`);
    });
  }
  if (backgroundService.stderr) {
    backgroundService.stderr.on("data", (data) => {
      console.log(`Child background python stderr: ${data}`);
    });
  }

  backgroundService.on("error", (error) => {
    console.error(
      `Error occurred in background python process: ${error}, ${error.message}`,
    );
  });

  backgroundService.on("exit", (code) => {
    console.log(
      `Background process ${backgroundService.pid} exited with code ${code}`,
    );
  });

  let backgroundClosed = false;
  app.on("before-quit", async (e) => {
    if (!backgroundClosed) {
      e.preventDefault();
      await stopBackground()
        .then(() => {
          backgroundClosed = true;
          console.log(
            `Background service ${backgroundService.pid} shut down, quitting`,
          );
          app.quit();
        })
        .catch((err) => {
          console.log(
            `Background service ${backgroundService.pid} failed to shut down ${err}`,
          );
          app.quit();
        });
    }
  });
  return backgroundService;
};

async function startBackgroundServiceSafe() {
  await findProcessesByName(targetProcessName).then((procs) => {
    if (procs.length > 0) {
      procs.map((proc) => {
        console.log(proc);
        console.log(
          `Background ${targetProcessName} is already running ${proc["pid"]}!`,
        );
        console.log(`Killing ${proc["pid"]} and restarting`);
        process.kill(proc["pid"]);
      });
    } else {
      console.log(
        `Background ${targetProcessName} is not running, starting it!`,
      );
    }

    startBackgroundService();
  });
}

// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.js
// │

// enable renders to access store
Store.initRenderer();

process.env.DIST = path.join(__dirname, "../dist");
process.env.PUBLIC = app.isPackaged
  ? process.env.DIST
  : path.join(process.env.DIST, "../public");

let win: BrowserWindow | null;
// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
const VITE_DEV_SERVER_URL = process.env["VITE_DEV_SERVER_URL"];

function createWindow() {
  win = new BrowserWindow({
    icon: path.join(process.env.PUBLIC, "appicon.svg"),
    fullscreen: app.isPackaged ? true : false,
    webPreferences: {
      contextIsolation: false,
      nodeIntegration: true,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  // Test active push message to Renderer-process.
  win.webContents.on("did-finish-load", () => {
    win?.webContents.send("main-process-message", new Date().toLocaleString());
    win?.webContents.send("api-key", API_KEY);
  });

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL);
  } else {
    // win.loadFile('dist/index.html')
    win.loadFile(path.join(process.env.DIST, "index.html"));
  }


  win.webContents.session.setCertificateVerifyProc((request, callback) => {
    const { hostname } = request
    if (hostname === 'client.schwab.com') {
      callback(0)
    }
    else if (hostname === '127.0.0.1') {
      callback(0)
    } else {
      // TODO: restric this further
      callback(0)
    }
  })
  console.log(`App ready and available at ${VITE_DEV_SERVER_URL}`);
}

// app.on('window-all-closed', () => {
//   // win = null
// })

app.on("window-all-closed", () => {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== "darwin") {
    app.quit();
  }
});

// app.isPackaged ? app.whenReady().then(startBackgroundServiceSafe).then(createWindow) : app.whenReady().then(createWindow)
app
  .whenReady()
  .then(startBackgroundServiceSafe)
  .then(createWindow)
  .catch((err) => {
    console.log(`Error starting background service ${err}`);
    app.quit();
  });
//
