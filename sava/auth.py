"""Shared authentication for Google services."""

import os

from google.oauth2 import service_account


SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

PRIMARY_USER_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
]


def _key_file() -> str:
    key_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not key_file:
        raise RuntimeError("Set GOOGLE_SERVICE_ACCOUNT_FILE to the path of your service account JSON key.")
    return key_file


def get_credentials(subject: str | None = None):
    """Credentials for Sava's own account (full read/write)."""
    creds = service_account.Credentials.from_service_account_file(_key_file(), scopes=SCOPES)
    subject = subject or os.environ.get("GOOGLE_IMPERSONATE_USER")
    if subject:
        creds = creds.with_subject(subject)
    return creds


def get_primary_credentials():
    """Credentials for the human's account (calendar, read-only Gmail + Tasks)."""
    user = os.environ.get("GOOGLE_PRIMARY_USER")
    if not user:
        raise RuntimeError("Set GOOGLE_PRIMARY_USER to the human's email address.")
    creds = service_account.Credentials.from_service_account_file(_key_file(), scopes=PRIMARY_USER_SCOPES)
    return creds.with_subject(user)
