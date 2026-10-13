from types import SimpleNamespace
from unittest.mock import patch

from src.google_auth import authenticate_google_sheets


def test_uses_service_account_file_when_available():
    config = SimpleNamespace(PATH_JSON="credenciais.json")
    credentials = object()
    client = object()

    with (
        patch("src.google_auth.os.path.isfile", return_value=True),
        patch(
            "src.google_auth.Credentials.from_service_account_file",
            return_value=credentials,
        ) as file_auth,
        patch("src.google_auth.gspread.authorize", return_value=client) as authorize,
    ):
        result = authenticate_google_sheets(config)

    assert result is client
    file_auth.assert_called_once_with(
        "credenciais.json",
        scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    authorize.assert_called_once_with(credentials)


def test_uses_application_default_credentials_when_file_missing():
    config = SimpleNamespace(PATH_JSON="credenciais.json")
    credentials = object()
    client = object()

    with (
        patch("src.google_auth.os.path.isfile", return_value=False),
        patch(
            "src.google_auth.google.auth.default",
            return_value=(credentials, "test-project"),
        ) as default_auth,
        patch("src.google_auth.gspread.authorize", return_value=client) as authorize,
    ):
        result = authenticate_google_sheets(config)

    assert result is client
    default_auth.assert_called_once_with(
        scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    authorize.assert_called_once_with(credentials)
