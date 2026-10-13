import os

import gspread
import google.auth
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def authenticate_google_sheets(config):
    """Autentica no Google Sheets localmente ou no Cloud Run."""

    try:
        if os.path.isfile(config.PATH_JSON):
            credentials = Credentials.from_service_account_file(
                config.PATH_JSON,
                scopes=SCOPES,
            )
        else:
            credentials, _ = google.auth.default(
                scopes=SCOPES,
            )

        return gspread.authorize(credentials)

    except Exception as exc:
        raise RuntimeError(
            f"Falha na autenticação com Google Sheets: {exc}"
        ) from exc