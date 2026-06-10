import time

from monitoring_agent.collectors.fs_watcher import start_watchers


def test_watcher_starts(tmp_path):
    logger = __import__("unittest.mock").mock.MagicMock()

    observer = start_watchers([{"path": str(tmp_path), "recursive": False}], logger)
    try:
        assert observer.is_alive()
    finally:
        observer.stop()
        observer.join()


def test_event_logged_on_file_write(tmp_path):
    logger = __import__("unittest.mock").mock.MagicMock()

    observer = start_watchers([{"path": str(tmp_path), "recursive": False}], logger)
    try:
        file_path = tmp_path / "sample.txt"
        file_path.write_text("hello world", encoding="utf-8")
        time.sleep(0.5)

        assert logger.info.called
        assert any("[FS]" in call.args[0] for call in logger.info.call_args_list)
    finally:
        observer.stop()
        observer.join()
