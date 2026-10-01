from datetime import date, datetime
from typing import List, Optional

import gspread

from src.config import Config
from src.models import AlertHistory, AlertType, ProjectState


class SystemRepository:
    """Persistência dos estados dos projetos e histórico de alertas."""

    PROJECTS_WORKSHEET = "PROJECTS"
    ALERT_HISTORY_WORKSHEET = "ALERT_HISTORY"

    PROJECT_HEADERS = [
        "project",
        "spreadsheet_id",
        "active",
        "completed_at",
    ]

    ALERT_HISTORY_HEADERS = [
        "project",
        "activity",
        "researcher",
        "email",
        "alert_type",
        "sent_at",
        "reference_date",
    ]

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.client = self._authenticate()

    def _authenticate(self):
        """Autentica no Google Sheets usando as credenciais do projeto."""

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        from oauth2client.service_account import ServiceAccountCredentials

        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.config.PATH_JSON,
                scope,
            )
            return gspread.authorize(creds)
        except FileNotFoundError:
            raise Exception(
                f"Arquivo de credenciais não encontrado: {self.config.PATH_JSON}"
            )
        except Exception as e:
            raise Exception(f"Falha na autenticação: {e}")

    def _get_control_spreadsheet(self):
        """Retorna a planilha central de controle."""

        if not self.config.CONTROL_SPREADSHEET_ID:
            raise ValueError(
                "SPREADSHEET_ID_CONTROL não está configurado."
            )

        try:
            return self.client.open_by_key(
                self.config.CONTROL_SPREADSHEET_ID
            )
        except Exception as e:
            raise Exception(
                "Erro ao abrir a planilha de controle: "
                f"{self.config.CONTROL_SPREADSHEET_ID}: {e}"
            )

    def _get_worksheet(self, worksheet_name: str):
        """Retorna uma aba da planilha de controle."""

        spreadsheet = self._get_control_spreadsheet()

        try:
            return spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            raise ValueError(
                f"Aba '{worksheet_name}' não encontrada "
                "na planilha de controle."
            )

    def ensure_control_worksheets(self) -> None:
        """Garante que as abas de controle existam com os cabeçalhos esperados."""

        spreadsheet = self._get_control_spreadsheet()

        control_worksheets = [
            (
                self.PROJECTS_WORKSHEET,
                self.PROJECT_HEADERS,
                1000,
                4,
            ),
            (
                self.ALERT_HISTORY_WORKSHEET,
                self.ALERT_HISTORY_HEADERS,
                1000,
                7,
            ),
        ]

        existing_worksheets = spreadsheet.worksheets()

        for worksheet_name, headers, rows, cols in control_worksheets:
            worksheet = next(
                (
                    item
                    for item in existing_worksheets
                    if item.title == worksheet_name
                ),
                None,
            )

            if worksheet is None:
                worksheet = spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=rows,
                    cols=cols,
                )

            current_headers = worksheet.row_values(1)

            if current_headers != headers:
                last_column = chr(64 + len(headers))
                worksheet.update(
                    f"A1:{last_column}1",
                    [headers],
                )

    def get_project_state(self, project: str) -> Optional[ProjectState]:
        """Busca o estado de um projeto."""

        worksheet = self._get_worksheet(self.PROJECTS_WORKSHEET)
        records = worksheet.get_all_records()

        for row in records:
            if row.get("project") != project:
                continue

            completed_at = row.get("completed_at") or None

            if completed_at:
                try:
                    completed_at = datetime.fromisoformat(completed_at)
                except (TypeError, ValueError):
                    completed_at = None

            return ProjectState(
                project=row["project"],
                spreadsheet_id=row["spreadsheet_id"],
                active=str(row.get("active", "TRUE")).upper() == "TRUE",
                completed_at=completed_at,
            )

        return None

    def save_project_state(self, state: ProjectState) -> None:
        """Salva ou atualiza o estado de um projeto."""

        worksheet = self._get_worksheet(self.PROJECTS_WORKSHEET)
        records = worksheet.get_all_records()

        values = [
            state.project,
            state.spreadsheet_id,
            str(state.active).upper(),
            state.completed_at.isoformat() if state.completed_at else "",
        ]

        for index, row in enumerate(records, start=2):
            if row.get("project") == state.project:
                worksheet.update(
                    f"A{index}:D{index}",
                    [values],
                )
                return

        worksheet.append_row(values)

    def mark_project_completed(self, project: str) -> bool:
        """Marca um projeto como concluído."""

        state = self.get_project_state(project)

        if state is None:
            return False

        state.active = False
        state.completed_at = datetime.now()

        self.save_project_state(state)
        return True

    def alert_was_sent(
        self,
        project: str,
        activity: str,
        researcher: str,
        alert_type: AlertType,
        reference_date: Optional[date] = None,
    ) -> bool:
        """Verifica se um alerta já foi enviado."""

        worksheet = self._get_worksheet(self.ALERT_HISTORY_WORKSHEET)
        records = worksheet.get_all_records()

        for row in records:
            if (
                row.get("project") != project
                or row.get("activity") != activity
                or row.get("researcher") != researcher
                or row.get("alert_type") != alert_type.value
            ):
                continue

            if reference_date is None:
                return True

            if row.get("reference_date") == reference_date.isoformat():
                return True

        return False

    def save_alert_history(self, history: AlertHistory) -> None:
        """Registra um alerta enviado."""

        worksheet = self._get_worksheet(self.ALERT_HISTORY_WORKSHEET)

        worksheet.append_row(
            [
                history.project,
                history.activity,
                history.researcher,
                history.email,
                history.alert_type.value,
                history.sent_at.isoformat(),
                (
                    history.reference_date.isoformat()
                    if history.reference_date
                    else ""
                ),
            ]
        )