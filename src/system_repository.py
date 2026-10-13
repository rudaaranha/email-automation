from datetime import date, datetime
from typing import List, Optional

import gspread

from src.config import Config
from src.models import AlertHistory, AlertType, ProjectState
from src.google_auth import authenticate_google_sheets


class SystemRepository:
    """PersistÃªncia dos estados dos projetos e histÃ³rico de alertas."""

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
        self._control_spreadsheet_cache = None
        self._worksheet_cache = {}
        self._alert_history_records = None


    def _authenticate(self):
        """Autentica no Google Sheets usando as credenciais locais ou ADC."""
        return authenticate_google_sheets(self.config)


    def _get_control_spreadsheet(self):
        """Retorna a planilha central de controle, reutilizando a conexÃ£o aberta."""

        if not self.config.CONTROL_SPREADSHEET_ID:
            raise ValueError(
                "SPREADSHEET_ID_CONTROL nÃ£o estÃ¡ configurado."
            )


        cached = getattr(self, "_control_spreadsheet_cache", None)
        if cached is not None:
            return cached

        try:
            spreadsheet = self.client.open_by_key(
                self.config.CONTROL_SPREADSHEET_ID
            )
            self._control_spreadsheet_cache = spreadsheet
            return spreadsheet

        except Exception as e:
            raise Exception(
                "Erro ao abrir a planilha de controle: "
                f"{self.config.CONTROL_SPREADSHEET_ID}: {e}"
            )


    def _get_worksheet(self, worksheet_name: str):
        """Retorna uma aba em cache ou a busca em uma Ãºnica vez."""

        cache = getattr(self, "_worksheet_cache", None)
        if cache is None:
            cache = {}
            self._worksheet_cache = cache

        if worksheet_name in cache:
            return cache[worksheet_name]

        spreadsheet = self._get_control_spreadsheet()

        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            raise ValueError(
                f"Aba '{worksheet_name}' nÃ£o encontrada "
                "na planilha de controle."
            )

        cache[worksheet_name] = worksheet
        return worksheet


    def ensure_control_worksheets(self) -> None:
        """Garante que as abas de controle existam com os cabeÃ§alhos esperados."""

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


    def get_active_projects(self) -> List[ProjectState]:
        """
        Return all active projects configured in the control spreadsheet.

        Only projects with active=TRUE are returned.
        """
        worksheet = self._get_worksheet(self.PROJECTS_WORKSHEET)

        records = worksheet.get_all_records()
        active_projects = []

        for record in records:
            project_name = str(record.get("project", "")).strip()
            spreadsheet_id = str(record.get("spreadsheet_id", "")).strip()
            active = str(record.get("active", "")).strip().upper() == "TRUE"

            if not project_name or not spreadsheet_id:
                continue

            if not active:
                continue

            completed_at_raw = record.get("completed_at")
            completed_at = None

            if completed_at_raw:
                try:
                    completed_at = datetime.fromisoformat(
                        str(completed_at_raw)
                    )
                except (ValueError, TypeError):
                    pass

            active_projects.append(
                ProjectState(
                    project=project_name,
                    spreadsheet_id=spreadsheet_id,
                    active=True,
                    completed_at=completed_at,
                )
            )

        return active_projects


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

    def sync_completed_projects(self) -> None:
        """
        Registra automaticamente a data de conclusÃ£o dos projetos
        que foram desativados manualmente.

        O operador controla apenas o campo `active`.
        Quando active=FALSE e completed_at estÃ¡ vazio,
        o sistema registra a data/hora atual.
        """
        worksheet = self._get_worksheet(self.PROJECTS_WORKSHEET)
        records = worksheet.get_all_records()

        for index, row in enumerate(records, start=2):
            active = str(row.get("active", "")).strip().upper() == "TRUE"
            completed_at = row.get("completed_at")

            if active or completed_at:
                continue

            values = [
                row.get("project", ""),
                row.get("spreadsheet_id", ""),
                "FALSE",
                datetime.now().isoformat(),
            ]

            worksheet.update(
                f"A{index}:D{index}",
                [values],
            )


    def mark_project_completed(self, project: str) -> bool:
        """Marca um projeto como concluÃ­do."""

        state = self.get_project_state(project)

        if state is None:
            return False

        state.active = False
        state.completed_at = datetime.now()

        self.save_project_state(state)
        return True

    def reset_alert_history_cache(self) -> None:
        """Invalida o histÃ³rico para iniciar uma nova execuÃ§Ã£o."""
        self._alert_history_records = None


    def alert_was_sent(
            self,
            project: str,
            activity: str,
            researcher: str,
            alert_type: AlertType,
            reference_date: Optional[date] = None,
    ) -> bool:
        """Verifica em memÃ³ria se um alerta jÃ¡ foi enviado"""

        records = getattr(self, "_alert_history_records", None)

        if records is None:
            worksheet = self._get_worksheet(
                self.ALERT_HISTORY_WORKSHEET
            )
            records = worksheet.get_all_records()
            self._alert_history_records = records

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
        """Registra o alerta e atualiza o cache em memÃ³ria."""

        worksheet = self._get_worksheet(
            self.ALERT_HISTORY_WORKSHEET
        )

        reference_date = (
            history.reference_date.isoformat()
            if history.reference_date
            else ""
        )

        values = [
                history.project,
                history.activity,
                history.researcher,
                history.email,
                history.alert_type.value,
                history.sent_at.isoformat(),
                reference_date,
        ]

        worksheet.append_row(values)

        records = getattr(self, "_alert_history_records", None)
        if records is not None:
            records.append({
                "project": history.project,
                "activity": history.activity,
                "researcher": history.researcher,
                "email": history.email,
                "alert_type": history.alert_type.value,
                "sent_at": history.sent_at.isoformat(),
                "reference_date": reference_date,
            })


    def sync_completed_projects(self) -> None:
        """
        Registra automaticamente a data de conclusÃ£o dos projetos
        que foram desativados manualmente.

        O operador controla apenas o campo `active`.
        Quando active=FALSE e completed_at estÃ¡ vazio,
        o sistema registra a data/hora atual.
        """
        worksheet = self._get_worksheet(self.PROJECTS_WORKSHEET)
        records = worksheet.get_all_records()

        for index, row in enumerate(records, start=2):
            active = str(row.get("active", "")).strip().upper() == "TRUE"
            completed_at = row.get("completed_at")

            if active or completed_at:
                continue

            values = [
                row.get("project", ""),
                row.get("spreadsheet_id", ""),
                "FALSE",
                datetime.now().isoformat(),
            ]

            worksheet.update(
                f"A{index}:D{index}",
                [values],
            )
