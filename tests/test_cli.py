from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from archivooor.cli import cli


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
