from unittest.mock import patch

import pytest
from keyring.errors import KeyringError, PasswordDeleteError, PasswordSetError

from archivooor import key_utils


class TestGetCredentials:
    def test_env_vars_take_precedence(self, monkeypatch):
        monkeypatch.setenv("s3_access_key", "env_ak")
        monkeypatch.setenv("s3_secret_key", "env_sk")

        with patch.object(key_utils.keyring, "get_password") as mock_kr:
            result = key_utils.get_credentials()

        assert result == ("env_ak", "env_sk")
        mock_kr.assert_not_called()

    def test_keyring_fallback(self, monkeypatch):
        monkeypatch.delenv("s3_access_key", raising=False)
        monkeypatch.delenv("s3_secret_key", raising=False)

        with patch.object(
            key_utils.keyring,
            "get_password",
            side_effect=lambda svc, key: {
                "s3_access_key": "kr_ak",
                "s3_secret_key": "kr_sk",
            }[key],
        ):
            result = key_utils.get_credentials()

        assert result == ("kr_ak", "kr_sk")

    def test_no_credentials(self, monkeypatch):
        monkeypatch.delenv("s3_access_key", raising=False)
        monkeypatch.delenv("s3_secret_key", raising=False)

        with patch.object(key_utils.keyring, "get_password", return_value=None):
            result = key_utils.get_credentials()

        assert result is None

    def test_keyring_error(self, monkeypatch):
        monkeypatch.delenv("s3_access_key", raising=False)
        monkeypatch.delenv("s3_secret_key", raising=False)

        with patch.object(
            key_utils.keyring, "get_password", side_effect=KeyringError("broken")
        ):
            result = key_utils.get_credentials()

        assert result is None


class TestSetCredentials:
    def test_success(self):
        with patch.object(key_utils.keyring, "set_password") as mock_set:
            key_utils.set_credentials("ak", "sk")

        assert mock_set.call_count == 2
        mock_set.assert_any_call("archivooor", "s3_access_key", "ak")
        mock_set.assert_any_call("archivooor", "s3_secret_key", "sk")

    def test_error_prints_message(self, capsys):
        with patch.object(
            key_utils.keyring, "set_password", side_effect=PasswordSetError("fail")
        ):
            key_utils.set_credentials("ak", "sk")

        assert "Failed to set credentials" in capsys.readouterr().out


class TestDeleteCredentials:
    def test_success(self):
        with patch.object(key_utils.keyring, "delete_password") as mock_del:
            key_utils.delete_credentials()

        assert mock_del.call_count == 2
        mock_del.assert_any_call("archivooor", "s3_access_key")
        mock_del.assert_any_call("archivooor", "s3_secret_key")

    def test_error_prints_message(self, capsys):
        with patch.object(
            key_utils.keyring,
            "delete_password",
            side_effect=PasswordDeleteError("fail"),
        ):
            key_utils.delete_credentials()

        assert "Failed to delete credentials" in capsys.readouterr().out
