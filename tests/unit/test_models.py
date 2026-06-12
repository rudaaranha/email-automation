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

from src.models import ExecuteRequest, TestEmailRequest, ActivityResponse
    

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
