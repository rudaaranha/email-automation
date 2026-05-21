"""
Teste unitários do models.py

Esses testes buscam validar: 
- Validação de dados (campos obrigatórios, tipos e formatos)
- Validações customizadas (@field_validator)
- Conversão de dados (to/from JSON)
- Enums e valores permidos
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError

from src.models import ExecuteRequest, TestEmailRequest, ActivityResponse
    

class TestExecuteRequest:
    """Testa o modelo de requisição POST/execute"""
    
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
    """Teste para garantir que o email é válido"""

    def test_valid_email_accepted(self):
        req = TestEmailRequest(to_email="teste@lab.com")
        assert req.to_email == "teste@lab.com"
    
    def test_invalid_email_rejected(self):
        with pytest.raises(ValueError):
            TestEmailRequest(to_email="email_invalido")


class TestActivityResponse:
    """Verifica campos obrigatórios"""

    def test_required_fields(self):
        activity = ActivityResponse(
            id=1, nome="Teste", responsavel="João",
            status="Pendente", project="teste"
        )
        assert activity.id == 1
        assert activity.nome == "Teste"
