#!/usr/bin/env node

/**
 * Python File Watcher for Hot Reload
 * Monitors Python files in the langgraph directory and restarts the Node.js process
 * when Python files change to trigger full application reload
 */

const chokidar = require('chokidar');
const path = require('path');
const { spawn } = require('child_process');

// Configuration
const PYTHON_DIRS = ['langgraph/**/*.py'];
const WATCH_OPTIONS = {
  ignored: [
    '**/node_modules/**',
    '**/venv/**',
    '**/__pycache__/**',
    '**/*.pyc',
    '**/dist/**',
    '**/uploads/**'
  ],
  persistent: true,
  ignoreInitial: true,
  followSymlinks: false,
  depth: 10
};

console.log('🐍 Python Hot Reload Watcher Starting...');
console.log('📁 Watching directories:', PYTHON_DIRS);

// Track changes to avoid rapid restarts
let changeTimeout;
let isRestarting = false;

// Function to trigger reload notification
function triggerReload(filePath) {
  if (isRestarting) {
    console.log('🔄 Restart already in progress, skipping...');
    return;
  }

  // Clear existing timeout
  if (changeTimeout) {
    clearTimeout(changeTimeout);
  }

  // Debounce changes (wait 1 second before triggering)
  changeTimeout = setTimeout(() => {
    console.log(`\n🔥 Python file changed: ${path.relative(process.cwd(), filePath)}`);
    console.log('📡 Sending reload signal to Node.js server...');
    
    // Send a signal that can be picked up by the main process
    // Since nodemon watches TypeScript files, we'll touch a TypeScript file to trigger reload
    const fs = require('fs');
    const touchFile = path.join(process.cwd(), 'src', 'index.ts');
    
    try {
      // Update the modification time of the main TypeScript file
      const now = new Date();
      fs.utimesSync(touchFile, now, now);
      console.log('✅ Reload signal sent - Node.js server will restart');
    } catch (error) {
      console.error('❌ Failed to send reload signal:', error.message);
    }
    
    isRestarting = true;
    setTimeout(() => {
      isRestarting = false;
    }, 3000); // Prevent rapid restarts for 3 seconds
    
  }, 1000);
}

// Initialize watcher
const watcher = chokidar.watch(PYTHON_DIRS, WATCH_OPTIONS);

// Event handlers
watcher
  .on('ready', () => {
    console.log('✅ Python watcher ready - monitoring for changes');
    console.log('🔄 Python file changes will trigger full server reload');
    console.log('🛑 Press Ctrl+C to stop watching\n');
  })
  .on('change', triggerReload)
  .on('add', (filePath) => {
    console.log(`➕ New Python file detected: ${path.relative(process.cwd(), filePath)}`);
    triggerReload(filePath);
  })
  .on('unlink', (filePath) => {
    console.log(`➖ Python file deleted: ${path.relative(process.cwd(), filePath)}`);
    triggerReload(filePath);
  })
  .on('error', (error) => {
    console.error('❌ Python watcher error:', error);
  });

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down Python watcher...');
  watcher.close().then(() => {
    console.log('✅ Python watcher stopped');
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  console.log('\n🛑 SIGTERM received - shutting down Python watcher...');
  watcher.close().then(() => {
    console.log('✅ Python watcher stopped');
    process.exit(0);
  });
});

// Keep the process alive
process.stdin.resume();
