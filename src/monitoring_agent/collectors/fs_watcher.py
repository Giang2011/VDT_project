import logging
import os

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class AgentFSHandler(FileSystemEventHandler):
    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger = logger

    def on_any_event(self, event):
        if not event.is_directory:
            self.logger.info(f"[FS] {event.event_type.upper()} {event.src_path}")


def start_watchers(watch_paths: list, logger: logging.Logger) -> Observer:
    """
    Schedule a handler for each configured path.
    Returns a started Observer thread.
    """
    observer = Observer()
    for entry in watch_paths:
        path = entry.get("path", "")
        recursive = entry.get("recursive", False)
        if not path:
            logger.warning("[WATCHER] Skipping empty watch path entry")
            continue
        if not os.path.exists(path):
            logger.warning(f"[WATCHER] Skipping missing path: {path}")
            continue
        handler = AgentFSHandler(logger)
        observer.schedule(handler, path, recursive=recursive)
        logger.info(f"[WATCHER] Watching: {path} (recursive={recursive})")
    observer.start()
    return observer
