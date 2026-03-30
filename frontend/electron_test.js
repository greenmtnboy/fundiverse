const { app } = require('electron');
console.log({ hasApp: !!app, type: typeof require('electron'), versions: process.versions });
if (app) {
  app.whenReady().then(() => { console.log('ready'); app.quit(); });
}
