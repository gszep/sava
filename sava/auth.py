"""Shared authentication for Google services."""

import os
import sys

from google.oauth2 import service_account


SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_credentials():
    key_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not key_file:
        raise RuntimeError("Set GOOGLE_SERVICE_ACCOUNT_FILE to the path of your service account JSON key.")

    creds = service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)

    impersonate = os.environ.get("GOOGLE_IMPERSONATE_USER")
    if impersonate:
        creds = creds.with_subject(impersonate)

    return creds
