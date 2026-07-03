import sys
import os
import pytest
import gspread
from datetime import date
from unittest.mock import Mock, patch

os.environ["TESTE_MODE"] = "True"
os.environ["EMAIL_NATS"] = "teste@email.com"

# Adiciona o caminho do projeto para todos os testes
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture(scope="session")
def config():
    """Fixture que carrega a configuração uma vez para todos os testes"""
    from src.config import Config
    return Config

@pytest.fixture(scope="module")
def google_client(config):
    
    if not os.path.exists(config.PATH_JSON):
        pytest.skip(f'Credenciais não encontradas: {config.PATH_JSON}')

    
    try:
        return gspread.service_account(filename=config.PATH_JSON)
    except Exception as e:
        pytest.skip(f'Erro na conexão: {e}')


# @pytest.fixture
# def app():
#     """Fixture para aplicação FastAPI"""
#     from src.api import create_app
#     return create_app() 


# @pytest.fixture
# def client(app):
#     """Fixture para clinte de test HTTP"""
#     from fastapi.testclient import TestClient
#     return TestClient(app)

@pytest.fixture
def alert_system(config):
    from src.alert_system import AlertSystems
    return AlertSystems(config)


@pytest.fixture
def spreadsheet_manager(config):
    """Cria uma instância do SpreadSheetManager para os testes"""
    from src.spreadsheet_manager import SpreadsheetManager
    return SpreadsheetManager(config)


@pytest.fixture
def mock_google_client():
    """
    Simula o cliente do Google Sheets para testes sem internet
    
    - Cria um obejto falso que imita o comportamento do gspread
    """
    mock = Mock()

    # Configuração dos métodos que serão usados
    mock.open_by_key = Mock()
    mock.open_by_key.return_value = Mock()
    return mock


@pytest.fixture
def sample_reseachers_data():
    """
    Dados da aba de pesquisadores usados como exemplo nos testes

    - Cada dicionário deve ter um 'Responsável' e 'E-mail'
    """
    return [
        {"Responsável": "João Teste", "E-mail": "joao@email.com"},
        {"Responsável": "Felipe Teste", "E-mail": "felipe@email.com"},
        {"Responsável": "Maria", "E-mail": "maria@email.com"},
        {"Responsável": "  José Teste  ", "E-mail": "jose@email.com"},
        {"Responsável": "", "E-mail": "vazio@email.com"},
        {"Responsável": "SEM_EMAIL", "E-mail": ""}
    ]


@pytest.fixture
def sample_activities_data():
    """"
    Dados da aba entretga de atividades usados como exemplos nos testes

    Data de referência: data de hoje
    """

    return [
        {
            "DEMANDA": "Reunião inicial de alinhamento",
            "DIA INICIO": "2026-04-02",
            "DIA DE TÉRMINO": "2026-04-02",
            "SITUAÇÃO": "Concluídas",
            "RESPONSÁVEL": "TODOS"
        },
        {
            "DEMANDA": "Seleção pareada no Rayyan",
            "DIA INICIO": "2026-04-08",
            "DIA DE TÉRMINO": "2026-04-14",
            "SITUAÇÃO": "Andamento",
            "RESPONSÁVEL": "Aldenora\nAna Carolina\nBárbara"
        },
        {
            "DEMANDA": "Extração de dados",
            "DIA INICIO": "2026-04-01",
            "DIA DE TÉRMINO": "2026-04-05",
            "SITUAÇÃO": "Não iniciada",
            "RESPONSÁVEL": "MÔNICA"
        },
        {
            "DEMANDA": "Atividade sem data fim",
            "DIA INICIO": "2026-04-01",
            "DIA DE TÉRMINO": "",
            "SITUAÇÃO": "Não iniciada",
            "RESPONSÁVEL": "JOSÉ"
        },
        {
            "DEMANDA": "",  # Nome vazio - deve ser ignorado
            "DIA INICIO": "2026-04-01",
            "DIA DE TÉRMINO": "2026-04-05",
            "SITUAÇÃO": "Não iniciada",
            "RESPONSÁVEL": "IGNORADO"
        }
    ]


@pytest.fixture
def mock_today_date():
    """
    Retorna uma data fixa para tos testes (ex: 2026-04-10)

    - Data usada no cálculo do número de dias de atraso de uma atividade
    """
    return date(2026, 4, 10)


@pytest.fixture
def mock_worksheet_with_data(sample_researchers_data):
    """
    Cria uma aba (worksheet) simulada que retorna dados de exemplo
    
    - Simula o comportamento de uma aba real do Google Sheets
    - Permite testar o load_researchers sem chamar a API real
    """
    mock_worksheet = Mock()
    mock_worksheet.get_all_records.return_value = sample_researchers_data
    return mock_worksheet


@pytest.fixture
def mock_spreadsheet_with_activities(mock_worksheet_with_data):
    """
    Cria uma planilha simulada que tem a aba de atividades

    - Simula uma planilha completa do Google Sheets
    - Permite testar o load_activities
    """
    mock_spreadsheet = Mock()
    mock_spreadsheet.worksheet.return_value = mock_worksheet_with_data
    return mock_spreadsheet
