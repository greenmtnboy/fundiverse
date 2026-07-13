try {
  const main = require('electron/main');
  console.log('electron/main', { keys: Object.keys(main).slice(0,10), hasApp: !!main.app });
} catch (error) {
  console.error('electron/main failed', error);
}
try {
  const renderer = require('electron/renderer');
  console.log('electron/renderer', { keys: Object.keys(renderer).slice(0,10) });
} catch (error) {
  console.error('electron/renderer failed', error);
}
