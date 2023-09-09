// build-pyinstaller.js
const { exec } = require('child_process');
const path = require('path');

const parentDir = path.resolve(__dirname, '..')
// Replace 'your_script.py' with your actual Python script or entry point
const pythonScript = path.join(parentDir, 'backend/build.py');
// const pythonScript = '../backend/src/build.py';

const venvPath = path.join(parentDir, '.venv/bin/python');
require('dotenv').config();
// this is set in CI
// but if you have a pyenv set will override
const pythonPath = process.env.pythonLocation;
const pyInstallerCommand = pythonPath ? `${pythonPath}/python ${pythonScript}` : `${venvPath} ${pythonScript}`;

exec(pyInstallerCommand, {env: {'pyenv': process.env.pyenv, 'pythonLocation': process.env.pythonLocation}}, (error, stdout, stderr) => {
  if (error) {
    console.error(`Error: ${error}`);
    console.error(`PyInstaller Errors:\n${stderr}`);
    throw error;
  }
  console.error(`PyInstaller Errors:\n${stderr}`);
  console.log(`PyInstaller Output:\n${stdout}`);
  
});