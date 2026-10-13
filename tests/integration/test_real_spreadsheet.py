import os

import gspread
import pytest
from dotenv import load_dotenv

from src.config import Config


@pytest.fixture(scope="module")
def real_config():
    """
    Cria uma configuração específica para os testes de integração.

    O conftest.py define valores fictícios para os testes unitários.
    Aqui usamos o .env real para acessar os recursos do Google Sheets.
    """
    load_dotenv(override=True)

    config = Config()

    config.CONTROL_SPREADSHEET_ID = os.getenv(
        "SPREADSHEET_ID_CONTROL"
    )

    return config


@pytest.fixture(scope="module")
def real_google_client(real_config):
    """
    Cria um cliente real do Google Sheets.

    Usa as credenciais reais definidas em credenciais.json.
    """
    return gspread.service_account(
        filename=real_config.PATH_JSON
    )


class TestGoogleSheets:
    """Integration tests with Google Sheets."""

    @pytest.mark.integration
    def test_google_client_connection(self, real_google_client):
        """Connection test with Google Sheets."""
        assert real_google_client is not None
        print("Success in establishing a connection")

    @pytest.mark.integration
    def test_open_first_spreadsheet(
        self,
        real_google_client,
        real_config,
    ):
        """Open first active project spreadsheet."""

        control_spreadsheet = real_google_client.open_by_key(
            real_config.CONTROL_SPREADSHEET_ID
        )

        projects_worksheet = control_spreadsheet.worksheet(
            "PROJECTS"
        )

        projects = projects_worksheet.get_all_records()

        active_projects = [
            project
            for project in projects
            if str(project.get("active", "")).strip().upper() == "TRUE"
            and project.get("spreadsheet_id")
        ]

        assert active_projects, "No active projects configured"

        spreadsheet_id = active_projects[0]["spreadsheet_id"]

        spreadsheet = real_google_client.open_by_key(
            spreadsheet_id
        )

        assert spreadsheet is not None

        print(f"Planilha: {spreadsheet.title}")

    @pytest.mark.integration
    def test_spreadsheet_data_read(
        self,
        real_google_client,
        real_config,
    ):
        """Read activities from the first active project spreadsheet."""

        control_spreadsheet = real_google_client.open_by_key(
            real_config.CONTROL_SPREADSHEET_ID
        )

        projects_worksheet = control_spreadsheet.worksheet(
            "PROJECTS"
        )

        projects = projects_worksheet.get_all_records()

        active_projects = [
            project
            for project in projects
            if str(project.get("active", "")).strip().upper() == "TRUE"
            and project.get("spreadsheet_id")
        ]

        assert active_projects, "No active projects configured"

        spreadsheet_id = active_projects[0]["spreadsheet_id"]

        spreadsheet = real_google_client.open_by_key(
            spreadsheet_id
        )

        worksheet = spreadsheet.worksheet(
            real_config.ACTIVITIES_WORKSHEET
        )

        data = worksheet.get_all_values()

        assert len(data) > 0, "Worksheet is empty"

        print(f"{len(data)} read lines")
        print(f"Header: {data[0][:3]}...")


if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "-s", "-m", "integration"]
    )
    