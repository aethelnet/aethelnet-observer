import asyncio
import logging
import json
import os
from pathlib import Path
from typing import Set, Dict, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Lazy import to avoid circular dependency
from routers.stream import get_frontend_manager

logger = logging.getLogger("FilesystemWatcher")

class AuraticFileEventHandler(FileSystemEventHandler):
    """
    Handles filesystem events and broadcasts them to the frontend.
    Focuses on 'git-like' incremental updates.
    """
    def __init__(self, loop):
        self.loop = loop
        self.frontend = get_frontend_manager()
        self.ignored_dirs = {
            'node_modules', '.git', 'venv', '__pycache__', 'dist', 'build', '.idea', '.vscode', '.DS_Store',
            'mrcloud_storage', 'market_data.db-wal', 'market_data.db-shm', '__pycache__'
        }
        self.ignored_extensions = {'.pyc', '.swp', '.tmp'}

    def _is_ignored(self, src_path: str) -> bool:
        path = Path(src_path)
        # Check extensions
        if path.suffix in self.ignored_extensions:
            return True
        # Check directories
        for part in path.parts:
            if part in self.ignored_dirs:
                return True
        return False

    def _broadcast(self, event_type: str, src_path: str, is_dir: bool, dest_path: str = None):
        if self._is_ignored(src_path):
            return

        # Prepare Payload
        payload = {
            "type": "FS_PATCH",
            "action": event_type,
            "path": src_path,
            "is_dir": is_dir
        }
        
        if dest_path:
            payload["dest_path"] = dest_path

        # Fire and forget broadcast on the main event loop
        # We use run_coroutine_threadsafe because Watchdog runs in a separate thread
        asyncio.run_coroutine_threadsafe(
            self.frontend.broadcast(json.dumps(payload)), 
            self.loop
        )

    def on_created(self, event):
        self._broadcast("create", event.src_path, event.is_directory)

    def on_deleted(self, event):
        self._broadcast("delete", event.src_path, event.is_directory)

    def on_modified(self, event):
        if not event.is_directory: # We generally care about file content mods, not dir mods
            self._broadcast("modify", event.src_path, event.is_directory)

    def on_moved(self, event):
        self._broadcast("move", event.src_path, event.is_directory, event.dest_path)


class FilesystemWatcher:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FilesystemWatcher, cls).__new__(cls)
            cls._instance.observer = None
            cls._instance.handler = None
            cls._instance.is_running = False
        return cls._instance

    def start(self, path: str):
        if self.is_running:
            return

        logger.info(f"Starting Filesystem Watcher on: {path}")
        
        # We need the running loop to schedule broadcasts from the watchdog thread
        loop = asyncio.get_running_loop()
        self.handler = AuraticFileEventHandler(loop)
        
        self.observer = Observer()
        self.observer.schedule(self.handler, path, recursive=True)
        self.observer.start()
        self.is_running = True
        logger.info("Filesystem Watcher Active (Git-Mode).")

    def stop(self):
        if self.observer and self.is_running:
            logger.info("Stopping Filesystem Watcher...")
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            logger.info("Filesystem Watcher Stopped.")

def get_fs_watcher():
    return FilesystemWatcher()
