const { spawn } = require("child_process");
const path = require("path");
const os = require('os');
const parentDir = path.resolve(__dirname, "..");
const pythonScript = path.join(parentDir, "backend/build.py");

// Determine Python path
let venvPath = path.join(parentDir, ".venv/Scripts/python");
if (os.platform() === 'linux') {
  venvPath = path.join(parentDir, ".venv/bin/python");
}

require("dotenv").config();
const pythonPath = process.env.pythonLocation;
const pythonExecutable = pythonPath ? `${pythonPath}/python` : venvPath;

console.log(`Using Python executable: ${pythonExecutable}`);
console.log(`Building script: ${pythonScript}`);

// Use spawn instead of exec to get real-time output
const pyInstallerProcess = spawn(
  pythonExecutable,
  [pythonScript],
  {
    env: {
      ...process.env, // Include all current env variables
      pyenv: process.env.pyenv,
      pythonLocation: process.env.pythonLocation,
    },
  }
);

// Set a timeout (e.g., 30 minutes = 1800000 ms)
const TIMEOUT_MS = 900000;
const timeout = setTimeout(() => {
  console.error("PyInstaller build timed out after 15 minutes");
  pyInstallerProcess.kill();
  process.exit(1);
}, TIMEOUT_MS);

// Log output in real-time
pyInstallerProcess.stdout.on('data', (data) => {
  console.log(`PyInstaller: ${data.toString().trim()}`);
});

pyInstallerProcess.stderr.on('data', (data) => {
  console.error(`PyInstaller Error: ${data.toString().trim()}`);
});

// Handle process completion
pyInstallerProcess.on('close', (code) => {
  clearTimeout(timeout);
  if (code !== 0) {
    console.error(`PyInstaller process exited with code ${code}`);
    process.exit(code);
  } else {
    console.log("PyInstaller build completed successfully");
  }
});

// Handle unexpected errors
pyInstallerProcess.on('error', (err) => {
  clearTimeout(timeout);
  console.error(`Failed to start PyInstaller process: ${err}`);
  process.exit(1);
});