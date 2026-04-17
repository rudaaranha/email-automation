import sys
import os
import pytest
import gspread

os.environ["TESTE_MODE"] = "True"
os.environ["EMAIL_NATS"] = "teste@email.com"

# Adiciona o caminho do projeto UMA VEZ para todos os testes
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
