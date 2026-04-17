import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Email
    EMAIL_NATS = os.getenv("EMAIL_NATS")
    SENHA_APP_NATS = os.getenv("PASSWORD_APP_NATS")

    # Planilhas
    SPREADSHEETS = {}
    for key, value in os.environ.items():
        if key.startswith("SPREADSHEET_ID_"):
            project_name = key.replace("SPREADSHEET_ID_", "").lower()
            SPREADSHEETS[project_name] = value

    # Configuração do servidor SMTP
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587

    # Caminhos
    PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PATH_JSON = os.path.join(PROJECT, 'credenciais.json')

    # Abas de interesse nas planilhas
    ACTIVITIES_WORKSHEET = "ENTREGA DE ATIVIDADES"
    RESEARCHERS_WORKSHEET = "PESQUISADORES"

    # Mapeamento das colunas
    COLUMNS = {
        'atividade': 'DEMANDA',
        'data_inicio': 'DIA INICIO',
        'data_fim': 'DIA DE TÉRMINO',
        'status': 'SITUAÇÃO',
        'responsavel': 'RESPONSÁVEL'
    }

    # Configurações de alerta
    RESENDING_DAYS_DELAY = 3 # envia alerta a cada 3 dias de atraso
    EXECUTION_HOUR = ["09:00", "14:00"]

    # Modo de teste
    TEST_MODE = os.getenv("TEST_MODE", "FALSE").lower() == "true"
    TEST_EMAIL = os.getenv("TEST_EMAIL", "teste@exemplo.com")
