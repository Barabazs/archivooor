import sqlite3
import threading
import time

import pytest

from archivooor.history import HistoryDB


@pytest.fixture
def history_db(tmp_path):
    db = HistoryDB(db_path=str(tmp_path / "test.db"))
    yield db
    db.close()


class TestHistoryDB:
    def test_record_and_query(self, history_db):
        row_id = history_db.record_submission("https://a.com", "job1", "submitted")
        assert row_id is not None

        rows = history_db.query()
        assert len(rows) == 1
        assert rows[0]["url"] == "https://a.com"
        assert rows[0]["job_id"] == "job1"
        assert rows[0]["status"] == "submitted"

    def test_duplicate_job_id_returns_none(self, history_db):
        history_db.record_submission("https://a.com", "dup1", "submitted")
        result = history_db.record_submission("https://b.com", "dup1", "submitted")
        assert result is None

    def test_null_job_id_allows_multiple(self, history_db):
        id1 = history_db.record_submission("https://a.com", None, "error")
        id2 = history_db.record_submission("https://b.com", None, "error")
        assert id1 is not None
        assert id2 is not None

    def test_update_completion(self, history_db):
        history_db.record_submission("https://a.com", "job1", "submitted")
        history_db.update_completion(
            "job1",
            status="success",
            original_url="https://a.com",
            timestamp="20260425120000",
            duration_sec=3.5,
            status_ext=None,
        )

        rows = history_db.query()
        assert rows[0]["status"] == "success"
        assert rows[0]["timestamp"] == "20260425120000"
        assert rows[0]["duration_sec"] == 3.5
        assert rows[0]["completed_at"] is not None

    def test_query_filter_url(self, history_db):
        history_db.record_submission("https://a.com/page1", "j1", "submitted")
        history_db.record_submission("https://b.com/page2", "j2", "submitted")

        rows = history_db.query(url="a.com")
        assert len(rows) == 1
        assert rows[0]["url"] == "https://a.com/page1"

    def test_query_filter_status(self, history_db):
        history_db.record_submission("https://a.com", "j1", "submitted")
        history_db.record_submission("https://b.com", "j2", "error")

        rows = history_db.query(status="error")
        assert len(rows) == 1
        assert rows[0]["url"] == "https://b.com"

    def test_query_filter_since(self, history_db):
        history_db.record_submission("https://a.com", "j1", "submitted")
        future = "2099-01-01T00:00:00"
        rows = history_db.query(since=future)
        assert len(rows) == 0

    def test_query_limit(self, history_db):
        for i in range(10):
            history_db.record_submission(f"https://a.com/{i}", f"j{i}", "submitted")

        rows = history_db.query(limit=3)
        assert len(rows) == 3

    def test_query_order_desc(self, history_db):
        history_db.record_submission("https://first.com", "j1", "submitted")
        time.sleep(0.01)
        history_db.record_submission("https://second.com", "j2", "submitted")

        rows = history_db.query()
        assert rows[0]["url"] == "https://second.com"

    def test_clear(self, history_db):
        history_db.record_submission("https://a.com", "j1", "submitted")
        history_db.record_submission("https://b.com", "j2", "submitted")

        count = history_db.clear()
        assert count == 2
        assert history_db.query() == []

    def test_thread_safety(self, history_db):
        errors = []

        def insert(n):
            try:
                history_db.record_submission(f"https://{n}.com", f"job{n}", "submitted")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=insert, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(history_db.query(limit=100)) == 20

    def test_schema_version(self, tmp_path):
        db_path = str(tmp_path / "version.db")
        db = HistoryDB(db_path=db_path)
        conn = sqlite3.connect(db_path)
        (version,) = conn.execute("PRAGMA user_version").fetchone()
        assert version == 1
        conn.close()
        db.close()

    def test_default_db_path(self):
        db = HistoryDB.__new__(HistoryDB)
        from archivooor.history import _default_db_path

        path = _default_db_path()
        assert "archivooor" in path
        assert path.endswith("history.db")
