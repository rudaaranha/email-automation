"""
Unit tests of test_models.py

These tests will validate:  
- data (required fields, types and formats)
- Custom validations (@field_validator)
- Data convertion (to/from JSON)
- Enums and allowed values
"""

import pytest
from datetime import datetime, date
from pydantic import ValidationError

from src.models import (
    ExecuteRequest, 
    TestEmailRequest, 
    ActivityResponse,
    AlertHistory,
    ProjectState,
    AlertType,
)
    

class TestExecuteRequest:
    """Tests the model of POST/execute requisition"""
    
    def test_project_normalization(self):
        req = ExecuteRequest(project="  SENSOR_DIABETES  ")
        assert req.project == "sensor_diabetes"

    def test_project_optional(self):
        req = ExecuteRequest(project=None)
        assert req.project is None

    def test_empty_string_rejected(self):
        with pytest.raises(ValueError):
            ExecuteRequest(project="  ")


class TestEmailValidation:
    """Tests to validate email"""

    def test_valid_email_accepted(self):
        req = TestEmailRequest(to_email="teste@lab.com")
        assert req.to_email == "teste@lab.com"
    
    def test_invalid_email_rejected(self):
        with pytest.raises(ValueError):
            TestEmailRequest(to_email="email_invalido")


class TestActivityResponse:
    """Verify required fields"""

    def test_required_fields(self):
        activity = ActivityResponse(
            id=1, nome="Teste", responsavel="João",
            status="Não iniciada", project="teste"
        )
        assert activity.id == 1
        assert activity.nome == "Teste"


class TestAlertHistory:
    """Tests the AlertHistory model"""

    def test_required_fields(self):
        history = AlertHistory(
            project="projeto_teste",
            activity="Atividade 1",
            researcher="João",
            email="joao@example.com",
            alert_type=AlertType.ATRASO,
        )

        assert history.project == "projeto_teste"
        assert history.activity == "Atividade 1"
        assert history.researcher == "João"
        assert history.email == "joao@example.com"
        assert history.alert_type == AlertType.ATRASO

    def test_sent_at_has_default(self):
        history = AlertHistory(
            project="projeto_teste",
            activity="Atividade 1",
            researcher="João",
            email="joao@example.com",
            alert_type=AlertType.ATRASO,
        )

        assert history.sent_at is not None
        assert isinstance(history.sent_at, datetime)

    def test_reference_date_is_optional(self):
        history = AlertHistory(
            project="projeto_teste",
            activity="Atividade 1",
            researcher="João",
            email="joao@example.com",
            alert_type=AlertType.ATRASO,
        )

        assert history.reference_date is None


class TestProjectState:
    """Tests the ProjectState model"""

    def test_project_is_active_by_default(self):
        state = ProjectState(
            project="projeto_teste",
            spreadsheet_id="spreadsheet123",
        )

        assert state.project == "projeto_teste"
        assert state.spreadsheet_id == "spreadsheet123"
        assert state.active is True
        assert state.completed_at is None

    def test_project_can_be_completed(self):
        completed_at = datetime.now()

        state = ProjectState(
            project="projeto_teste",
            spreadsheet_id="spreadsheet123",
            active=False,
            completed_at=completed_at,
        )

        assert state.active is False
        assert state.completed_at == completed_at
