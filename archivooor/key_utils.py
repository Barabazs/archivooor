"""Module for managing archive.org credentials in keyring."""

import os
from typing import Optional, Tuple

import keyring
from keyring import errors


def get_credentials() -> Optional[Tuple[str, str]]:
    """Get credentials from keyring or environment variables.

    Returns:
        A tuple containing the access key and secret key if found, otherwise
            None
    """
    access_key = os.environ.get("s3_access_key")
    secret_key = os.environ.get("s3_secret_key")
    if access_key and secret_key:
        return access_key, secret_key

    try:
        access_key = keyring.get_password("archivooor", "s3_access_key")
        secret_key = keyring.get_password("archivooor", "s3_secret_key")
        if access_key and secret_key:
            return access_key, secret_key
        else:
            return None
    except errors.KeyringError as e:
        print(f"Failed to get credentials from keyring: {e}")
        return None


def set_credentials(s3_access_key: str, s3_secret_key: str) -> None:
    """Set credentials in keyring.

    Args:
        s3_access_key: The access key
        s3_secret_key: The secret key
    """
    try:
        keyring.set_password("archivooor", "s3_access_key", s3_access_key)
        keyring.set_password("archivooor", "s3_secret_key", s3_secret_key)
        print("Successfully set credentials in keyring.")
    except errors.PasswordSetError as e:
        print(f"Failed to set credentials in keyring: {e}")


def delete_credentials() -> None:
    """Delete credentials from keyring."""
    try:
        keyring.delete_password("archivooor", "s3_access_key")
        keyring.delete_password("archivooor", "s3_secret_key")
        print("Successfully deleted credentials from keyring.")
    except errors.PasswordDeleteError as e:
        print(f"Failed to delete credentials from keyring: {e}")
