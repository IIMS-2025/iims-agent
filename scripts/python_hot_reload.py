#!/usr/bin/env python3
"""
Python Hot Reload Monitor
Monitors Python files and provides hot reload functionality for LangGraph flows
"""

import os
import sys
import time
import signal
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class PythonHotReloadHandler(FileSystemEventHandler):
    """Handler for Python file changes"""
    
    def __init__(self):
        self.debounce_time = 1.0  # 1 second debounce
        self.last_reload_time = 0
        self.pending_reload = False
        
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and event.src_path.endswith('.py'):
            self._schedule_reload(event.src_path, 'modified')
    
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and event.src_path.endswith('.py'):
            self._schedule_reload(event.src_path, 'created')
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory and event.src_path.endswith('.py'):
            self._schedule_reload(event.src_path, 'deleted')
    
    def _schedule_reload(self, file_path, action):
        """Schedule a reload with debouncing"""
        current_time = time.time()
        
        # Skip if we just reloaded recently
        if current_time - self.last_reload_time < self.debounce_time:
            return
        
        self.last_reload_time = current_time
        
        # Get relative path for cleaner output
        rel_path = os.path.relpath(file_path, project_root)
        
        print(f"\n🔥 Python file {action}: {rel_path}")
        print("🔄 Triggering hot reload...")
        
        # Clear Python module cache for changed modules
        self._clear_module_cache(file_path)
        
        # Touch the main TypeScript file to trigger nodemon restart
        self._trigger_nodejs_reload()
        
        print("✅ Hot reload triggered")
    
    def _clear_module_cache(self, file_path):
        """Clear Python module cache for the changed file"""
        try:
            # Convert file path to module path
            rel_path = os.path.relpath(file_path, project_root)
            if rel_path.startswith('langgraph/'):
                module_path = rel_path.replace('/', '.').replace('.py', '')
                
                # Remove from sys.modules if present
                modules_to_remove = [
                    module for module in sys.modules.keys()
                    if module.startswith(module_path) or module_path in module
                ]
                
                for module in modules_to_remove:
                    if module in sys.modules:
                        del sys.modules[module]
                        print(f"🗑️  Cleared module cache: {module}")
                        
        except Exception as e:
            print(f"⚠️  Could not clear module cache: {e}")
    
    def _trigger_nodejs_reload(self):
        """Trigger Node.js reload by touching the main TypeScript file"""
        try:
            main_ts_file = project_root / 'src' / 'index.ts'
            if main_ts_file.exists():
                # Update modification time
                main_ts_file.touch()
                print("📡 Sent reload signal to Node.js server")
            else:
                print("⚠️  Could not find main TypeScript file to trigger reload")
        except Exception as e:
            print(f"❌ Failed to trigger Node.js reload: {e}")


class PythonHotReloader:
    """Main hot reload monitor"""
    
    def __init__(self):
        self.observer = Observer()
        self.handler = PythonHotReloadHandler()
        self.watch_paths = [
            project_root / 'langgraph',
        ]
        
    def start(self):
        """Start the file watcher"""
        print("🐍 Python Hot Reload Monitor Starting...")
        print(f"📁 Project root: {project_root}")
        
        # Set up watchers for each path
        for watch_path in self.watch_paths:
            if watch_path.exists():
                self.observer.schedule(
                    self.handler,
                    str(watch_path),
                    recursive=True
                )
                print(f"👁️  Watching: {watch_path}")
            else:
                print(f"⚠️  Path not found: {watch_path}")
        
        # Start observer
        self.observer.start()
        print("✅ Python hot reload monitor ready")
        print("🔄 Python changes will clear module cache and trigger server restart")
        print("🛑 Press Ctrl+C to stop\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the file watcher"""
        print("\n🛑 Stopping Python hot reload monitor...")
        self.observer.stop()
        self.observer.join()
        print("✅ Python hot reload monitor stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start hot reload monitor
    reloader = PythonHotReloader()
    reloader.start()
