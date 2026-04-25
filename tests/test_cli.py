from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from archivooor.cli import cli
from archivooor.history import HistoryDB


@patch("archivooor.cli.key_utils")
@patch("archivooor.cli.archiver.Archiver")
class TestCli:
    def _runner(self):
        return CliRunner()

    def test_save_no_urls_shows_help(self, mock_archiver_cls, mock_key_utils):
        mock_key_utils.get_credentials.return_value = ("ak", "sk")
        mock_archiver_cls.return_value = MagicMock()

        result = self._runner().invoke(cli, ["save"])

        assert result.exit_code == 0
        assert "Usage" in result.output or "save" in result.output

    def test_save_default_output(self, mock_archiver_cls, mock_key_utils):
        mock_key_utils.get_credentials.return_value = ("ak", "sk")
        mock_arch = MagicMock()
        mock_arch.save_pages.return_value = [
            {"url": "https://a.com", "status": "submitted", "job_id": "j1"}
        ]
        mock_archiver_cls.return_value = mock_arch

        result = self._runner().invoke(cli, ["save", "https://a.com"])

        assert "status: submitted" in result.output
        assert "job_id: j1" in result.output

    def test_save_verbose_output(self, mock_archiver_cls, mock_key_utils):
        mock_key_utils.get_credentials.return_value = ("ak", "sk")
        mock_arch = MagicMock()
        mock_arch.save_pages.return_value = [
            {
                "url": "https://a.com",
                "status": "submitted",
                "job_id": "j1",
                "message": None,
            }
        ]
        mock_archiver_cls.return_value = mock_arch

        result = self._runner().invoke(cli, ["save", "-v", "https://a.com"])

        assert "url: https://a.com" in result.output
        assert "status: submitted" in result.output
        assert "job_id: j1" in result.output

    def test_job_output(self, mock_archiver_cls, mock_key_utils):
        mock_key_utils.get_credentials.return_value = ("ak", "sk")
        mock_arch = MagicMock()
        mock_arch.get_save_status.return_value = {
            "status": "success",
            "original_url": "https://a.com",
            "outlinks": ["https://b.com"],
        }
        mock_archiver_cls.return_value = mock_arch

        result = self._runner().invoke(cli, ["job", "abc123"])

        assert "status: success" in result.output
        assert "original_url: https://a.com" in result.output
        assert "outlinks_saved: 1" in result.output

    def test_stats_output(self, mock_archiver_cls, mock_key_utils):
        mock_key_utils.get_credentials.return_value = ("ak", "sk")
        mock_arch = MagicMock()
        mock_arch.get_user_status_request.return_value = {
            "available": 5,
            "processing": 1,
        }
        mock_archiver_cls.return_value = mock_arch

        result = self._runner().invoke(cli, ["stats"])

        assert "available: 5" in result.output
        assert "processing: 1" in result.output

    def test_keys_set(self, mock_archiver_cls, mock_key_utils):
        mock_key_utils.get_credentials.return_value = None

        result = self._runner().invoke(cli, ["keys", "set", "my_ak", "my_sk"])

        assert result.exit_code == 0
        mock_key_utils.set_credentials.assert_called_once_with(
            s3_access_key="my_ak", s3_secret_key="my_sk"
        )

    def test_keys_delete(self, mock_archiver_cls, mock_key_utils):
        mock_key_utils.get_credentials.return_value = None

        result = self._runner().invoke(cli, ["keys", "delete"])

        assert result.exit_code == 0
        mock_key_utils.delete_credentials.assert_called_once()

    def test_no_history_flag(self, mock_archiver_cls, mock_key_utils):
        mock_key_utils.get_credentials.return_value = ("ak", "sk")
        mock_archiver_cls.return_value = MagicMock()

        self._runner().invoke(cli, ["--no-history", "save"])

        mock_archiver_cls.assert_called_once_with(
            s3_access_key="ak",
            s3_secret_key="sk",
            track_history=False,
        )


class TestHistoryCli:
    def _runner(self):
        return CliRunner()

    def test_history_table_output(self, tmp_path):
        db = HistoryDB(db_path=str(tmp_path / "h.db"))
        db.record_submission("https://example.com", "job1", "submitted")

        mock_arch = MagicMock()
        mock_arch.history = db

        with (
            patch("archivooor.cli.key_utils") as mk,
            patch("archivooor.cli.archiver.Archiver", return_value=mock_arch),
        ):
            mk.get_credentials.return_value = ("ak", "sk")
            result = self._runner().invoke(cli, ["history"])

        assert result.exit_code == 0
        assert "example.com" in result.output
        assert "job1" in result.output
        assert "submitted" in result.output
        db.close()

    def test_history_json_output(self, tmp_path):
        db = HistoryDB(db_path=str(tmp_path / "h.db"))
        db.record_submission("https://example.com", "job1", "submitted")

        mock_arch = MagicMock()
        mock_arch.history = db

        with (
            patch("archivooor.cli.key_utils") as mk,
            patch("archivooor.cli.archiver.Archiver", return_value=mock_arch),
        ):
            mk.get_credentials.return_value = ("ak", "sk")
            result = self._runner().invoke(cli, ["history", "--json"])

        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["url"] == "https://example.com"
        db.close()

    def test_history_empty(self, tmp_path):
        db = HistoryDB(db_path=str(tmp_path / "h.db"))
        mock_arch = MagicMock()
        mock_arch.history = db

        with (
            patch("archivooor.cli.key_utils") as mk,
            patch("archivooor.cli.archiver.Archiver", return_value=mock_arch),
        ):
            mk.get_credentials.return_value = ("ak", "sk")
            result = self._runner().invoke(cli, ["history"])

        assert result.exit_code == 0
        assert "No submissions found" in result.output
        db.close()

    def test_history_clear(self, tmp_path):
        db = HistoryDB(db_path=str(tmp_path / "h.db"))
        db.record_submission("https://a.com", "j1", "submitted")

        mock_arch = MagicMock()
        mock_arch.history = db

        with (
            patch("archivooor.cli.key_utils") as mk,
            patch("archivooor.cli.archiver.Archiver", return_value=mock_arch),
        ):
            mk.get_credentials.return_value = ("ak", "sk")
            result = self._runner().invoke(cli, ["history", "clear", "--yes"])

        assert result.exit_code == 0
        assert "Deleted 1 entries" in result.output
        db.close()

    def test_history_disabled_error(self):
        mock_arch = MagicMock()
        mock_arch.history = None

        with (
            patch("archivooor.cli.key_utils") as mk,
            patch("archivooor.cli.archiver.Archiver", return_value=mock_arch),
        ):
            mk.get_credentials.return_value = ("ak", "sk")
            result = self._runner().invoke(cli, ["history"])

        assert result.exit_code != 0
        assert "disabled" in result.output
