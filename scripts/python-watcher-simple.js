#!/usr/bin/env node

/**
 * Simple Python File Watcher
 * A lightweight alternative that just monitors Python files and logs changes
 */

const chokidar = require('chokidar');
const path = require('path');
const fs = require('fs');

console.log('🐍 Simple Python Watcher Starting...');

// Configuration
const pythonPaths = ['langgraph/**/*.py'];
const options = {
  ignored: ['**/venv/**', '**/__pycache__/**', '**/*.pyc'],
  persistent: true,
  ignoreInitial: true
};

// Track changes to avoid spam
let lastChange = 0;
const DEBOUNCE_MS = 1000;

function handleChange(filePath, event = 'change') {
  const now = Date.now();
  if (now - lastChange < DEBOUNCE_MS) {
    return;
  }
  lastChange = now;

  const relativePath = path.relative(process.cwd(), filePath);
  console.log(`\n🔥 [${event}] ${relativePath}`);
  
  // Touch index.ts to trigger nodemon restart
  const indexPath = path.join(process.cwd(), 'src', 'index.ts');
  try {
    const now = new Date();
    fs.utimesSync(indexPath, now, now);
    console.log('🔄 Triggered server restart');
  } catch (err) {
    console.log('❌ Could not trigger restart:', err.message);
  }
}

// Start watching
const watcher = chokidar.watch(pythonPaths, options);

watcher
  .on('ready', () => console.log('✅ Watching Python files for changes...\n'))
  .on('change', (path) => handleChange(path, 'changed'))
  .on('add', (path) => handleChange(path, 'added'))
  .on('unlink', (path) => handleChange(path, 'removed'))
  .on('error', (error) => console.error('❌ Watcher error:', error));

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Stopping Python watcher...');
  watcher.close();
  process.exit(0);
});
