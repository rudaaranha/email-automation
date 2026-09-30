import pytest
from datetime import datetime, date
from unittest.mock import Mock

from src.models import AlertHistory, AlertType, ProjectState
from src.system_repository import SystemRepository


class TestGetProjectState:
    """Tests for project state retrieval."""

    def test_returns_project_state(self):
        repository = SystemRepository.__new__(SystemRepository)

        worksheet = Mock()
        worksheet.get_all_records.return_value = [
            {
                "project": "projeto_teste",
                "spreadsheet_id": "sheet123",
                "active": "TRUE",
                "completed_at": "",
            }
        ]

        repository._get_worksheet = Mock(return_value=worksheet)

        result = repository.get_project_state("projeto_teste")

        assert isinstance(result, ProjectState)
        assert result.project == "projeto_teste"
        assert result.spreadsheet_id == "sheet123"
        assert result.active is True
        assert result.completed_at is None

    def test_returns_none_when_project_does_not_exist(self):
        repository = SystemRepository.__new__(SystemRepository)

        worksheet = Mock()
        worksheet.get_all_records.return_value = []

        repository._get_worksheet = Mock(return_value=worksheet)

        result = repository.get_project_state("inexistente")

        assert result is None


class TestSaveProjectState:
    """Tests for project state persistence."""

    def test_appends_new_project(self):
        repository = SystemRepository.__new__(SystemRepository)

        worksheet = Mock()
        worksheet.get_all_records.return_value = []

        repository._get_worksheet = Mock(return_value=worksheet)

        state = ProjectState(
            project="projeto_teste",
            spreadsheet_id="sheet123",
        )

        repository.save_project_state(state)

        worksheet.append_row.assert_called_once_with(
            [
                "projeto_teste",
                "sheet123",
                "TRUE",
                "",
            ]
        )

    def test_updates_existing_project(self):
        repository = SystemRepository.__new__(SystemRepository)

        worksheet = Mock()
        worksheet.get_all_records.return_value = [
            {
                "project": "projeto_teste",
                "spreadsheet_id": "sheet123",
                "active": "TRUE",
                "completed_at": "",
            }
        ]

        repository._get_worksheet = Mock(return_value=worksheet)

        completed_at = datetime(2026, 9, 30, 10, 0)

        state = ProjectState(
            project="projeto_teste",
            spreadsheet_id="sheet123",
            active=False,
            completed_at=completed_at,
        )

        repository.save_project_state(state)

        worksheet.update.assert_called_once_with(
            "A2:D2",
            [[
                "projeto_teste",
                "sheet123",
                "FALSE",
                completed_at.isoformat(),
            ]],
        )


class TestAlertHistory:
    """Tests for alert history persistence."""

    def test_alert_was_not_sent(self):
        repository = SystemRepository.__new__(SystemRepository)

        worksheet = Mock()
        worksheet.get_all_records.return_value = []

        repository._get_worksheet = Mock(return_value=worksheet)

        result = repository.alert_was_sent(
            project="projeto_teste",
            activity="Atividade 1",
            researcher="JOÃO",
            alert_type=AlertType.CONCLUSAO,
        )

        assert result is False

    def test_completion_alert_was_sent(self):
        repository = SystemRepository.__new__(SystemRepository)

        worksheet = Mock()
        worksheet.get_all_records.return_value = [
            {
                "project": "projeto_teste",
                "activity": "Atividade 1",
                "researcher": "JOÃO",
                "email": "joao@email.com",
                "alert_type": "conclusao",
                "sent_at": "2026-09-30T10:00:00",
                "reference_date": "",
            }
        ]

        repository._get_worksheet = Mock(return_value=worksheet)

        result = repository.alert_was_sent(
            project="projeto_teste",
            activity="Atividade 1",
            researcher="JOÃO",
            alert_type=AlertType.CONCLUSAO,
        )

        assert result is True

    def test_delay_alert_checks_reference_date(self):
        repository = SystemRepository.__new__(SystemRepository)

        worksheet = Mock()
        worksheet.get_all_records.return_value = [
            {
                "project": "projeto_teste",
                "activity": "Atividade 1",
                "researcher": "JOÃO",
                "email": "joao@email.com",
                "alert_type": "atraso",
                "sent_at": "2026-09-30T09:00:00",
                "reference_date": "2026-09-30",
            }
        ]

        repository._get_worksheet = Mock(return_value=worksheet)

        assert repository.alert_was_sent(
            project="projeto_teste",
            activity="Atividade 1",
            researcher="JOÃO",
            alert_type=AlertType.ATRASO,
            reference_date=date(2026, 9, 30),
        ) is True

        assert repository.alert_was_sent(
            project="projeto_teste",
            activity="Atividade 1",
            researcher="JOÃO",
            alert_type=AlertType.ATRASO,
            reference_date=date(2026, 10, 1),
        ) is False

    def test_save_alert_history(self):
        repository = SystemRepository.__new__(SystemRepository)

        worksheet = Mock()
        repository._get_worksheet = Mock(return_value=worksheet)

        sent_at = datetime(2026, 9, 30, 9, 0)
        reference_date = date(2026, 9, 30)

        history = AlertHistory(
            project="projeto_teste",
            activity="Atividade 1",
            researcher="JOÃO",
            email="joao@email.com",
            alert_type=AlertType.ATRASO,
            sent_at=sent_at,
            reference_date=reference_date,
        )

        repository.save_alert_history(history)

        worksheet.append_row.assert_called_once_with(
            [
                "projeto_teste",
                "Atividade 1",
                "JOÃO",
                "joao@email.com",
                "atraso",
                sent_at.isoformat(),
                reference_date.isoformat(),
            ]
        )